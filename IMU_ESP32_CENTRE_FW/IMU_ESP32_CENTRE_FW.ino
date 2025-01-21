#include <BLEDevice.h>
#include <BLEClient.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps612.h"
// Arduino Wire library is required if I2Cdev I2CDEV_ARDUINO_WIRE implementation
// is used in I2Cdev.h
#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
#include "Wire.h"
#endif

#define ENABLE_DEBUG_PRINT_BLE 0
#define ENABLE_DEBUG_PRINT_IMU 0
#define ENABLE_DEBUG_PRINT_IMU_BLE 0
#define ENABLE_IMU_FUSION 1
#define DEBUG 1

// UUIDs pour le service et la caractéristique BLE
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define BLE_DEVICE_NAME     "ESP32_EUC_Centre"

// BLE Address of hand modules
#define LEFT_HAND_ADDRESS "CC:DB:A7:92:9F:0E"
#define RIGHT_HAND_ADDRESS "F8:B3:B7:22:2E:3A"

// Pins pour les LEDs de clignotement
#define LEFT_BLINKER_PIN 18
#define RIGHT_BLINKER_PIN 19

#define LEFT 0
#define RIGHT 1

// Configuration de l'accéléromètre et du gyroscope
#define ACCEL_RANGE 4   // Options: 2, 4, 8, 16 (en g)
#define GYRO_RANGE 500  // Options: 250, 500, 1000, 2000 (en °/s)
#define ODR_IMU 52      // Options: 12.5, 26, 52, 104, 208, 416, 833 (en Hz)

// Variables pour l'échelle
float LSB_TO_G;
float LSB_TO_DPS;
float LSB_TO_MDPS;
float LSB_TO_MG;
float DPS_TO_RADPS = M_PI / 180.0f;
float G_TO_MS2 = 9.8;

// Variables pour le clignotement
bool isBlinkingL = false;
bool isBlinkingR = false;
const unsigned long BLINKER_FREQUENCY = 1;  // Hz
const unsigned long BLINKER_PERIOD = 1000 / BLINKER_FREQUENCY;  // ms
long int prev_millis_blink_command = 0;
int isTurning = false;
float prevYaw = 0;
#define BUFFER_SIZE 15
float dy_buffer[BUFFER_SIZE];
unsigned int bufferIndex = 0;
boolean isFirstBlink = true;
float startYaw = 0;
#define TURN_ANGLE_THRESHOLD 20


// BLE client variables
BLEClient* leftClient = nullptr;
BLEClient* rightClient = nullptr;

// Remote characteristics
BLERemoteCharacteristic* leftRemoteCharacteristic = nullptr;
BLERemoteCharacteristic* rightRemoteCharacteristic = nullptr;

// Declare the BLE characteristic globally
BLECharacteristic *pCharacteristic;
BLEServer *pServer;
bool BLEConnected = false;

// Création de l'objet MPU6050
// class default I2C address is 0x68
// specific I2C addresses may be passed as a parameter here
// AD0 low = 0x68 (default for SparkFun breakout and InvenSense evaluation board)
// AD0 high = 0x69
MPU6050 mpu;
// #define OUTPUT_READABLE_YAWPITCHROLL
#define OUTPUT_READABLE_EULER

bool IMUConnected = false;
// Timing variables for MPU6050 data reading
unsigned long lastReadTime = 0;
const unsigned long readIntervalIMU = 1000 / ODR_IMU;  // Interval in ms (e.g., ~19ms for 52Hz)

#define INTERRUPT_PIN 2  // use pin 2 on Arduino Uno & most boards
#define LED_PIN 13 // (Arduino is 13, Teensy is 11, Teensy++ is 6)
bool blinkState = false;

// MPU control/status vars
bool dmpReady = false;  // set true if DMP init was successful
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
uint8_t devStatus;      // return status after each device operation (0 = success, !0 = error)
uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[64]; // FIFO storage buffer

// orientation/motion vars
Quaternion q;           // [w, x, y, z]         quaternion container
VectorInt16 aa;         // [x, y, z]            accel sensor measurements
VectorInt16 gy;         // [x, y, z]            gyro sensor measurements
VectorInt16 aaReal;     // [x, y, z]            gravity-free accel sensor measurements
VectorInt16 aaWorld;    // [x, y, z]            world-frame accel sensor measurements
VectorFloat gravity;    // [x, y, z]            gravity vector
float euler[3];         // [psi, theta, phi]    Euler angle container
float ypr[3];           // [yaw, pitch, roll]   yaw/pitch/roll container and gravity vector

// ================================================================
// ===               INTERRUPT DETECTION ROUTINE                ===
// ================================================================

volatile bool mpuInterrupt = false;     // indicates whether MPU interrupt pin has gone high
void dmpDataReady() {
  mpuInterrupt = true;
}

// BLE Server callback to track connection status
class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    BLEConnected = true;
    Serial.println("[BLE] Client connecté.");
  }

  void onDisconnect(BLEServer* pServer) {
    BLEConnected = false;
    Serial.println("[BLE] Client déconnecté.");
    pServer->getAdvertising()->start();  // Redémarrer la publicité
    Serial.println("[BLE] Publicité BLE redémarrée.");
  }
};

// Callback to handle notifications for LEFT HAND
class LeftHandCallback : public BLEClientCallbacks {
  void onConnect(BLEClient* pClient) {
    Serial.println("[BLE] Connected to LEFT hand.");
  }

  void onDisconnect(BLEClient* pClient) {
    Serial.println("[BLE] Disconnected from LEFT hand.");
    isBlinkingL = false;
  }
};

void leftNotificationCallback(BLERemoteCharacteristic* pCharacteristic, uint8_t* data, size_t length, bool isNotify) {
  String receivedData = String((char*)data).substring(0, length);
  if (ENABLE_DEBUG_PRINT_BLE){
    Serial.print("[LEFT] Received: ");
    Serial.println(receivedData);
  }

  if (receivedData == "2") {
    blinkerControl(LEFT, HIGH);
  } else if (receivedData == "1") {
    blinkerControl(LEFT, LOW);
  }
}

// Callback to handle notifications for RIGHT HAND
class RightHandCallback : public BLEClientCallbacks {
  void onConnect(BLEClient* pClient) {
    Serial.println("[BLE] Connected to RIGHT hand.");
  }

  void onDisconnect(BLEClient* pClient) {
    Serial.println("[BLE] Disconnected from RIGHT hand.");
    isBlinkingR = false;
  }
};

void rightNotificationCallback(BLERemoteCharacteristic* pCharacteristic, uint8_t* data, size_t length, bool isNotify) {
  String receivedData = String((char*)data).substring(0, length);
  if (ENABLE_DEBUG_PRINT_BLE){
    Serial.print("[RIGHT] Received: ");
    Serial.println(receivedData);
  }

  if (receivedData == "2") {
    blinkerControl(RIGHT, HIGH);
  } else if (receivedData == "1") {
    blinkerControl(RIGHT, LOW);
  }
}

// Connect to BLE server (generalized for left or right)
BLEClient* connectToServer(const char* address, BLEClientCallbacks* clientCallback, BLERemoteCharacteristic** remoteCharacteristic, void(*notificationCallback)(BLERemoteCharacteristic*, uint8_t*, size_t, bool)) {
  BLEClient* client = BLEDevice::createClient();
  client->setClientCallbacks(clientCallback);

  BLEAddress bleAddress(address);
  if (client->connect(bleAddress)) {
    Serial.print("[BLE] Connected to ");
    Serial.println(address);

    BLERemoteService* pRemoteService = client->getService(SERVICE_UUID);
    if (pRemoteService) {
      *remoteCharacteristic = pRemoteService->getCharacteristic(CHARACTERISTIC_UUID);
      if (*remoteCharacteristic && (*remoteCharacteristic)->canNotify()) {
        (*remoteCharacteristic)->registerForNotify(notificationCallback);
        Serial.println("[BLE] Notification enabled.");
      } else {
        Serial.println("[BLE] Characteristic not found or cannot notify.");
      }
    } else {
      Serial.println("[BLE] Service not found.");
    }
  } else {
    Serial.print("[BLE] Failed to connect to ");
    Serial.println(address);
  }
  return client;
}

// Function to get circular buffer values starting at buffer_index
void getCircularBufferValues(int32_t buffer[], int bufferIndex, int32_t output[]) {
    // Check if buffer is empty
    if (buffer == NULL) return;

    // Loop through the buffer and copy the values starting from bufferIndex
    for (int i = 0; i < BUFFER_SIZE; i++) {
        // Calculate the circular index using modulo operation
        output[i] = buffer[(bufferIndex + i) % BUFFER_SIZE];
    }
}

// Function that checks if all values in the buffer are below the threshold
bool are_all_below_threshold(float dy_buffer[], float threshold = 2.0) {
    for (int i = 0; i < BUFFER_SIZE; i++) {
        if (dy_buffer[i] >= threshold) {
            return false;  // Return false if any value exceeds or equals the threshold
        }
    }
    return true;  // All values are below the threshold
}

void setup() {
  Serial.begin(115200);

  // Initialisation BLE
  BLEDevice::init(BLE_DEVICE_NAME);
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Création d'une caractéristique pour les données
  pCharacteristic = pService->createCharacteristic(
                                          CHARACTERISTIC_UUID,
                                          BLECharacteristic::PROPERTY_READ |
                                          BLECharacteristic::PROPERTY_NOTIFY
                                        );
  pCharacteristic->addDescriptor(new BLE2902());

  // Démarrage du service BLE
  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->start();
  Serial.println("BLE prêt et en mode publicité !");

  // Initialisation du MPU6050
  // join I2C bus (I2Cdev library doesn't do this automatically)
  #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    Serial.println("I2CDEV_IMPLEMENTATION="+String(I2CDEV_IMPLEMENTATION));
    Wire.begin();
    Wire.setClock(400000); // 400kHz I2C clock. Comment this line if having compilation difficulties
  #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
    Fastwire::setup(400, true);
  #endif

  // initialize device
  Serial.println(F("Initializing I2C devices..."));
  mpu.initialize();
  pinMode(INTERRUPT_PIN, INPUT);
  if (mpu.testConnection()) {
    IMUConnected = true;
    Serial.println("MPU6050 connection successful");
  } else {
    IMUConnected = false;
    Serial.println("MPU6050 connection failed");
    // while (1);
  }
  Serial.println("MPU6050 configuration completed!");

  // load and configure the DMP
  Serial.println(F("Initializing DMP..."));
  devStatus = mpu.dmpInitialize();

  // supply your own gyro offsets here, scaled for min sensitivity
  mpu.setXGyroOffset(-6369);
  mpu.setYGyroOffset(2248);
  mpu.setZGyroOffset(3424);
  mpu.setXAccelOffset(-123);
  mpu.setYAccelOffset(-100);
  mpu.setZAccelOffset(46);
  // -6369.00000,	2248.00000,	3424.00000,	-123.00000,	-100.00000,	46.00000
  
  // make sure it worked (returns 0 if so)
  if (devStatus == 0) {
    // Calibration Time: generate offsets and calibrate our MPU6050
    mpu.CalibrateAccel(6);
    mpu.CalibrateGyro(6);
    Serial.println();
    mpu.PrintActiveOffsets();
    // turn on the DMP, now that it's ready
    Serial.println(F("Enabling DMP..."));
    mpu.setDMPEnabled(true);
    
    // enable Arduino interrupt detection
    Serial.print(F("Enabling interrupt detection (Arduino external interrupt "));
    Serial.print(digitalPinToInterrupt(INTERRUPT_PIN));
    Serial.println(F(")..."));
    attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), dmpDataReady, RISING);
    mpuIntStatus = mpu.getIntStatus();

    // set our DMP Ready flag so the main loop() function knows it's okay to use it
    Serial.println(F("DMP ready! Waiting for first interrupt..."));
    dmpReady = true;

    // get expected DMP packet size for later comparison
    packetSize = mpu.dmpGetFIFOPacketSize();
  } else {
    // ERROR!
    // 1 = initial memory load failed
    // 2 = DMP configuration updates failed
    // (if it's going to break, usually the code will be 1)
    Serial.print(F("DMP Initialization failed (code "));
    Serial.print(devStatus);
    Serial.println(F(")"));
  }

  // configure LED for output
  pinMode(LED_PIN, OUTPUT);

  // Initialisation des LEDs
  pinMode(LEFT_BLINKER_PIN, OUTPUT);
  pinMode(RIGHT_BLINKER_PIN, OUTPUT);
  digitalWrite(LEFT_BLINKER_PIN, LOW);
  digitalWrite(RIGHT_BLINKER_PIN, LOW);

  // Initialisation BLE
  BLEDevice::init(BLE_DEVICE_NAME);

  // Connexion au module gauche
  leftClient = connectToServer(LEFT_HAND_ADDRESS, new LeftHandCallback(), &leftRemoteCharacteristic, leftNotificationCallback);

  // Connexion au module droit
  rightClient = connectToServer(RIGHT_HAND_ADDRESS, new RightHandCallback(), &rightRemoteCharacteristic, rightNotificationCallback);
}   

void loop() {
  unsigned long currentMillis = millis();

  // Wait until connected to IMU
  if (IMUConnected) {
    // if programming failed, don't try to do anything
    if (!dmpReady) return;
    // read a packet from FIFO
    if (mpu.dmpGetCurrentFIFOPacket(fifoBuffer)) { // Get the Latest packet 
    
      #ifdef OUTPUT_READABLE_EULER
      // display Euler angles in degrees
      mpu.dmpGetQuaternion(&q, fifoBuffer);
      mpu.dmpGetEuler(euler, &q);

      if (isBlinkingR || isBlinkingL){
        if (isFirstBlink){
          startYaw = euler[0] * 180 / M_PI;
          isFirstBlink = false;
        }
        dy_buffer[bufferIndex] = abs(euler[0] * 180 / M_PI - prevYaw);
        prevYaw = euler[0] * 180 / M_PI;
        bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;
        if (BLEConnected){
          if(DEBUG){
            String data = String(startYaw) + "+-" + String(TURN_ANGLE_THRESHOLD) + "\t" + String(euler[0] * 180 / M_PI) + "\t"
                        + String(isTurning) + "\t" + String(isBlinkingL) + "\t" + String(isBlinkingR) + "\t" ;
            
            for (int i = 0; i < BUFFER_SIZE; i++){
              data += "," + String(dy_buffer[i]);
            }

            // Send data to the connected BLE client
            pCharacteristic->setValue(data.c_str());
            pCharacteristic->notify();
          }
        }
        if (!isTurning){
          float delta_yaw = (euler[0] * 180 / M_PI) - startYaw;
          if (isBlinkingR && delta_yaw >= TURN_ANGLE_THRESHOLD){
            isTurning = true;
          }else if (isBlinkingL && delta_yaw <= -TURN_ANGLE_THRESHOLD){
            isTurning = true;
          }
        }else{
          if (are_all_below_threshold(dy_buffer, 0.05)){
            isTurning = false;
            blinkerControl(LEFT, LOW);
            blinkerControl(RIGHT, LOW);
          }
        }
      }

      if (BLEConnected){
        if(ENABLE_DEBUG_PRINT_IMU_BLE){
          String data = String(euler[0] * 180 / M_PI) + "," 
                      + String(euler[1] * 180 / M_PI) + "," 
                      + String(euler[2] * 180 / M_PI);
          // Send data to the connected BLE client
          pCharacteristic->setValue(data.c_str());
          pCharacteristic->notify();
        }
      }

      if (ENABLE_DEBUG_PRINT_IMU) {
        Serial.print("euler\t");
        Serial.print(euler[0] * 180 / M_PI);
        Serial.print("\t");
        Serial.print(euler[1] * 180 / M_PI);
        Serial.print("\t");
        Serial.println(euler[2] * 180 / M_PI);
      }
      #endif

      #ifdef OUTPUT_READABLE_YAWPITCHROLL
      // display Euler angles in degrees
      mpu.dmpGetQuaternion(&q, fifoBuffer);
      mpu.dmpGetGravity(&gravity, &q);
      mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);

      if (isBlinkingR || isBlinkingL){
        float dy = (ypr[0] * 180 / M_PI) - prevYaw;
        dy_buffer[bufferIndex] = dy;
        bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;

        if (!isTurning){
          if (dy > 3.0 && isBlinkingR){
            isTurning = true;
          }else if (dy < -3.0 && isBlinkingL){
            isTurning = true;
          }
        }else{
          if (are_all_below_threshold(dy_buffer, 1.0)){
            isTurning = false;
            blinkerControl(LEFT, LOW);
            blinkerControl(RIGHT, LOW);
          }
        }
        if(DEBUG){
          String data = String(dy_buffer[0]) + "," + String(dy_buffer[1]) + "," + String(dy_buffer[2]) + "," + String(dy_buffer[3]) + "," + String(dy_buffer[4]) + "," + String(isTurning) + "," + String(dy) + "," + String(isBlinkingL) + "," + String(isBlinkingR) + "," + String(ypr[0] * 180 / M_PI);
          // Send data to the connected BLE client
          pCharacteristic->setValue(data.c_str());
          pCharacteristic->notify();
        }
      }

      if (BLEConnected){
        if(ENABLE_DEBUG_PRINT_IMU_BLE){
          String data = String(ypr[0] * 180 / M_PI) + "," + String(ypr[1] * 180 / M_PI) + "," + String(ypr[2] * 180 / M_PI);
          // Send data to the connected BLE client
          pCharacteristic->setValue(data.c_str());
          pCharacteristic->notify();
        }
      }

      if (ENABLE_DEBUG_PRINT_IMU) {
        Serial.print("ypr\t");
        Serial.print(ypr[0] * 180 / M_PI);
        Serial.print("\t");
        Serial.print(ypr[1] * 180 / M_PI);
        Serial.print("\t");
        Serial.print(ypr[2] * 180 / M_PI);

        mpu.dmpGetAccel(&aa, fifoBuffer);
        Serial.print("\tRaw Accl XYZ\t");
        Serial.print(aa.x);
        Serial.print("\t");
        Serial.print(aa.y);
        Serial.print("\t");
        Serial.print(aa.z);
        mpu.dmpGetGyro(&gy, fifoBuffer);
        Serial.print("\tRaw Gyro XYZ\t");
        Serial.print(gy.x);
        Serial.print("\t");
        Serial.print(gy.y);
        Serial.print("\t");
        Serial.print(gy.z);
        Serial.println();
      }
      prevYaw = ypr[0] * 180 / M_PI;
      #endif
      
      // blink LED to indicate activity
      blinkState = !blinkState;
      digitalWrite(LED_PIN, blinkState);
    }
  }

  // Gestion du clignotement des LEDs
  if (isBlinkingL) {
    digitalWrite(LEFT_BLINKER_PIN, (currentMillis % BLINKER_PERIOD) < BLINKER_PERIOD / 2);
  } else {
    digitalWrite(LEFT_BLINKER_PIN, LOW);
  }

  if (isBlinkingR) {
    digitalWrite(RIGHT_BLINKER_PIN, (currentMillis % BLINKER_PERIOD) < BLINKER_PERIOD / 2);
  } else {
    digitalWrite(RIGHT_BLINKER_PIN, LOW);
  }

  // Reconnexion si nécessaire
  if (leftClient && !leftClient->isConnected()) {
    leftClient = connectToServer(LEFT_HAND_ADDRESS, new LeftHandCallback(), &leftRemoteCharacteristic, leftNotificationCallback);
  }
  if (rightClient && !rightClient->isConnected()) {
    rightClient = connectToServer(RIGHT_HAND_ADDRESS, new RightHandCallback(), &rightRemoteCharacteristic, rightNotificationCallback);
  }
}

// Example functions to control blinkers
void blinkerControl(int side, int newState){
  long int currentMillis = millis();
  long int delta_time = currentMillis - prev_millis_blink_command;
  if (side == LEFT)
  {
    if (delta_time > 500)
    {
      isBlinkingR = LOW;
    }
    isBlinkingL = newState;
  } 
  else if (side == RIGHT)
  {
    if (delta_time > 500)
    {
      isBlinkingL = LOW;
    }
    isBlinkingR = newState;
  }
  prev_millis_blink_command = currentMillis;
  isFirstBlink = true;
}
