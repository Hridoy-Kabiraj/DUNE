import numpy as np
from scipy import integrate
from reactorPhysics import reactorSystem
from reactorPhysics import qFuel
from reactorPhysics import rho
import reactorPhysics
from reactorPhysics import N235_0, N238_0, N239Pu_0, NFP_0
from reactorPhysics import beta_i, lambda_i, Lamb
#import matplotlib.pyplot as pl
import time


class DUNEReactor(object):
    """
    Provides methods to interact with the point kenetics model.
    The reactor system state vector (with 6 delayed neutron groups, Xenon-135, Samarium-149 poisoning,
    fuel isotope depletion, and burnup tracking):
    S = [n, C1-C6, Tfuel, Tcoolant, rodPosition, I135, Xe135, Nd149, Pm149, Sm149, N235, N238, N239Pu, NFP, Burnup]
    Total: 20 state variables
    """
    def __init__(self, initialSystemState=None, tstep=0.01):
        """ Initialize reactor system state """
        if initialSystemState is None:
            # Default: [n, C1-C6, Tfuel, Tcoolant, rodPosition, I135, Xe135, Nd149, Pm149, Sm149, N235, N238, N239Pu, NFP, Burnup]
            # Start at source level (very low neutron population)
            # Reactor will build up power when brought to criticality by withdrawing rods
            n0 = 1.e3  # Source level neutrons - essentially zero power at startup
            # Initialize precursors at equilibrium: C_i = beta_i * n / (lambda_i * Lamb)
            C_init = list(beta_i * n0 / (lambda_i * Lamb))
            I0 = 0.0  # Start with no Iodine-135
            X0 = 0.0  # Start with no Xenon-135
            Nd0 = 0.0  # Start with no Neodymium-149
            Pm0 = 0.0  # Start with no Promethium-149
            Sm0 = 0.0  # Start with no Samarium-149
            # Fuel isotope initial values
            N235_init = N235_0  # Fresh fuel U-235 concentration
            N238_init = N238_0  # Fresh fuel U-238 concentration
            N239Pu_init = N239Pu_0  # No Pu-239 in fresh fuel
            NFP_init = NFP_0  # No fission products in fresh fuel
            B_init = 0.0  # Zero burnup for fresh fuel
            initialSystemState = [n0] + C_init + [450., 450., 0., I0, X0, Nd0, Pm0, Sm0, N235_init, N238_init, N239Pu_init, NFP_init, B_init]
        self.S = np.array(initialSystemState)
        self.reactivity = rho(self.S, 0, 0, 0)
        self.tstep = tstep
        self.t = np.array([0, self.tstep])
        self.hrate = 0.0  # rod movement rate [% / s]
        self.rodSetPoint = 0.0  # initial rod setpoint [%]
        self.mdotC = 200.e3  # coolant flow rate [g / s]
        self.coolantSetPoint = 200.e3
        self.pwrCtrl = False
        self.coolantCtrl = False
        self.scramToggle = False
        self.promptCriticalMode = False
        # For Storage/Plotting (store key variables)
        self.maxTime = 100.  # maximum time storage history [s]
        dataStorLength = int(self.maxTime / self.tstep)
        self.time = np.zeros(dataStorLength)
        # Store: n, sum(precursors), Tfuel, Tcoolant, rodPosition, reactivity, Xe135, Sm149, N235, N238, N239Pu, NFP, Burnup
        # Pre-fill with initial values so plots don't show zeros at start
        initial_store = np.array([self.S[0], np.sum(self.S[1:7]), 
                                   self.S[7], self.S[8], self.S[9], self.reactivity, 
                                   self.S[11], self.S[14], self.S[15], self.S[16], self.S[17], self.S[18], self.S[19]])
        self.storVals = np.tile(initial_store.reshape(-1, 1), (1, dataStorLength))

    def timeStep(self):
        """ Step reactor system forward in time """
        self.__preStep()
        self.S = integrate.odeint(reactorSystem, self.S, self.t,
                                  args=(self.hrate, self.tstep, self.mdotC))[-1]
        self.reactivity = rho(self.S, 0, 0, 0)
        self.t += self.tstep
        self.storVals = np.roll(self.storVals, -1, axis=1)
        self.time = np.roll(self.time, -1)
        self.time[-1] = self.t[-1]
        # Store key values: [n, sum(C1-C6), Tfuel, Tcoolant, rodPosition, reactivity, Xe135, Sm149, N235, N238, N239Pu, NFP, Burnup]
        self.storVals[:, -1] = np.array([self.S[0], np.sum(self.S[1:7]), 
                                          self.S[7], self.S[8], self.S[9], self.reactivity, 
                                          self.S[11], self.S[14], self.S[15], self.S[16], self.S[17], self.S[18], self.S[19]])

    def __preStep(self):
        """
        Check for valid rod movements or SCRAM condition
        """
        if self.pwrCtrl:
            self.__controlPID()
        else:
            self.__rodCtrl()
        if self.hrate < 0 and self.S[9] <= 0.:
            # do not allow control rods below 0
            self.hrate = 0.
        elif self.hrate > 0 and self.S[9] >= 100.:
            self.hrate = 0.
        if not self.coolantCtrl:
            self.__updateCoolantForPower()
            self.__controlCoolantRate()
        self.__scramCheck()
        if self.scramToggle:
            # Insert control rods all the way
            self.S[9] = 0.
            self.hrate = 0.

    def __scramCheck(self):
        """
        Check for conditions which require us to SCRAM.
        """
        if self.S[7] > 1700:
            # Fuel temp scram (Temp in Kelvin)
            print("Fuel Temperature SCRAM setpoint Exceeded")
            self.SCRAM()
        elif self.S[8] > 700:
            # Coolant temp scram
            print("Coolant Temperature SCRAM setpoint Exceeded")
            self.SCRAM()
        else:
            pass

    def setTimeStep(self, tstep):
        self.tstep = tstep

    def setRodRate(self, rodRate):
        if not self.pwrCtrl:
            self.hrate = rodRate

    def setRodPosition(self, rodPos):
        self.rodSetPoint = rodPos

    def setCoolantRate(self, mdotCin):
        self.coolantSetPoint = mdotCin

    def toggleCoolantCtrl(self, coolantSet, coolantCtrlToggle=True):
        """
        Set coolant flow rate in kg/s (converts to g/s internally)
        """
        self.coolantSetPoint = coolantSet * 1.e3  # convert kg/s to g/s
        self.coolantCtrl = coolantCtrlToggle
        if self.coolantCtrl:
            self.mdotC = self.coolantSetPoint

    def __updateCoolantForPower(self):
        """
        Automatically adjust coolant setpoint based on reactor power
        Maps power to coolant flow rate: low power ~ 200 kg/s, high power ~ 1200 kg/s
        """
        currentPower = qFuel(self.S[0]) / 1.e6  # Power in MW
        maxPwr = 600.  # Maximum power for scaling
        
        # Normalize power (0 to 1)
        normPwr = abs(currentPower / maxPwr)
        if normPwr > 1.0:
            normPwr = 1.0
        
        # Map to coolant flow rate range
        minFlowRate = 200.e3  # 200 kg/s = 200000 g/s at minimum power
        maxFlowRate = 1200.e3  # 1200 kg/s = 1200000 g/s at maximum power
        self.coolantSetPoint = minFlowRate + (maxFlowRate - minFlowRate) * normPwr

    def __controlCoolantRate(self):
        diff = (self.coolantSetPoint - self.mdotC) / 10.
        fnDiff = np.tanh(1.0 * abs(diff))  # Relax control rod into position
        if self.coolantSetPoint > self.mdotC:
            self.mdotC += 1. / self.tstep * fnDiff
        elif self.coolantSetPoint < self.mdotC:
            self.mdotC -= 1. / self.tstep * fnDiff
        else:
            pass

    def togglePwrCtrl(self, pwrSet, pwrCtrlToggle=True):
        """
        Set power in MW
        """
        self.pwrSet = pwrSet
        self.pwrCtrl = pwrCtrlToggle
        self.pidBias = 0.0
        self.hrate = 0.0

    def __controlPID(self):
        maxRate = 0.60  # maxumum rod movement rate in %/s
        Kp = 0.0100000   # Proportional tunable const
        Ki = 0.0001000  # Intergral tunable const
        Kd = 0.0001000  # Derivitive tunable const
        currentpwr = qFuel(self.S[0]) / 1.e6
        errorFn = self.pwrSet - qFuel(self.storVals[0, :]) / 1.e6
        errorIntegral = np.sum(errorFn[-100:])  # base integral error on past 100 values
        errorDerivative = (errorFn[-1] - errorFn[-2]) / (self.tstep)
        if hasattr(self, 'pwrSet'):
            pidOut = self.pidBias + Kp * (self.pwrSet - currentpwr) + Ki * errorIntegral + Kd * errorDerivative
            self.hrate = pidOut
            if abs(self.hrate) > maxRate:
                self.hrate = maxRate * (self.hrate / abs(self.hrate))
        else:
            self.togglePwrCtrl(qFuel(self.S[0]) / 1.e6)

    def __rodCtrl(self):
        diff = self.S[9] - self.rodSetPoint
        fnDiff = np.tanh(1.0 * abs(diff))  # Relax control rod into position
        if diff < 0.:
            self.hrate = 0.5 * fnDiff
        elif diff > 0.:
            self.hrate = -0.5 * fnDiff
        else:
            self.hrate = 0.

    def SCRAM(self, scramToggle=True):
        """
        You crashed the reactor.
        """
        self.scramToggle = scramToggle

    def togglePromptJumpMode(self, promptCriticalToggle=True):
        """
        Toggle Prompt Jump Mode.
        When enabled, instantly inserts ~$0.003 reactivity by quickly
        withdrawing the control rod (similar to reverse SCRAM).
        Automatic SCRAM remains enabled.
        WARNING: This is for educational demonstration only!
        """
        self.promptCriticalMode = promptCriticalToggle
        if promptCriticalToggle:
            # Instantly withdraw rod by ~3% to insert ~$0.003 reactivity
            # (with $0.2 total rod worth, 3% withdrawal ≈ $0.003)
            newPos = min(self.S[9] + 3.0, 100.0)
            self.S[9] = newPos
            self.hrate = 0.0  # Stop any ongoing rod movement


def test():
    """
    Test reactor in rod control and power control modes.
    """
    i = 0
    t0 = time.time()
    duneReactor = DUNEReactor()
    duneReactor.setRodPosition(50.)  # set rod position to 50% withdrawn
    while i < 10000:
        duneReactor.timeStep()
        print("===================================")
        print("Time [s] = %f" % duneReactor.t[-1])
        print("Rod percent Withdrawn = %f" % duneReactor.S[9])
        print("Reactor Power [MW] = %f " % float(qFuel(duneReactor.S[0]) / 1.e6))
        print("Tfuel [K] = %f ,  Tcoolant [K] = %f" % (duneReactor.S[7], duneReactor.S[8]))
        i += 1
    i = 0
    duneReactor.togglePwrCtrl(200.)  # set reactor power to 200 MW
    while i < 10000:
        duneReactor.timeStep()
        print("===================================")
        print("Time [s] = %f" % duneReactor.t[-1])
        print("Rod percent Withdrawn = %f" % duneReactor.S[9])
        print("Reactor Power [MW] = %f " % float(qFuel(duneReactor.S[0]) / 1.e6))
        print("Tfuel [K] = %f ,  Tcoolant [K] = %f" % (duneReactor.S[7], duneReactor.S[8]))
        i += 1
    t1 = time.time()
    print(t1 - t0)

if __name__ == "__main__":
    test()
