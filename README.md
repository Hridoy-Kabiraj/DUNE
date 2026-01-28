# PyReactor - Nuclear Reactor Simulator

## About

PyReactor is an advanced point kinetics nuclear reactor simulator with a graphical user interface (GUI) designed for educational purposes and reactor physics demonstrations. This package provides a comprehensive simulation environment that models nuclear reactor behavior, including neutronics, thermal hydraulics, and control systems.

### Key Features

- **Real-time Reactor Simulation**: Implements a 6-group delayed neutron precursor model based on point kinetics equations
- **Interactive GUI**: Built with wxPython and matplotlib for real-time data visualization
- **Thermal-Hydraulic Modeling**: Temperature-dependent heat transfer with Dittus-Boelter correlation
- **Control Systems**: Supports both manual control rod operation and automatic PID-based power control
- **Safety Systems**: Automatic SCRAM functionality based on temperature setpoints
- **Arduino Integration**: Interfaces with physical 3D printed reactor model for hands-on demonstrations
- **Educational Tool**: Designed for K-12 outreach and nuclear engineering education

![3D Printed Reactor Physical Model](Reactor%20Arduino%20Physical%20Setup.jpeg)

## Project Structure and Components

### Core Modules

#### 1. **reactorPhysics.py** - Nuclear Physics Engine
This module contains the fundamental reactor physics equations and parameters:

- **Point Kinetics Model**: Implements the time-dependent neutron diffusion equations with 6 delayed neutron groups for U-235
- **Delayed Neutron Data**: 
  - Beta values (β₁ through β₆): Individual delayed neutron fractions
  - Lambda values (λ₁ through λ₆): Decay constants ranging from 0.0124 to 3.01 s⁻¹
  - Total delayed neutron fraction: β_total = 0.0065
  - Average neutron lifetime: Λ = 10⁻⁵ seconds

- **Thermal-Hydraulic Models**:
  - Temperature-dependent UO₂ fuel heat capacity
  - Flow-dependent heat transfer using Dittus-Boelter correlation
  - Coupled fuel and coolant temperature evolution
  - Reactivity feedback from temperature coefficients (α_T = -0.007 × 10⁻⁵ per K per beta)

- **Power Calculation**: Converts neutron population to thermal power output using:
  - Energy per fission: 3.204 × 10⁻¹¹ J
  - Macroscopic fission cross-section: 0.0065 cm⁻¹
  - Reactor volume: 3 × 10⁶ cm³

#### 2. **reactor.py** - Reactor Control System
The `Reactor` class provides the main interface for reactor operations:

- **State Vector Management**: Tracks [neutrons/cc, C₁-C₆ precursors, T_fuel, T_coolant, rod position]
- **Time Integration**: Uses scipy's odeint for solving the stiff ODE system
- **Control Rod Dynamics**: Realistic rod motion with rate limiting
- **PID Power Control**: Automatic power level regulation
- **Coolant Flow Control**: Variable coolant mass flow rate (up to 1000 kg/s)
- **Safety Systems**:
  - Fuel temperature SCRAM at 1700 K
  - Coolant temperature SCRAM at 700 K
  - Automatic control rod insertion on SCRAM

#### 3. **legoReactor.py** - GUI and Visualization
The graphical interface built with wxPython provides:

- **Real-time Plotting**: Live power, fuel temperature, and coolant temperature traces
- **Control Interfaces**:
  - Manual control rod position slider
  - Power setpoint control
  - Coolant flow rate adjustment
  - SCRAM button for emergency shutdown
  - Pause/Resume simulation control
  - Zoom controls for plot viewing

- **Monitoring Displays**:
  - Current reactor power (MW)
  - Fuel and coolant temperatures (K)
  - Control rod position (%)
  - Reactivity ($ρ$ in dollars)
  - Delayed neutron precursor populations

- **Arduino Communication**: Serial interface to physical reactor model

#### 4. **Arduino Integration** (arduino/reactorSketch/)
The Arduino code provides physical feedback through:
- **Servo Control**: Moves 3D printed control rods to match simulator position
- **LED Indication**: RGB LED brightness represents reactor power level
  - Blue LED: Normal operation (power level)
  - Red LED: SCRAM condition
- **Motor Control**: PWM-driven motor for visual effects (e.g., coolant pump simulation)

![Arduino Physical Setup](Reactor%20Arduino%20Physical%20Setup.jpeg)

**Circuit Diagram**:

![Arduino Setup Circuit Diagram](Arduino%20Setup%20Cricuit%20diagram.jpeg)

The circuit diagram shows the complete wiring configuration for the Arduino-based physical reactor model, including:
- Servo motor connections (Pin 9) for control rod actuation
- RGB LED wiring (Pins 6 and 11) for power level indication
- Motor PWM control (Pin 3) for coolant pump visualization
- Power supply and ground connections
- Resistor values for LED current limiting

## Physics and Mathematical Model

### Neutron Kinetics Equations

The simulator solves the coupled point kinetics equations with 6 delayed neutron groups:

$$\frac{dn}{dt} = \frac{\rho - \beta}{\Lambda}n + \sum_{i=1}^{6}\lambda_i C_i$$

$$\frac{dC_i}{dt} = \frac{\beta_i}{\Lambda}n - \lambda_i C_i$$

Where:
- $n$ = neutron population density
- $C_i$ = delayed neutron precursor concentration for group i
- $\rho$ = reactivity (includes temperature feedback)
- $\beta$ = total delayed neutron fraction
- $\beta_i$ = delayed neutron fraction for group i
- $\Lambda$ = prompt neutron lifetime
- $\lambda_i$ = decay constant for group i

### Reactivity Feedback

The total reactivity includes contributions from:
- **Control Rod Position**: Primary control mechanism
- **Fuel Temperature**: Doppler broadening effect (negative feedback)
- **Coolant Temperature**: Moderator temperature coefficient (negative feedback)

### Thermal Hydraulics

Fuel temperature evolution:
$$\frac{dT_f}{dt} = \frac{Q_{fission} - h \cdot A_c (T_f - T_c)}{m_f \cdot C_{p,fuel}}$$

Coolant temperature evolution:
$$\frac{dT_c}{dt} = \frac{h \cdot A_c (T_f - T_c) + \dot{m}_c \cdot C_{p,coolant}(T_{in} - T_c)}{m_c \cdot C_{p,coolant}}$$

Where:
- $Q_{fission}$ = fission power generated
- $h$ = heat transfer coefficient (flow-dependent)
- $A_c$ = fuel-coolant contact area (4 × 10⁵ cm²)
- $\dot{m}_c$ = coolant mass flow rate
- $C_p$ = specific heat capacity

## Reactor Operation Demonstrations

### Startup Transient
![Reactor Startup - Exponential Power Rise](Reactor%20Startup%20exponential%20power%20rise.jpeg)

This image demonstrates a typical reactor startup sequence showing exponential power rise as control rods are withdrawn. The behavior follows the reactor period equation demonstrating subcritical to critical transition.

### Prompt Jump Phenomenon
![Reactor Prompt Jump Transient](Reactor%20Transient(Prompt%20Jump).jpeg)

This captures a reactivity insertion accident resulting in a prompt jump. When reactivity exceeds one dollar ($ρ > $1.00), the reactor becomes prompt critical, causing an instantaneous power jump followed by temperature feedback stabilization.

### SCRAM Event
![Reactor SCRAM Event](Reactor%20SCARM.jpeg)

Documentation of an automatic SCRAM (Safety Control Rod Axe Man) event triggered by exceeding temperature safety limits. Shows rapid power decrease as control rods are fully inserted and negative reactivity is added.



## Installation

### Prerequisites

PyReactor requires Python 3.6 or higher and the following dependencies:
- **numpy** (≥1.20): Numerical computing and array operations
- **scipy** (≥1.6): ODE solver for reactor kinetics equations
- **matplotlib** (≥3.3): Plotting and data visualization
- **wxPython** (≥4.1): Cross-platform GUI toolkit
- **pyserial** (≥3.0): Serial communication with Arduino (optional)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/wgurecky/pyReactor.git
   cd pyReactor
   ```

2. **Install in development mode**:
   ```bash
   python setup.py develop
   ```
   
   Or using pip:
   ```bash
   pip install -e .
   ```

3. **Verify installation**:
   ```bash
   pyReactor --help
   ```

### Arduino Setup (Optional)

For physical reactor model integration:

1. Upload `arduino/reactorSketch/reactorSketch.ino` to your Arduino board
2. Connect servo to pin 9, RGB LED to pins 6 and 11, and motor to pin 3
3. Connect Arduino via USB before starting the simulator
4. The simulator will automatically detect and connect to the Arduino

## Usage Guide

### Starting the Simulator

Launch the reactor GUI with the command:
```bash
pyReactor
```

### Operating Modes

#### Manual Control Mode (Default)
- Use the vertical slider to set control rod position (0-100%)
- Rods move at a realistic rate (~10%/second)
- Monitor reactivity in dollars displayed in real-time
- Watch power respond to rod movements with reactor period dynamics

#### Automatic Power Control Mode
1. Check the "Power Control" toggle
2. Set desired power level in the power setpoint box
3. The PID controller automatically adjusts control rods to maintain setpoint
4. Observe how the controller responds to temperature feedback

### Control Interfaces

#### Main Controls
- **Rod Position Slider**: Manual control rod height (0% = fully inserted, 100% = fully withdrawn)
- **Power Setpoint**: Target power level in MW for automatic control
- **Coolant Flow**: Adjust coolant mass flow rate (kg/s)
- **SCRAM Button**: Emergency shutdown - inserts all control rods immediately
  - Press again to reset SCRAM condition and unlock reactor
- **Pause**: Freeze simulation to examine current state

#### Display Monitors
- **Power Plot**: Real-time reactor power in MW (upper panel)
- **Temperature Plot**: Fuel temperature (red) and coolant temperature (blue) in Kelvin (lower panel)
- **Rod Height Indicator**: Vertical bar showing current rod position
- **Reactivity Display**: Current reactivity in dollars ($ρ$)
- **Time Scale**: Adjustable zoom for viewing different time windows

### Operational Guidelines

#### Safe Startup Procedure
1. Verify coolant flow is adequate (default 1000 kg/s)
2. Slowly withdraw control rods (increase position from 0%)
3. Watch reactivity approach zero dollars
4. Continue rod withdrawal until desired power is reached
5. Fine-tune position to stabilize at target power

#### Understanding Reactivity
- **Subcritical** ($ρ < 0$): Power decreasing, reactor shutting down
- **Critical** ($ρ = 0$): Power stable, equilibrium condition
- **Supercritical** ($ρ > 0$): Power increasing
- **Prompt Critical** ($ρ > $1.00$): Dangerous! Very rapid power increase

#### Temperature Monitoring
- **Fuel Temperature**: Must stay below 1700 K (automatic SCRAM above)
- **Coolant Temperature**: Must stay below 700 K (automatic SCRAM above)
- Temperature increases lag behind power changes due to thermal inertia
- Higher coolant flow improves heat removal and lowers temperatures

### Safety Systems

The simulator includes realistic safety features:

1. **Automatic SCRAM Triggers**:
   - Fuel temperature > 1700 K
   - Coolant temperature > 700 K
   - Both conditions cause immediate rod insertion

2. **SCRAM Recovery**:
   - Click SCRAM button again to unlock
   - Reactor must be manually restarted from subcritical state
   - Delayed neutron precursors must rebuild (takes 30-60 seconds)

3. **Physical Limits**:
   - Rods cannot be withdrawn beyond 100%
   - Rods cannot be inserted below 0%
   - Coolant flow has minimum/maximum bounds

### Experimental Scenarios

#### Experiment 1: Reactor Period
- Start with rods at 0%
- Quickly move to 45% and hold
- Observe exponential power rise
- Calculate reactor period from plot: $T = \frac{t}{\ln(P_2/P_1)}$

#### Experiment 2: Temperature Feedback
- Establish steady state at high power (400+ MW)
- Suddenly reduce coolant flow by 50%
- Observe power reduction due to negative temperature feedback
- Demonstrates inherent safety of negative temperature coefficients

#### Experiment 3: Prompt Criticality
- **WARNING**: For educational observation only!
- Starting from low power, rapidly insert large reactivity (>$1.00)
- Observe prompt jump followed by temperature-limited stabilization
- Shows importance of staying below prompt critical limit

#### Experiment 4: SCRAM Response
- Operate at high power
- Press SCRAM button
- Observe power decay from delayed neutrons
- Note the characteristic decay time (~80 seconds for 6-group model)

## Educational Applications

### Target Audiences
- **K-12 Students**: Introduction to nuclear energy and reactor safety
- **Undergraduate Engineering**: Reactor physics and control systems
- **Public Outreach**: Demonstrations at science fairs and events
- **Training**: Basic reactor operation concepts

### Learning Objectives
1. Understand neutron population dynamics and delayed neutrons
2. Learn about reactivity and reactor control
3. Observe temperature feedback effects
4. Experience safety system operation
5. Appreciate the role of control systems in reactor operation

### Classroom Integration
- Use with 3D printed physical model for tactile learning experience
- LED brightness provides visual feedback of power level
- Moving servo demonstrates control rod mechanism
- Combine with discussion of real reactor designs (PWR, BWR, etc.)

## Technical Details

### Numerical Methods
- **ODE Solver**: scipy.integrate.odeint with adaptive step sizing
- **Time Step**: Default 5 ms for stability with stiff equations
- **Update Rate**: GUI refreshes at 1 Hz, physics calculates at 500 Hz
- **Numerical Stability**: Implicit solver handles stiff reactor kinetics

### Model Fidelity
- 6-group delayed neutron model (industry standard for training simulators)
- Lumped parameter thermal hydraulics (0D approximation)
- Point kinetics (spatially averaged neutronics)
- Representative of small research reactor or PWR unit cell

### Performance
- Real-time capable on modern hardware
- Scales to 1000x faster-than-real-time for rapid scenario testing
- Memory efficient with circular buffer for plot data

### Code Architecture
- **Model-View-Controller** design pattern
- Physics engine separated from GUI for testability
- Extensible for additional physics models
- Well-documented with inline comments

## Troubleshooting

### Common Issues

**Arduino not detected**:
- Check USB connection and permissions
- Verify correct COM port in device manager
- Ensure pyserial is installed: `pip install pyserial`

**GUI not displaying**:
- Install wxPython: `pip install wxPython`
- On Linux, may need system packages: `sudo apt-get install python3-wxgtk4.0`

**Simulation crashes**:
- Reduce time step if numerical instabilities occur
- Check that initial conditions are physical
- Ensure numpy/scipy versions are compatible

**Slow performance**:
- Increase plot update interval (decrease refresh rate)
- Reduce stored data history length
- Close other applications

### Debug Mode
Enable verbose output for troubleshooting:
```python
# In legoReactor.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```


## Future Enhancements

Potential improvements and extensions:

### Physics Models
- [ ] Xenon and Samarium poisoning dynamics
- [ ] Burnup and fuel depletion tracking
- [ ] Multi-region core model (radial/axial variations)
- [ ] Improved neutron kinetics with spatial effects

### Control Systems
- [ ] Advanced control algorithms (MPC, fuzzy logic)
- [ ] Load-following operation modes
- [ ] Grid frequency response simulation
- [ ] Multiple control rod banks

### Visualization
- [ ] 3D reactor core visualization
- [ ] Neutron flux distribution animation
- [ ] Historical data logging and replay
- [ ] Export data to CSV/HDF5

### Hardware Integration
- [ ] Support for additional Arduino sensors (temperature, flow)
- [ ] Raspberry Pi integration for standalone operation
- [ ] Multiple 3D printed reactor units for comparison
- [ ] VR/AR visualization support

## Contributing

Contributions are welcome! Areas where help is needed:

- Documentation improvements and tutorials
- Additional example scenarios and lesson plans
- Testing on different platforms
- Bug reports and feature requests
- Translation to other languages

Please submit issues and pull requests on GitHub.

## Documentation

For comprehensive technical documentation, including detailed reactor physics derivations, implementation details, and experimental results, please refer to:

**[DUNE Project Report](doc/DUNE%20Report.pdf)** - Complete technical documentation covering:
- Theoretical background and nuclear physics equations
- System architecture and software design
- Hardware integration and Arduino implementation
- Validation and testing results
- Educational applications and case studies
- Performance analysis and benchmarking

## Publications and Presentations

This simulator has been used in:
- K-12 STEM outreach events
- University reactor physics courses
- Public science demonstrations
- Nuclear engineering department open houses

## Acknowledgments

- Original concept and development: William Gurecky
- Current maintainer: Hridoy Kabiraj
- Delayed neutron data from ENDF/B-VII.1 nuclear data library
- Inspiration from commercial reactor training simulators
- Special thanks to educators who provided feedback

## Related Resources

### Learning Materials
- [Nuclear Reactor Physics (Lamarsh & Baratta)](https://www.pearson.com/en-us/subject-catalog/p/introduction-to-nuclear-engineering/P200000003276)
- [Fundamentals of Nuclear Science and Engineering (Shultis & Faw)](https://www.crcpress.com/Fundamentals-of-Nuclear-Science-and-Engineering-Third-Edition/Shultis-Faw/p/book/9781498769297)
- [MIT OpenCourseWare: Nuclear Engineering](https://ocw.mit.edu/courses/22-01-introduction-to-nuclear-engineering-and-ionizing-radiation-fall-2016/)

### Similar Projects
- [OpenMC](https://openmc.org/): Monte Carlo particle transport code
- [SCALE](https://www.ornl.gov/scale): Comprehensive nuclear safety analysis suite  
- [Serpent](http://montecarlo.vtt.fi/): Reactor physics burnup calculation code

### Nuclear Engineering Organizations
- [American Nuclear Society (ANS)](https://www.ans.org/)
- [International Atomic Energy Agency (IAEA)](https://www.iaea.org/)
- [Nuclear Energy Institute (NEI)](https://www.nei.org/)

## Frequently Asked Questions (FAQ)

**Q: Is this simulator accurate for real reactor design?**  
A: No. PyReactor uses simplified point kinetics and 0D thermal hydraulics suitable for education and conceptual understanding. Real reactor design requires detailed 3D neutronics and CFD analysis.

**Q: Can I use this for homework/projects?**  
A: Yes! The software is open source and free to use for educational purposes. Please cite this repository in your work.

**Q: How realistic are the physics models?**  
A: The 6-group delayed neutron model is standard for training simulators. Thermal hydraulics are simplified but capture essential behavior. Good for qualitative understanding, not quantitative design.

**Q: Why does the reactor SCRAM when I withdraw rods too quickly?**  
A: Rapid rod withdrawal causes power to rise exponentially. Power heats the fuel, and if temperature limits are exceeded, automatic SCRAM occurs. This demonstrates the importance of controlled startups.

**Q: What's the difference between dollars and absolute reactivity?**  
A: Reactivity in dollars ($) is normalized by β (delayed neutron fraction). $1.00 is the prompt critical threshold. Absolute reactivity ρ has units of Δk/k.

**Q: Can I modify the reactor parameters?**  
A: Yes! Edit `reactorPhysics.py` to change core size, fuel type, temperature coefficients, etc. Rerun `python setup.py develop` after changes.

**Q: Why is there a delay after SCRAM before I can restart?**  
A: Delayed neutron precursors (with half-lives of 0.2 to 55 seconds) must decay. Real reactors also have xenon buildup considerations.

**Q: Does this work on Raspberry Pi?**  
A: It should work but may be slow. The GUI is computationally intensive. Consider using a more powerful computer for smooth operation.

## Version History

### Version 0.1 (Current)
- Initial public release
- 6-group delayed neutron model
- Temperature-dependent thermal hydraulics
- PID power control
- Arduino/LEGO integration
- wxPython GUI with matplotlib plots
- Automatic SCRAM systems

### Planned for Version 0.2
- Data export functionality
- Improved parameter configuration UI
- Pre-configured scenario library
- Enhanced documentation and tutorials

## Authors

**Hridoy Kabiraj**  
Email: rudrokabiraj@gmail.com  
GitHub: [@hridoy](https://github.com/hridoy)

**Original Developer: William Gurecky**

## License

This project is currently unlicensed. All rights reserved by the author.

For usage permissions or licensing inquiries, please contact the author.

---

## Contact and Support

For questions, bug reports, or feature requests:
- Open an issue on [GitHub](https://github.com/wgurecky/pyReactor/issues)
- Email: rudrokabiraj@gmail.com

For educational partnerships or collaboration inquiries, please reach out via email.

---

**⚠️ Disclaimer**: This software is for educational and demonstration purposes only. It is not intended for use in actual nuclear reactor design, operation, or safety analysis. Always consult qualified nuclear engineers and follow proper regulatory procedures for real reactor systems.

---

*Last Updated: January 2026*
