# EUC's Blinkers  
**DELEULE Alix and DELZENNE-ZAMPARUTTI Tinaël**

## Project Overview  
This project aims to activate turn signals (blinkers) for electric unicycles (EUC) using gesture recognition. The goal is to eliminate the need for buttons or phone interactions by leveraging innovative sensor-based solutions.

### Objectives  
- Enable blinkers activation through gestures.  
- Develop and compare two proof-of-concept (POC) solutions using different sensor technologies:  
  - **IMU (Inertial Measurement Unit)**  made by **DELEULE Alix**
    - Employ `MPU-6050` IMU sensors on each hand to recognize gestures.  
    - Send motion data via BLE to a central unit.
    - [IMU report](IMU/)
  - **ToF (Time-of-Flight)**  made by **DELZENNE-ZAMPARUTTI Tinaël**
    - Utilize the multi-zone `SATEL-VL53L8CX` sensor for gesture detection via distance mapping.  
    - Provide visualizations of gesture data.  
    - [TOF report](TOF/)
![](img/nylonove-full-upgrade-set-for-leperkim-lynx.jpg)


```
.
├── .gitignore
├── IMU
│   ├── FW
│   │   ├── IMU_ESP32_CENTRE_FW
│   │   │   └── IMU_ESP32_CENTRE_FW.ino
│   │   ├── IMU_ESP32_LEFT_FW
│   │   │   └── IMU_ESP32_LEFT_FW.ino
│   │   └── IMU_ESP32_RIGHT_FW
│   │       └── IMU_ESP32_RIGHT_FW.ino
│   ├── README.md
│   ├── data_processing
│   │   ├── peak_detection
│   │   │   ├── classification.py
│   │   │   ├── data_testing.ipynb
│   │   │   ├── img
│   │   │   │   └── ...
│   │   │   ├── logs
│   │   │   │   └── ...
│   │   │   └── peak_detection_plot.ipynb
│   │   └── turn_detection
│   │       ├── logs
│   │       │   └── ...
│   │       └── plot.ipynb
│   ├── img
│   │   └── ...
│   ├── tools
│   │   ├── BLE_scanner.py
│   │   ├── BLE_terminal.py
│   │   ├── BLE_visualizer.py
│   │   ├── ESP32-Pinout.webp
│   │   ├── IMU_visualizer.py
│   │   ├── SERIAL_GUI.py
│   │   └── visualizer_GUI.py
│   └── vid
│       └── ...
├── README.md
├── requirements.txt
├── TOF
│   ├── Data_processing
│   │   ├── Archives_csv
│   │   │   └── ...
│   │   ├── Archives_json
│   │   │   └── ...
│   │   ├── BLE_to_CSV.py
│   │   ├── Entrainement.py
│   │   ├── GUI_couple.py
│   │   ├── TOF_BLE_GUI.py
│   │   ├── TOF_serial_GUI.py
│   │   ├── data.csv
│   │   ├── data_label
│   │   │   └── ...
│   │   ├── mp4_to_frames.py
│   │   ├── output
│   │   │   ├── model.cc
│   │   │   └── model.tflite
│   │   ├── timestamp.py
│   │   └── vid
│   │       └── ...
│   ├── Firmware
│   │   ├── ESP32
│   │   │   ├── ESP32_BLE _V2.ino
│   │   │   ├── ESP32_BLE.ino
│   │   │   ├── ESP32_BLE_V1.ino
│   │   │   └── ESP32_serial.ino
│   │   └── STM_32_serial
│   │       ├── VL53L8CX_SimpleRanging
│   │       │   └── ...(STM32 Project Files)
│   │       └── app_tof.c
│   ├── README.md
│   ├── img
│   │   └── ...
│   └── vid
│       └── ...
└── img
    └── ...
```

## Presentation Videos

[Link to the YouTube pitch video](https://youtube.com/shorts/kZVuSzMemOc?feature=share)

[Link to the YouTube tutorial video](https://www.youtube.com/watch?v=0yWugvFKKVM)

## List of Dependencies and Prerequisites

- ([STM32-duino](https://github.com/stm32duino/VL53L8CX/blob/main/examples/VL53L8CX_HelloWorld_I2C/VL53L8CX_HelloWorld_I2C.ino))
- [X-CUBE-TOF1](https://www.st.com/en/ecosystems/x-cube-tof1.html)
- requirements.txt

## Startup Procedure

- Follow the video guide
- For python code juste install the requirements.txt and execute them
