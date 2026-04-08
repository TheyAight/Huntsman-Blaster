# AI Auto-Foam Dart Blaster

An automated, AI-powered turret that uses YOLOv11 for real-time target tracking and a custom mechanical pusher system to fire foam darts. This project is designed to run on a Raspberry Pi 5.

## Hardware Overview
- Controller: Raspberry Pi 5
- Vision: USB Webcam or Pi Camera
- AI Model: YOLOv11n (Nano)
- PWM Driver: PCA9685 (Adafruit ServoKit)
- Actuators: 2x Standard Servos (Pan/Tilt), 1x Continuous Rotation Servo (Pusher)
- Firing Mechanism: 3D-printed rack and pinion gear system
- Reset: Compressed spring-return slide
- Flywheels: High-torque DC motors controlled via an N-Channel MOSFET (GPIO 17)

## How It Works
1. Detection: The Pi 5 captures frames and runs them through YOLOv11, filtering for persons (class 0).
2. Tracking: The script calculates the error between the target's center and the frame's center, moving the Pan/Tilt servos to compensate.
3. Priming: Once a lock is achieved for 0.5s, the MOSFET triggers the flywheel motors.
4. Firing: After a 1s priming delay, the continuous servo rotates the gear, pushing the rack forward to chamber a dart.
5. Mechanical Reset: Once the push duration is met, the servo stops, allowing the compressed spring to pull the slide back to the starting position automatically.

## Repository Structure
---
- main.py: Core logic for YOLO tracking and hardware control
- requirements.txt: Python dependencies
- .gitignore: Files to exclude (models, pycache)
- /models: Directory for YOLOv11 weights (.pt)
- /hardware: Wiring diagrams and mechanical notes
- /docs: Project design and flowcharts

## Installation and Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/Huntsman-Blaster.git
cd auto-foam-blaster
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the System
Ensure your PCA9685 is connected via I2C and your MOSFET is on Pin 17.
```bash
python main.py
```

## Mechanical Calibration
The following variables in main.py are critical for the spring-return system:
- PUSH_DURATION: The time the servo spins forward to compress the spring.
- SERVO_SPEED: The throttle required to overcome the spring's tension.
- FIRE_DELAY: The time allowed for flywheel motors to reach max RPM.

## Future Updates
- Ammo counter integration.
- Friendly vs Hostile target identification.
