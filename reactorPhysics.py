#!/usr/bin/env python3

# Contains reactor kenetics equations
# and reactor parameters

import numpy as np

# 6-group delayed neutron precursor data for U-235 (more accurate)
beta_i = np.array([0.000215, 0.001424, 0.001274, 0.002568, 0.000748, 0.000273])  # delayed neutron fractions
lambda_i = np.array([0.0124, 0.0305, 0.111, 0.301, 1.14, 3.01])  # decay constants [1/s]
beta = np.sum(beta_i)  # total delayed neutron fraction = 0.0065
Lamb = 10.e-5  # average neutron lifetime [s]

v = 2200.e3  # neutron velocity cm/s
Ef = 3.204e-11  # energy per fission [J]
Sigma_f = 0.0065  # Macrosopic fission cross section in reactor [1/cm]
Vr = 3.e6  # reactor volumue [cc]
Lc = Lamb * v  # mean nutron travel length in core [cm]
VfFuel = 0.4
VfH2O = 1. - VfFuel

hc = 1.    # W/cm^2 * K avg heat transfer coeff between fuel and water
Ac = 4.e5  # cm^2  fuel to coolant contact area
Tin = 450.  # K coolant inlet temperature

alphaT = -0.007 * 1.e-5 / beta  # pcm / K / beta  reactivity per kelvin

# Number of delayed neutron groups
NUM_GROUPS = 6

# Control rod worth scaling factor for $0.2 total worth
ROD_WORTH_SCALING = 0.02042

# Excess reactivity of fresh fuel ($ dollars)
# This represents the excess reactivity built into fresh fuel to compensate for burnup
# Rods must be inserted to compensate: at rod=0, reactor is subcritical
# At ~33% rod withdrawal, reactor reaches criticality (due to sinusoidal worth curve)
RHO_EXCESS = 0.05  # $0.05 excess reactivity with fresh fuel

# Xenon-135 and Iodine-135 parameters
gamma_I = 0.061  # I-135 yield per fission (direct)
gamma_X = 0.003  # Xe-135 yield per fission (direct)
lambda_I = 2.87e-5  # I-135 decay constant [1/s] (half-life ~6.6 hr)
lambda_X = 2.09e-5  # Xe-135 decay constant [1/s] (half-life ~9.2 hr)
sigma_aX = 2.6e6 * 1e-24  # Xe-135 absorption cross-section [cm^2] (2.6 million barns)
eta = 0.6  # neutron survival factor (flux = eta * n)
nu = 2.43  # neutrons per fission for U-235

# Samarium-149 chain parameters (Nd-149 → Pm-149 → Sm-149)
gamma_Nd = 0.011  # Nd-149 yield per fission
lambda_Nd = 9.67e-5  # Nd-149 decay constant [1/s] (half-life ~1.73 hr)
lambda_Pm = 1.46e-6  # Pm-149 decay constant [1/s] (half-life ~53.1 hr)
sigma_aPm = 1400 * 1e-24  # Pm-149 absorption cross-section [cm^2] (1400 barns)
sigma_aSm = 40800 * 1e-24  # Sm-149 absorption cross-section [cm^2] (40,800 barns)
# Note: Sm-149 is essentially stable (half-life ~2e15 years), so no decay term

# ============================================================================
# Burnup and Fuel Isotope Depletion Parameters
# ============================================================================

# Microscopic cross-sections [cm^2] (1 barn = 1e-24 cm^2)
sigma_f235 = 585.0 * 1e-24   # U-235 fission cross-section [cm^2] (585 barns thermal)
sigma_c238 = 2.68 * 1e-24    # U-238 capture cross-section [cm^2] (2.68 barns thermal)
sigma_f239 = 750.0 * 1e-24   # Pu-239 fission cross-section [cm^2] (750 barns thermal)

# Initial fuel composition (number densities [atoms/cm^3])
# For typical 4% enriched UO2 fuel with density ~10.5 g/cm^3
N235_0 = 9.84e20     # Initial U-235 number density [atoms/cm^3]
N238_0 = 2.21e22     # U-238 number density [atoms/cm^3] (assumed constant for simplicity)
N239Pu_0 = 0.0       # Initial Pu-239 (none at fresh fuel)
NFP_0 = 0.0          # Initial fission products (none at fresh fuel)

# Fission product yield (lumped)
Y_FP = 2.0  # ~2 fission products per fission

# Heavy metal mass for burnup calculation
# M_HM = total heavy metal inventory in kg (U-235 + U-238 initially)
# For Vr = 3e6 cc with VfFuel = 0.4 and UO2 density ~10.5 g/cm^3
# Fuel volume = 3e6 * 0.4 = 1.2e6 cc
# UO2 mass = 1.2e6 * 10.5 = 1.26e7 g = 12600 kg
# U mass fraction in UO2 = 238/(238+32) = 0.881
# Heavy metal mass = 12600 * 0.881 = 11100 kg
M_HM = 11100.0  # Heavy metal inventory [kg]

# Reactivity coefficients for isotope changes [$/atom/cm^3]
# These relate number density changes to reactivity changes
# Burnup reactivity coefficients (scaled down for demo timescales)
# Real reactors see these effects over months/years; we scale for visualization
BURNUP_SCALE = 1e-3  # Scale factor to slow down burnup reactivity effects
k_235 = 1.5e-21 / beta * BURNUP_SCALE   # $ per (atom/cm^3) for U-235
k_239 = 2.0e-21 / beta * BURNUP_SCALE   # $ per (atom/cm^3) for Pu-239 (higher due to higher eta)
k_FP = 5.0e-23 / beta * BURNUP_SCALE    # $ per (atom/cm^3) for fission products (parasitic absorption)

# Define all terms in list S[]
# S = [neutrons/cc, C1, C2, C3, C4, C5, C6, fuelT, coolantT, rodPosition, I135, Xe135, Nd149, Pm149, Sm149, N235, N238, N239Pu, NFP, Burnup]
# Indices: 0=n, 1-6=C1-C6, 7=Tfuel, 8=Tcoolant, 9=rod, 10=I135, 11=Xe135, 12=Nd149, 13=Pm149, 14=Sm149, 15=N235, 16=N238, 17=N239Pu, 18=NFP, 19=Burnup

def dndt(S, t, reactivity):
    """
    Time derivative of neutron population with 6 delayed neutron groups.
    """
    # Sum contributions from all delayed neutron groups
    delayed_contribution = np.sum(lambda_i * S[1:7])
    ndot = (reactivity - beta) / Lamb * S[0] + delayed_contribution
    if S[0] <= 0. and ndot < 0.:
        return 0.
    else:
        return ndot


def dCdt(S, t, group_index):
    """
    Time derivative of delayed neutron precursor population for a specific group.
    group_index: 0-5 for groups 1-6
    Units of first term:
        (beta_i[unitless] / Lambda [s]) * [#/cm^3] = [#/cm^3-s]
    Units of second term:
        lambda_i [1/s] * [#/cm^3] = [#/cm^3 -s]
    """
    C_index = group_index + 1  # Precursor concentration at S[1] to S[6]
    Cdot = (beta_i[group_index] / Lamb) * S[0] - lambda_i[group_index] * S[C_index]
    if S[C_index] < 0. and Cdot < 0.:
        return 0.
    else:
        return Cdot


def dIdt(S, t):
    """
    Time derivative of Iodine-135 concentration.
    I-135 is produced directly from fission and decays to Xe-135.
    Units: [atoms/cm^3-s]
    """
    n = S[0]  # neutron density
    I = S[10]  # I-135 concentration
    
    # Production from fission: gamma_I * Sigma_f * flux
    production = gamma_I * Sigma_f * (eta * n)
    
    # Decay: lambda_I * I
    decay = lambda_I * I
    
    return production - decay


def dXdt(S, t):
    """
    Time derivative of Xenon-135 concentration.
    Xe-135 is produced directly from fission and from I-135 decay,
    and is removed by decay and neutron absorption (burnout).
    Units: [atoms/cm^3-s]
    """
    n = S[0]  # neutron density
    I = S[10]  # I-135 concentration
    X = S[11]  # Xe-135 concentration
    
    # Direct production from fission
    direct_production = gamma_X * Sigma_f * (eta * n)
    
    # Production from I-135 decay
    from_iodine = lambda_I * I
    
    # Decay
    decay = lambda_X * X
    
    # Neutron absorption (burnout)
    burnout = sigma_aX * (eta * n) * X
    
    return direct_production + from_iodine - decay - burnout


def dNddt(S, t):
    """
    Time derivative of Neodymium-149 concentration.
    Nd-149 is produced directly from fission and decays to Pm-149.
    Units: [atoms/cm^3-s]
    """
    n = S[0]  # neutron density
    Nd = S[12]  # Nd-149 concentration
    
    # Production from fission
    production = gamma_Nd * Sigma_f * (eta * n)
    
    # Decay to Pm-149
    decay = lambda_Nd * Nd
    
    return production - decay


def dPmdt(S, t):
    """
    Time derivative of Promethium-149 concentration.
    Pm-149 is produced from Nd-149 decay and removed by decay to Sm-149
    and neutron absorption.
    Units: [atoms/cm^3-s]
    """
    n = S[0]  # neutron density
    Nd = S[12]  # Nd-149 concentration
    Pm = S[13]  # Pm-149 concentration
    
    # Production from Nd-149 decay
    from_neodymium = lambda_Nd * Nd
    
    # Decay to Sm-149
    decay = lambda_Pm * Pm
    
    # Neutron absorption
    absorption = sigma_aPm * (eta * n) * Pm
    
    return from_neodymium - decay - absorption


def dSmdt(S, t):
    """
    Time derivative of Samarium-149 concentration.
    Sm-149 is produced from Pm-149 decay and removed only by neutron absorption.
    Sm-149 is essentially stable (no radioactive decay).
    Units: [atoms/cm^3-s]
    """
    n = S[0]  # neutron density
    Pm = S[13]  # Pm-149 concentration
    Sm = S[14]  # Sm-149 concentration
    
    # Production from Pm-149 decay
    from_promethium = lambda_Pm * Pm
    
    # Neutron absorption (burnout) - only removal mechanism
    burnout = sigma_aSm * (eta * n) * Sm
    
    return from_promethium - burnout


def dN235dt(S, t):
    """
    Time derivative of U-235 number density.
    U-235 is depleted by fission.
    Units: [atoms/cm^3-s]
    """
    n = S[0]  # neutron density
    N235 = S[15]  # U-235 concentration
    phi = eta * n * v  # neutron flux [n/cm^2-s]
    
    # Depletion by fission
    depletion = sigma_f235 * phi * N235
    
    return -depletion


def dN238dt(S, t):
    """
    Time derivative of U-238 number density.
    U-238 is depleted by neutron capture (producing Pu-239).
    Units: [atoms/cm^3-s]
    """
    n = S[0]  # neutron density
    N238 = S[16]  # U-238 concentration
    phi = eta * n * v  # neutron flux [n/cm^2-s]
    
    # Depletion by capture
    depletion = sigma_c238 * phi * N238
    
    return -depletion


def dN239Pudt(S, t):
    """
    Time derivative of Pu-239 number density.
    Pu-239 is produced from U-238 capture and depleted by fission.
    Units: [atoms/cm^3-s]
    """
    n = S[0]  # neutron density
    N238 = S[16]  # U-238 concentration
    N239Pu = S[17]  # Pu-239 concentration
    phi = eta * n * v  # neutron flux [n/cm^2-s]
    
    # Production from U-238 capture
    production = sigma_c238 * phi * N238
    
    # Depletion by fission
    depletion = sigma_f239 * phi * N239Pu
    
    return production - depletion


def dNFPdt(S, t):
    """
    Time derivative of lumped fission product concentration.
    Fission products are produced from fissions of U-235 and Pu-239.
    Units: [atoms/cm^3-s]
    """
    n = S[0]  # neutron density
    N235 = S[15]
    N239Pu = S[17]
    phi = eta * n * v  # neutron flux [n/cm^2-s]
    
    # Production from U-235 fission
    from_U235 = Y_FP * sigma_f235 * phi * N235
    
    # Production from Pu-239 fission
    from_Pu239 = Y_FP * sigma_f239 * phi * N239Pu
    
    return from_U235 + from_Pu239


def dBdt(S, t):
    """
    Time derivative of burnup.
    Burnup = integrated power / heavy metal mass.
    Units: [MWd/kgU per second]
    """
    n = S[0]  # neutron density
    power = qFuel(n)  # power in Watts
    power_MW = power / 1.0e6  # convert to MW
    
    # dB/dt = P(MW) / M_HM(kg) / 86400(s/day)
    # Result in MWd/kgU per second
    return power_MW / (M_HM * 86400.0)


def qFuel(n):
    """
    Given neutron population return thermal power [W]
    """
    return Vr * VfFuel * (n * v) * Sigma_f * Ef


def dTfdt(S, t, mdotC):
    """
    Time derivative of fuel temperature with improved heat transfer.
    Uses temperature-dependent properties and Dittus-Boelter correlation.
    """
    # Temperature-dependent UO2 heat capacity (J/g*K)
    T_fuel = S[7]  # fuel temperature at index 7
    CpUO2 = 0.2455 + 5.86e-5 * (T_fuel - 273.15)  # temperature dependent
    densityUO2 = 12.5  # g/cc
    
    # Improved heat transfer coefficient using flow-dependent correlation
    # Dittus-Boelter-like correlation: h = h0 * (mdot/mdot0)^0.8
    h0 = 1.5  # W/cm^2*K baseline heat transfer coefficient
    mdot0 = 1000.e3  # reference flow rate
    h = h0 * (mdotC / mdot0) ** 0.8
    
    return (qFuel(S[0]) - Ac * h * (S[7] - S[8])) / (densityUO2 * VfFuel * Vr * CpUO2)


def dTcdt(S, t, mdotC):
    """
    Time derivative of water coolant with improved heat transfer.
    Uses temperature-dependent properties.
    """
    # Temperature-dependent water properties
    T_coolant = S[8]  # coolant temperature at index 8
    CpH2O = 4.2 - 0.0005 * (T_coolant - 273.15)  # J/g*K (slightly temperature dependent)
    densityH2O = 1.0  # g/cc (simplified, could add T-dependence)
    
    # Use same improved heat transfer coefficient
    h0 = 1.5
    mdot0 = 1000.e3
    h = h0 * (mdotC / mdot0) ** 0.8
    
    return (Ac * h * (S[7] - S[8]) + CpH2O * (Tin - S[8]) * mdotC) / (densityH2O * Vr * CpH2O)


def diffRodWorth(h):
    """
    Improved differential control rod worth curve using cosine shape.
    Total worth: $0.1 from fully inserted to fully withdrawn
    h is fractional height: h=0 is fully inserted, h=100 is fully withdrawn
    delta_h * R(h) = reactivity change
    """
    scalingFac = ROD_WORTH_SCALING * 1.e-5 / beta
    return scalingFac * np.sin(np.pi * h / 100.0) * 100.0


def intRodWorth(h1, h2):
    """
    Integral control rod worth curve.
    Returns reactivity in dollars ($/Beta)
    Total worth: $0.1 from fully inserted to fully withdrawn
    """
    scalingFac = ROD_WORTH_SCALING * 1.e-5 / beta
    integral = lambda h: -100.0 * scalingFac * (100.0 / np.pi) * np.cos(np.pi * h / 100.0)
    return (integral(h2) - integral(h1))


def rho(S, t, hrate, deltaT):
    """
    Total reactivity including temperature, control rod, Xenon-135, Samarium-149 poisoning,
    and burnup-induced reactivity from isotope depletion.
    Reactivity in units of Dollars  (deltaK / Beta)
    Takes control rod movement rate in (%/s)
    """
    # Temperature reactivity feedback
    rho_temp = alphaT * (S[7] - Tin)
    
    # Control rod reactivity (subtracts from excess)
    # intRodWorth gives positive value as rod is withdrawn
    # We subtract rod worth from excess: more withdrawal = more positive reactivity
    rho_rod = intRodWorth(0., S[9]) - RHO_EXCESS
    
    # Xenon-135 poisoning reactivity (always negative)
    X = S[11]  # Xe-135 concentration
    rho_Xe = -(sigma_aX * eta * X) / (nu * Sigma_f * beta)
    
    # Samarium-149 poisoning reactivity (always negative)
    Sm = S[14]  # Sm-149 concentration
    rho_Sm = -(sigma_aSm * eta * Sm) / (nu * Sigma_f * beta)
    
    # Burnup-induced reactivity from isotope changes (scaled for demo timescales)
    # Positive contribution: Pu-239 buildup adds reactivity
    # Negative contributions: U-235 depletion and FP buildup remove reactivity
    N235 = S[15]
    N239Pu = S[17]
    NFP = S[18]
    rho_burnup = k_235 * (N235 - N235_0) + k_239 * (N239Pu - N239Pu_0) - k_FP * NFP
    
    return rho_temp + rho_rod + rho_Xe + rho_Sm + rho_burnup


def reactorSystem(S, t, hrate, deltaT, mdotC=1000.e3):
    """
    Complete reactor system with 6 delayed neutron groups, Xenon-135, Samarium-149 poisoning,
    fuel isotope depletion, and burnup tracking.
    State vector S = [n, C1-C6, Tfuel, Tcoolant, rodPosition, I135, Xe135, Nd149, Pm149, Sm149, N235, N238, N239Pu, NFP, Burnup]
    Total: 20 state variables
    """
    reactivity = rho(S, t, hrate, deltaT)
    
    # Build derivative vector
    dSdt = [dndt(S, t, reactivity)]
    
    # Add all 6 precursor group derivatives
    for i in range(NUM_GROUPS):
        dSdt.append(dCdt(S, t, i))
    
    # Add temperature, rod position, xenon, samarium, isotopes, and burnup dynamics
    dSdt.extend([
        dTfdt(S, t, mdotC),
        dTcdt(S, t, mdotC),
        hrate,
        dIdt(S, t),
        dXdt(S, t),
        dNddt(S, t),
        dPmdt(S, t),
        dSmdt(S, t),
        dN235dt(S, t),
        dN238dt(S, t),
        dN239Pudt(S, t),
        dNFPdt(S, t),
        dBdt(S, t)
    ])
    
    return dSdt
