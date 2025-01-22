# IMU Solution  
## System Description  
The IMU-based system consists of three main components:  
1. A central module (ESP32-WROOM microcontroller and IMU).  
2. Two hand modules (each with an ESP32-WROOM microcontroller and an MPU-6050 IMU).  

Each hand module collects accelerometer and gyroscope data and sends it via BLE to the central unit, which processes the data and controls the blinkers.

![IMU System Diagram](img/MEMS_system_diagram.png)
![IMU System Diagram](img/imu_illustration2.jpg)

## Features and Progress  
- **Data Visualization**  
  - Creation of a GUI to visualize real-time motion data.  
- **Data Logging**  
  - Scripts to log BLE-transmitted motion data for further analysis.  
- **Blinker Control**  
  - Prototyping LED blinkers to simulate real-world functionality.  

## Future Work  
- **IMU Solution**  
  - Integrate the second hand module to enable control of both blinkers.  
  - Implement an orientation fusion algorithm (e.g., MotionFX).  
  - Add automatic turn signal deactivation based on yaw velocity.  
  - Miniaturize components and enable induction charging. 

--- 
## Notes

Utilisation de MEMS Studio afin de generer un decision tree a partir des donnees IMU, FAILED algo fait main
mems studio features:
F1_MEAN_ACC_Z",
        "F2_MINIMUM_ACC_Z",
        "F3_VARIANCE_ACC_Y",
        "F4_MEAN_GYR_V",
        "F5_MAXIMUM_ACC_X",
        "F6_PEAK_TO_PEAK_ACC_Y",
        "F7_ENERGY_GYR_Z",
        "F8_VARIANCE_GYR_Z",
        "F9_MAXIMUM_ACC_V",
        "F10_MINIMUM_GYR_X",
        "F11_MEAN_ACC_X",
        "F12_VARIANCE_GYR_X",
        "F13_MINIMUM_ACC_V",
        "F14_MEAN_ACC_V",
        "F15_ENERGY_GYR_Y"