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
#define ACCEL_RANGE 2   // Options: 2, 4, 8, 16 (en g)
#define GYRO_RANGE 250  // Options: 250, 500, 1000, 2000 (en °/s)
#define IMU_ODR 52      // Desired Output Data Rate in Hz

// Pin pour la lecture de la tension de la batterie
const int batteryPin = 34;
float batteryVoltage = 0.0;

// Pin pour le buzzer
const int buzzerPin = 17;

// Variables pour l'échelle
float LSB_TO_G;
float LSB_TO_DPS;

// Timing variables for MPU6050 data reading
unsigned long lastReadTime = 0;
const unsigned long readIntervalIMU = 1000 / ODR_IMU;  // Interval in ms (e.g., ~19ms for 52Hz)

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

  Serial.println("MPU6050 configuration completed!");

  // Initialisation BLE
  BLEDevice::init(BLE_DEVICE_NAME);
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Création d'une caractéristique pour les données
  BLECharacteristic *pCharacteristic = pService->createCharacteristic(
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
}

void loop() {
  unsigned long currentMillis = millis();

  // Read data from MPU6050 at the specified ODR
  if (currentMillis - lastReadTime >= readIntervalIMU) {
    lastReadTime = currentMillis;
    int16_t ax, ay, az, gx, gy, gz;

    // Read raw data from MPU6050
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Convert accelerometer data to mg (millig)
    int32_t ax_mg = (int32_t)(ax * 1000 / LSB_TO_G);
    int32_t ay_mg = (int32_t)(ay * 1000 / LSB_TO_G);
    int32_t az_mg = (int32_t)(az * 1000 / LSB_TO_G);

    // Convert gyroscope data to mdps (millidegrees per second)
    int32_t gx_mdps = (int32_t)(gx * 1000 / LSB_TO_DPS);
    int32_t gy_mdps = (int32_t)(gy * 1000 / LSB_TO_DPS);
    int32_t gz_mdps = (int32_t)(gz * 1000 / LSB_TO_DPS);

    // Battery voltage reading
    int adcValue = analogRead(batteryPin);
    batteryVoltage = adcValue * (3.52 / 0.89 / 4095.0); // Conversion to voltage (up to ~3.6V for ADC_11db)

    if (batteryVoltage < 3.5) {
      digitalWrite(buzzerPin, HIGH);
    } else {
      digitalWrite(buzzerPin, LOW);
    }

    // Construct the data string with integer values
    String data = String(micros()) + "," +
                  String(ax_mg) + "," +
                  String(ay_mg) + "," +
                  String(az_mg) + "," +
                  String(gx_mdps) + "," +
                  String(gy_mdps) + "," +
                  String(gz_mdps);

    Serial.println(data); // Output to serial monitor

    // Send the data via BLE
    pCharacteristic->setValue(data.c_str());
    pCharacteristic->notify(); // Notify connected clients
  }
}
