#!/usr/bin/env python3

# LEGO REACTOR GUI
# Using wxPython and matplotlib for live plot updating.
#
# Hridoy Kabiraj
#
# changelog
# ----------
#
# 1/27/2015     Creation.
#

import time
import sys
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
        self.legoReactor = rct.LegoReactor(tstep=0.005)
        # Gen some seed data
        self.legoReactor.timeStep()
        self.data = [self.legoReactor.time, self.legoReactor.storVals]
        self.coolantBox.SetValue(str(round(self.legoReactor.mdotC / 1.e3, 2)))

        # Setup plot area
        self.create_plot_panel()

        # Setup the timer
        # On timer 'tic' we step the reactor system forward
        self.recalc_timer = wx.Timer(self)
        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_recalc_timer, self.recalc_timer)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        # Call reactor update and plot routines every 100 ms
        self.recalc_timer.Start(2)
        self.redraw_timer.Start(1000)

    def setInitConds(self):
        self.paused = False
        self.scramToggle = False
        self.pwrCtrlToggle = False
        self.pwrSetPt.SetValue(str(0.0))
        self.rodSetPt.SetValue(str(0.0))
        self.rodSlide.SetValue(100)
        self.zoom = 20

    def create_plot_panel(self):
        self.init_plot()
        self.canvas = FigCanvas(self.m_panel2, -1, self.fig)

    def on_redraw_timer(self, event):
        if not self.paused:
            self.data = [self.legoReactor.time, self.legoReactor.storVals]
            self.updateMonitors()
            self.writeToArduino()
        self.draw_plot()

    def on_recalc_timer(self, event):
        if not self.paused:
            self.legoReactor.timeStep()
            if abs(self.legoReactor.reactivity) >= 1.0:
                print("Promp Critical/Subcrit Event: Dollars = %f" % (self.legoReactor.reactivity))

    def init_plot(self):
        """
        Initilize plot area.
        """
        self.dpi = 100
        self.fig = Figure((6.0, 7.0), dpi=self.dpi)

        self.axes1 = self.fig.add_subplot(211)
        self.axes2 = self.fig.add_subplot(212)
        self.axes3 = self.axes2.twinx()
        if LooseVersion(matplotlib.__version__) >= LooseVersion('2.0.0'):
            self.axes1.set_facecolor('white')
        else:
            self.axes1.set_axis_bgcolor('white')
        self.axes1.set_title('Reactor Power [MW] Trace', size=12)

        pylab.setp(self.axes1.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes1.get_yticklabels(), fontsize=8)

    def draw_plot(self):
        # Determine plot data length depending on zoom lvl
        zoomPercentage = self.zoom / 100.
        if zoomPercentage < 0.02:
            zoomPercentage = 0.02
        plotMask = int(zoomPercentage * len(self.data[0]))

        # Plot the data
        xdata = np.array(np.array(range(plotMask)) / float(plotMask)) * self.legoReactor.maxTime * zoomPercentage
        pwrdata = qFuel(self.data[1][0, :][-plotMask:]) / 1.e6
        fuelTdata = self.data[1][2, :][-plotMask:]
        coolTdata = self.data[1][3, :][-plotMask:]
        self.axes1.clear()
        self.axes2.clear()
        self.axes3.clear()
        self.axes1.set_ylim(0, 650.)
        self.axes2.set_ylim(400, 1700.)
        self.axes3.set_ylim(400, 700.)
        self.axes1.set_title('Reactor Power [MW] Trace', size=12)
        self.axes1.set_ylabel('Power [MW]')
        self.axes1.set_xlabel(str(round(max(xdata), 0)) + ' time [s]')
        self.axes1.plot(xdata, pwrdata, linewidth=2)
        self.axes2.set_ylabel('Fuel Temperature [K]')
        self.axes3.set_ylabel('Coolant Temperature [K]')
        self.axes3.yaxis.set_label_position('right')
        self.axes3.yaxis.tick_right()
        fuelPlot, = self.axes2.plot(xdata, fuelTdata, color='r', linewidth=2, label='Fuel T')
        coolPlot, = self.axes3.plot(xdata, coolTdata, color='b', linewidth=2, label='Coolant T')
        handles, labels = self.axes2.get_legend_handles_labels()
        self.axes2.legend(handles, labels, loc=2)
        handles, labels = self.axes3.get_legend_handles_labels()
        self.axes3.legend(handles, labels, bbox_to_anchor=(0.402, 0.85))
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
        self.legoReactor.SCRAM(bool(self.scramToggle))

    def pwrCtrlON(self, event):
        """ On clicking the pwr ctrl checkbox """
        pwrSet = self.pwrSetPt.GetValue()
        self.pwrCtrlToggle = not self.pwrCtrlToggle
        self.legoReactor.togglePwrCtrl(float(pwrSet), bool(self.pwrCtrlToggle))

    def setReactorPwr(self, event):
        """ On txt input to reactor power box """
        pwrSet = self.pwrSetPt.GetValue()
        if self.pwrCtrlToggle:
            self.legoReactor.togglePwrCtrl(float(pwrSet))

    def setRodPos(self, event):
        """ On txt input to text input to rod pos box """
        enteredVal = self.rodSetPt.GetValue()
        self.legoReactor.setRodPosition(float(enteredVal))
        self.rodSlide.SetValue(100 - int(enteredVal))

    def setPlotZoom(self, event):
        self.zoom = int(self.plotZoom.GetValue())

    def rodSlideSet(self, event):
        """ On slider movement """
        self.rodSetPt.SetValue(str(100 - self.rodSlide.GetValue()))
        self.legoReactor.setRodPosition(float(self.rodSetPt.GetValue()))

    def coolantSet(self, event):
        self.legoReactor.setCoolantRate(float(self.coolantBox.GetValue()) * 1.e3)

    def updateMonitors(self):
        self.rodPosOut.SetValue(str(round(self.legoReactor.S[9], 1)))
        self.cooltOut.SetValue(str(self.legoReactor.S[8]))
        self.fueltOut.SetValue(str(self.legoReactor.S[7]))
        self.powOut.SetValue(str(float(qFuel(self.legoReactor.S[0]) / 1.e6)))
        self.rodGauge.SetValue(int(self.legoReactor.S[9]))        
        # Update coolant flow rate display based on current power
        # Map power to coolant flow rate matching Arduino motor control
        # Arduino maps power (0-255) to motor speed (20-180)
        # We'll convert this to coolant flow rate
        currentPower = float(qFuel(self.legoReactor.S[0]) / 1.e6)
        maxPwr = 500.  # Maximum power as defined in writeToArduino
        normPwr = abs(currentPower / maxPwr)
        normPwr = 250. * normPwr
        if normPwr >= 250:
            normPwr = 250
        
        # Map normalized power (0-250) to coolant flow rate
        # Arduino maps (0-255) to motor speed (20-180)
        # We'll map to coolant flow: low power ~ 200 kg/s, high power ~ 1800 kg/s
        minFlowRate = 200.0  # kg/s at minimum power
        maxFlowRate = 1800.0  # kg/s at maximum power
        coolantFlowRate = minFlowRate + (maxFlowRate - minFlowRate) * (normPwr / 250.0)
        self.coolantBox.SetValue(str(round(coolantFlowRate, 2)))
    def writeToArduino(self):
        """ write rod and power out to arduino if connected """
        if self.ser:
            # rod % withdrawn ranges stored in S[9] from 0 to 100
            rodWriteOut = abs((self.legoReactor.S[9] / 50.) * 160.)
            if rodWriteOut < 5.0:
                rodWriteOut = 5.0
            elif rodWriteOut > 140.0:
                rodWriteOut = 140.
            self.ser.write("r" + str(rodWriteOut))
            time.sleep(0.1)  # arduino needs time to adjust motor position

            # compute output voltage to blue LED
            maxPwr = 500.  # if pwr in [MW] greater than this value, set max bulb brightness
            normPwr = abs(qFuel(self.legoReactor.S[0]) / 1.e6 / maxPwr)
            # normPwr ranges from 0 to 255
            normPwr = 250. * normPwr
            if normPwr >= 250:
                normPwr = 250
            self.ser.write("p" + str(int(normPwr)))
            time.sleep(0.1)

            # send scram status to red RGB LED (stays on while scram is active)
            scramValue = 1 if self.legoReactor.scramToggle else 0
            print("Sending SCRAM value: {}".format(scramValue))
            self.ser.write("s" + str(int(scramValue)))
            time.sleep(0.1)

    def exitSim(self, event):
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
