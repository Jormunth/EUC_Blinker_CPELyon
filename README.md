# EUC's Blinkers
*DELEULE Alix and Delzenne-Zamparutti Tinaël*

We will first develop 2 different solutions in parallel to have POC:
- TOF
- MEMS

## TOF 
Use of the multi-zone ToF sensor `SATEL-VL53L8CX` to detect hand and arm gestures.

## MEMS
Use of 2 IMU, 1 on each hand that will recognize gestures and send the information back to the main unit via BLE.

We are using a MPU-6050 as the IMU it is connected to an ESP32 via I2C.
The ESP32 broadcasts the accel and gyro data on BLE to the main EPS32 unit on the wheel.

![](img/MEMS_system_diagram.png)



- creation d'un gui permettant de visualiser les donner
- un script permettant de logger les donnees avec le BLE
- blinkers des leds

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