#include <Wire.h>
#include <MPU6050.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// Création de l'objet MPU6050
MPU6050 mpu;

// UUIDs pour le service et la caractéristique BLE
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define BLE_DEVICE_NAME "ESP32_EUC_Left_Hand"

// Configuration de l'accéléromètre et du gyroscope
#define ACCEL_RANGE 4   // Options: 2, 4, 8, 16 (en g)
#define GYRO_RANGE 500  // Options: 250, 500, 1000, 2000 (en °/s)
#define ODR_IMU 52      // Options: 12.5, 26, 52, 104, 208, 416, 833 (en Hz)

// Pin pour la lecture de la tension de la batterie
const int batteryPin = 34;
float batteryVoltage = 0.0;

// Pin pour le buzzer
const int buzzerPin = 17;

// Variables pour l'échelle
float LSB_TO_G;
float LSB_TO_DPS;
float LSB_TO_MDPS;
float LSB_TO_MG;

// Timing variables for MPU6050 data reading
unsigned long lastReadTime = 0;
const unsigned long readIntervalIMU = 1000 / ODR_IMU;  // Interval in ms (e.g., ~19ms for 52Hz)
unsigned long lastBatteryReadTime = 0;
const unsigned long batteryReadInterval = 3000;  // Battery check every 3 seconds

// Declare the BLE characteristic globally
BLECharacteristic *pCharacteristic;
BLEServer *pServer;
bool deviceConnected = false;
bool buzzerState = false;  // Keeps track of the buzzer state

// To calculate millis from micros only once
unsigned long startMicros;

// BLE Server callback to track connection status
class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    Serial.println("Client connected!");
    buzzerState = true;
    digitalWrite(buzzerPin, HIGH);  // Buzzer feedback on connection
    delay(100);
    digitalWrite(buzzerPin, LOW);
  }

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    Serial.println("Client disconnected!");
  }
};

void setup() {
  Serial.begin(115200);

  // Initialisation du MPU6050
  Wire.begin();
  mpu.initialize();
  if (mpu.testConnection()) {
    Serial.println("MPU6050 connection successful");
  } else {
    Serial.println("MPU6050 connection failed");
    while (1);
  }

  // Définir la plage de l'accéléromètre et du gyroscope
  switch (ACCEL_RANGE) {
    case 2:
      mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);
      LSB_TO_G = 16384.0;
      break;
    case 4:
      mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);
      LSB_TO_G = 8192.0;
      break;
    case 8:
      mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_8);
      LSB_TO_G = 4096.0;
      break;
    case 16:
      mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_16);
      LSB_TO_G = 2048.0;
      break;
    default:
      Serial.println("Invalid ACCEL_RANGE. Defaulting to 2g.");
      mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);
      LSB_TO_G = 16384.0;
      break;
  }
  LSB_TO_MG = 1000.0 / LSB_TO_G; // Convert to milligrams

  switch (GYRO_RANGE) {
    case 250:
      mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_250);
      LSB_TO_DPS = 131.0;
      break;
    case 500:
      mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);
      LSB_TO_DPS = 65.5;
      break;
    case 1000:
      mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_1000);
      LSB_TO_DPS = 32.8;
      break;
    case 2000:
      mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_2000);
      LSB_TO_DPS = 16.4;
      break;
    default:
      Serial.println("Invalid GYRO_RANGE. Defaulting to 250dps.");
      mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_250);
      LSB_TO_DPS = 131.0;
      break;
  }
  LSB_TO_MDPS = 1000.0 / LSB_TO_DPS; // Convert to millidegrees per second

  Serial.println("MPU6050 configuration completed!");

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

  // Configuration du pin ADC
  analogReadResolution(12); // Résolution par défaut de l'ESP32 (12 bits)
  analogSetAttenuation(ADC_11db); // Échelle complète pour des tensions allant jusqu'à ~3.6V

  // Configuration du pin buzzer
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);

  // Signal setup fini
  digitalWrite(buzzerPin, HIGH);
  delay(100);
  digitalWrite(buzzerPin, LOW);

  // Store the initial micros() value
  startMicros = micros();
}

void loop() {
  unsigned long currentMicros = micros() - startMicros;
  unsigned long currentMillis = currentMicros / 1000;  // Convert micros to millis

  // Wait until connected before fetching IMU data
  if (deviceConnected) {
    // Fetch IMU data at the specified interval
    if (currentMillis - lastReadTime >= readIntervalIMU) {
      lastReadTime = currentMillis;
      int16_t ax, ay, az, gx, gy, gz;

      // Read raw data from MPU6050
      mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

      // Convert accelerometer data to mg (milligrams)
      int32_t ax_mg = (int32_t)(ax * LSB_TO_MG);
      int32_t ay_mg = (int32_t)(ay * LSB_TO_MG);
      int32_t az_mg = (int32_t)(az * LSB_TO_MG);

      // Convert gyroscope data to mdps (millidegrees per second)
      int32_t gx_mdps = (int32_t)(gx * LSB_TO_MDPS);
      int32_t gy_mdps = (int32_t)(gy * LSB_TO_MDPS);
      int32_t gz_mdps = (int32_t)(gz * LSB_TO_MDPS);

      // Construct the data string with integer values
      String data = String(currentMicros) + "," +
                    String(ax_mg) + "," + String(ay_mg) + "," + String(az_mg) + "," +
                    String(gx_mdps) + "," + String(gy_mdps) + "," + String(gz_mdps);

      // Send data to the connected BLE client
      pCharacteristic->setValue(data.c_str());
      pCharacteristic->notify();
    }

    // Read the battery voltage every 3 seconds
    if (currentMillis - lastBatteryReadTime >= batteryReadInterval) {
      lastBatteryReadTime = currentMillis;
      batteryVoltage = (analogRead(batteryPin) * 3.3) / 4095.0 * 2; // Read and scale voltage
      if (batteryVoltage < 3.5){
        digitalWrite(buzzerPin, HIGH);
      }
    }
  }
}
