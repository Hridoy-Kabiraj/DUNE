#!/usr/bin/env python3

# DUNE REACTOR GUI
# Using wxPython and matplotlib for live plot updating.
#
# Hridoy Kabiraj
#
# changelog
# ----------
#
# 1/09/2025     Creation.
# 2/04/2026     Renamed from legoReactor to DUNEReactor
#

import time
import sys
import csv
import os
from datetime import datetime
from distutils.version import LooseVersion
import numpy as np
import wx
import reactor as rct
from reactorPhysics import qFuel
import guiTemplate as gui
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas
#    NavigationToolbar2WxAgg as NavigationToolbar
import pylab


# Stupid fix for stupid problem
# def _sys_getenc_wrapper():
#     return 'UTF-8'
# sys.getfilesystemencoding = _sys_getenc_wrapper


class CalcFrame(gui.MyFrame1):
    def __init__(self, parent):
        gui.MyFrame1.__init__(self, parent)
        # Set initial conditions
        self.setInitConds()

        # Initialize connection to arduino if possible
        self.ser = initSerial()

        # Obtain an instance of the lego reactor class
        self.duneReactor = rct.DUNEReactor(tstep=0.005)
        # Gen some seed data
        self.duneReactor.timeStep()
        self.data = [self.duneReactor.time, self.duneReactor.storVals]
        self.coolantBox.SetValue(str(round(self.duneReactor.mdotC / 1.e3, 2)))

        # Setup plot area
        self.create_plot_panel()

        # Initialize CSV data logging
        self.initCSVLogging()

        # Setup the timer
        # On timer 'tic' we step the reactor system forward
        self.recalc_timer = wx.Timer(self)
        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_recalc_timer, self.recalc_timer)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        # Call reactor update and plot routines every 100 ms
        self.recalc_timer.Start(2)
        self.redraw_timer.Start(1000)
        
        # Maximize window to full screen
        self.Maximize(True)

    def setInitConds(self):
        self.paused = False
        self.scramToggle = False
        self.pwrCtrlToggle = False
        self.coolantCtrlToggle = False
        self.promptCriticalToggle = False
        self.pwrSetPt.SetValue(str(0.0))
        self.rodSetPt.SetValue(str(0.0))
        self.rodSlide.SetValue(100)
        self.zoom = 20

    def create_plot_panel(self):
        self.init_plot()
        self.canvas = FigCanvas(self.m_panel2, -1, self.fig)

    def on_redraw_timer(self, event):
        if not self.paused:
            self.data = [self.duneReactor.time, self.duneReactor.storVals]
            self.updateMonitors()
            self.writeToArduino()
        self.draw_plot()

    def on_recalc_timer(self, event):
        if not self.paused:
            self.duneReactor.timeStep()
            self.logDataToCSV()
            if abs(self.duneReactor.reactivity) >= 1.0:
                print("Promp Critical/Subcrit Event: Dollars = %f" % (self.duneReactor.reactivity))

    def init_plot(self):
        """
        Initilize plot area.
        """
        self.dpi = 100
        self.fig = Figure((15.0, 9.5), dpi=self.dpi)

        self.axes1 = self.fig.add_subplot(221)  # Top left: Power
        self.axes4 = self.fig.add_subplot(222)  # Top right: Reactivity
        self.axes2 = self.fig.add_subplot(223)  # Bottom left: Temperature
        self.axes3 = self.axes2.twinx()
        self.axes5 = self.fig.add_subplot(224)  # Bottom right: Xenon
        if LooseVersion(matplotlib.__version__) >= LooseVersion('2.0.0'):
            self.axes1.set_facecolor('white')
            self.axes4.set_facecolor('white')
            self.axes5.set_facecolor('white')
        else:
            self.axes1.set_axis_bgcolor('white')
            self.axes4.set_axis_bgcolor('white')
            self.axes5.set_axis_bgcolor('white')
        self.axes1.set_title('Reactor Power [MW] Trace', size=12)

        pylab.setp(self.axes1.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes1.get_yticklabels(), fontsize=8)
        pylab.setp(self.axes4.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes4.get_yticklabels(), fontsize=8)
        pylab.setp(self.axes5.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes5.get_yticklabels(), fontsize=8)

    def draw_plot(self):
        # Determine plot data length depending on zoom lvl
        zoomPercentage = self.zoom / 100.
        if zoomPercentage < 0.02:
            zoomPercentage = 0.02
        plotMask = int(zoomPercentage * len(self.data[0]))

        # Plot the data
        xdata = np.array(np.array(range(plotMask)) / float(plotMask)) * self.duneReactor.maxTime * zoomPercentage
        pwrdata = qFuel(self.data[1][0, :][-plotMask:]) / 1.e6
        fuelTdata = self.data[1][2, :][-plotMask:]
        coolTdata = self.data[1][3, :][-plotMask:]
        reactivitydata = self.data[1][5, :][-plotMask:]
        xenondata = self.data[1][6, :][-plotMask:]  # Xenon-135 concentration
        samariumdata = self.data[1][7, :][-plotMask:]  # Samarium-149 concentration
        self.axes1.clear()
        self.axes2.clear()
        self.axes3.clear()
        self.axes4.clear()
        self.axes5.clear()
        
        # Power plot (top left)
        self.axes1.set_ylim(0, 800.)
        self.axes1.set_title('Reactor Power [MW] Trace', size=12)
        self.axes1.set_ylabel('Power [MW]')
        self.axes1.set_xlabel('time [s]')
        self.axes1.plot(xdata, pwrdata, linewidth=2)
        
        # Reactivity plot (top right)
        self.axes4.set_title('Reactivity ($) Trace', size=12)
        self.axes4.set_ylabel('Reactivity ($)')
        self.axes4.set_xlabel('time [s]')
        self.axes4.plot(xdata, reactivitydata, color='g', linewidth=2)
        self.axes4.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.5)
        
        # Temperature plot (bottom left)
        self.axes2.set_ylim(400, 1750.)
        self.axes3.set_ylim(400, 750.)
        self.axes2.set_ylabel('Fuel Temperature [K]')
        self.axes2.set_xlabel('time [s]')
        self.axes3.set_ylabel('Coolant Temperature [K]')
        self.axes3.yaxis.set_label_position('right')
        self.axes3.yaxis.tick_right()
        fuelPlot, = self.axes2.plot(xdata, fuelTdata, color='r', linewidth=2, label='Fuel T')
        coolPlot, = self.axes3.plot(xdata, coolTdata, color='b', linewidth=2, label='Coolant T')
        handles, labels = self.axes2.get_legend_handles_labels()
        self.axes2.legend(handles, labels, loc=2)
        handles, labels = self.axes3.get_legend_handles_labels()
        self.axes3.legend(handles, labels, bbox_to_anchor=(0.402, 0.85))
        
        # Fission Product Poisons: Xenon-135 and Samarium-149 (bottom right)
        self.axes5.set_title('Fission Product Poisons', size=12)
        self.axes5.set_ylabel('Concentration [atoms/cm³]')
        self.axes5.set_xlabel(str(round(max(xdata), 0)) + ' time [s]')
        xenonPlot, = self.axes5.plot(xdata, xenondata, color='purple', linewidth=2, label='Xe-135')
        samariumPlot, = self.axes5.plot(xdata, samariumdata, color='orange', linewidth=2, label='Sm-149')
        self.axes5.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
        self.axes5.legend(loc='best', fontsize=9)
        self.canvas.draw()

    #######################
    # Button / Toggle Logic
    #######################
    def pauseSim(self, event):
        """
        Simulation pause logic
        """
        self.paused = not self.paused

    def SCRAM(self, event):
        """
        Scram button press logic
        """
        self.scramToggle = not self.scramToggle
        self.duneReactor.SCRAM(bool(self.scramToggle))

    def pwrCtrlON(self, event):
        """ On clicking the pwr ctrl checkbox """
        pwrSet = self.pwrSetPt.GetValue()
        self.pwrCtrlToggle = not self.pwrCtrlToggle
        self.duneReactor.togglePwrCtrl(float(pwrSet), bool(self.pwrCtrlToggle))

    def coolantCtrlON(self, event):
        """ On clicking the coolant ctrl checkbox """
        coolantSet = self.coolantBox.GetValue()
        self.coolantCtrlToggle = not self.coolantCtrlToggle
        self.duneReactor.toggleCoolantCtrl(float(coolantSet), bool(self.coolantCtrlToggle))

    def PromptJumpON(self, event):
        """ On clicking the prompt jump mode checkbox """
        self.promptCriticalToggle = not self.promptCriticalToggle
        self.duneReactor.togglePromptJumpMode(bool(self.promptCriticalToggle))
        if self.promptCriticalToggle:
            print("WARNING: Prompt Jump Mode ACTIVATED - Inserting ~$0.004 reactivity")
            print("Control rod withdrawn instantly (rod position increased by 8%)")
        else:
            print("Prompt Jump Mode DEACTIVATED")

    def setReactorPwr(self, event):
        """ On txt input to reactor power box """
        pwrSet = self.pwrSetPt.GetValue()
        if self.pwrCtrlToggle:
            self.duneReactor.togglePwrCtrl(float(pwrSet))

    def setRodPos(self, event):
        """ On txt input to text input to rod pos box """
        enteredVal = self.rodSetPt.GetValue()
        self.duneReactor.setRodPosition(float(enteredVal))
        self.rodSlide.SetValue(100 - int(enteredVal))

    def setPlotZoom(self, event):
        self.zoom = int(self.plotZoom.GetValue())

    def rodSlideSet(self, event):
        """ On slider movement """
        self.rodSetPt.SetValue(str(100 - self.rodSlide.GetValue()))
        self.duneReactor.setRodPosition(float(self.rodSetPt.GetValue()))

    def coolantSet(self, event):
        coolantSet = self.coolantBox.GetValue()
        if self.coolantCtrlToggle:
            self.duneReactor.toggleCoolantCtrl(float(coolantSet))
        else:
            self.duneReactor.setCoolantRate(float(coolantSet) * 1.e3)

    def updateMonitors(self):
        self.rodPosOut.SetValue(str(round(self.duneReactor.S[9], 1)))
        self.cooltOut.SetValue(str(round(self.duneReactor.S[8], 2)))
        self.fueltOut.SetValue(str(round(self.duneReactor.S[7], 2)))
        self.powOut.SetValue(str(round(float(qFuel(self.duneReactor.S[0]) / 1.e6), 6)))
        self.rodGauge.SetValue(int(self.duneReactor.S[9]))
        
        # Update reactivity display (in dollars)
        self.reactivityOut.SetValue('{:.6f}'.format(self.duneReactor.reactivity))
        
        # Update new monitoring fields
        self.xenonOut.SetValue('{:.3e}'.format(self.duneReactor.S[11]))  # Xe-135 in scientific notation
        self.samariumOut.SetValue('{:.3e}'.format(self.duneReactor.S[14]))  # Sm-149 in scientific notation
        
        # Update coolant flow rate display only if coolant control is not active
        if not self.coolantCtrlToggle:
            # Display current reactor coolant flow rate in kg/s
            self.coolantBox.SetValue(str(round(self.duneReactor.mdotC / 1.e3, 2)))
    def writeToArduino(self):
        """ write rod and power out to arduino if connected """
        if self.ser:
            # rod % withdrawn ranges stored in S[9] from 0 to 100
            rodWriteOut = abs((self.duneReactor.S[9] / 50.) * 160.)
            if rodWriteOut < 5.0:
                rodWriteOut = 5.0
            elif rodWriteOut > 140.0:
                rodWriteOut = 140.
            self.ser.write(("r" + str(rodWriteOut)).encode())
            time.sleep(0.1)  # arduino needs time to adjust motor position

            # compute output voltage to blue LED
            maxPwr = 600.  # if pwr in [MW] greater than this value, set max bulb brightness
            normPwr = abs(qFuel(self.duneReactor.S[0]) / 1.e6 / maxPwr)
            # normPwr ranges from 0 to 255
            normPwr = 250. * normPwr
            if normPwr >= 250:
                normPwr = 250
            self.ser.write(("p" + str(int(normPwr))).encode())
            time.sleep(0.1)

            # send coolant flow control to motor (case 'c')
            # Map coolant flow rate (g/s) to motor speed (20-180)
            minFlow = 200.e3  # 200 kg/s = 200000 g/s minimum
            maxFlow = 1200.e3  # 1200 kg/s = 1200000 g/s maximum
            currentFlow = self.duneReactor.mdotC
            # Clamp flow to valid range
            if currentFlow < minFlow:
                currentFlow = minFlow
            elif currentFlow > maxFlow:
                currentFlow = maxFlow
            # Map to motor speed range (20-180)
            motorSpeed = int(20 + (currentFlow - minFlow) / (maxFlow - minFlow) * 160)
            self.ser.write(("c" + str(motorSpeed)).encode())
            time.sleep(0.1)

            # send scram status to red RGB LED (stays on while scram is active)
            scramValue = 1 if self.duneReactor.scramToggle else 0
            self.ser.write(("s" + str(int(scramValue))).encode())
            time.sleep(0.1)

    def initCSVLogging(self):
        """Initialize CSV file for logging simulation data"""
        # Create SimulationData folder if it doesn't exist
        self.csv_folder = "SimulationData"
        if not os.path.exists(self.csv_folder):
            os.makedirs(self.csv_folder)
        
        # Create CSV filename with current date and time
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.csv_filename = os.path.join(self.csv_folder, f"reactor_sim_{timestamp}.csv")
        
        # Open CSV file and write header
        self.csv_file = open(self.csv_filename, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['Time(s)', 'Neutron_Density(#/cc)', 'Power(MW)', 
                                   'Reactivity($)', 'Fuel_Temp(K)', 'Coolant_Temp(K)', 
                                   'Flow_Rate(kg/s)', 'Rod_Position(%)', 
                                   'Xe-135(atoms/cc)', 'Sm-149(atoms/cc)'])
        self.last_log_time = 0.0
        self.log_interval = 0.5  # Log every 0.5 seconds
        print(f"CSV logging initialized: {self.csv_filename}")
    
    def logDataToCSV(self):
        """Log current simulation data to CSV file every 0.5 seconds"""
        if hasattr(self, 'csv_writer') and self.csv_writer:
            time_val = self.duneReactor.t[-1]
            
            # Only log if 0.5 seconds have passed since last log
            if time_val - self.last_log_time >= self.log_interval:
                neutron_density = self.duneReactor.S[0]
                power_mw = qFuel(self.duneReactor.S[0]) / 1.e6
                reactivity = self.duneReactor.reactivity
                fuel_temp = self.duneReactor.S[7]
                coolant_temp = self.duneReactor.S[8]
                flow_rate = self.duneReactor.mdotC / 1.e3  # convert g/s to kg/s
                rod_position = self.duneReactor.S[9]
                xenon_conc = self.duneReactor.S[11]  # Xe-135 concentration
                samarium_conc = self.duneReactor.S[14]  # Sm-149 concentration
                
                self.csv_writer.writerow([time_val, neutron_density, power_mw, 
                                           reactivity, fuel_temp, coolant_temp, 
                                           flow_rate, rod_position, 
                                           xenon_conc, samarium_conc])
                self.last_log_time = time_val
    
    def closeCSVLogging(self):
        """Close CSV file"""
        if hasattr(self, 'csv_file') and self.csv_file:
            self.csv_file.close()
            print(f"CSV file saved: {self.csv_filename}")

    def exitSim(self, event):
        self.closeCSVLogging()
        sys.exit()


def initSerial():
    from sys import platform as _platform
    import serial
    from serial.tools import list_ports
    ser = None
    print("Platform " + _platform + " detected.")
    print("Attempting to establish connection with arduino.")
    port_candidates = []
    if _platform == "linux" or _platform == "linux2":
        port_candidates.extend(["/dev/ttyACM" + str(i) for i in range(10)])
        port_candidates.extend(["/dev/ttyUSB" + str(i) for i in range(10)])
    elif _platform == "windows" or _platform == "win32" or _platform == "win64":
        port_candidates.extend(["COM" + str(i) for i in range(1, 11)])
    elif _platform == "darwin":
        port_candidates.extend(["/dev/cu.usbmodem14" + str(i + 10) for i in range(10)])

    # Also include any port that pyserial can already see
    port_candidates.extend([p.device for p in list_ports.comports()])

    tried = set()
    for port in port_candidates:
        if port in tried:
            continue
        tried.add(port)
        try:
            print("Attempting handshake with arduino on " + port + " :9600")
            ser = serial.Serial(port, 9600, timeout=2)
            time.sleep(3)
            break
        except Exception as exc:
            print("Connection failed on " + port + " because " + str(exc))
            ser = None
    if not ser:
        print("Arduino Not Detected.  Running without serial connection")
    else:
        print("Connection to Arduino Established on " + ser.port)
        return ser



def main():
    app = wx.App(False)
    frame = CalcFrame(None)
    frame.Show(True)
    app.MainLoop()

if __name__ == "__main__":
    # Start the application
    main()
