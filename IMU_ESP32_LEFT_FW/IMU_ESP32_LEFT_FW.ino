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
#define DEVICE_DATA_NAME = "left"

// Timing variables for MPU6050 data reading
unsigned long lastReadTime = 0;
const unsigned long ODR_IMU = 52;  // Hz
const unsigned long readIntervalIMU = 1000 / ODR_IMU;  // ms

BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic = NULL;

// Pin pour la lecture de la tension de la batterie
const int batteryPin = 34;
float batteryVoltage = 0.0;

// Pin pour le buzzer
const int buzzerPin = 17;

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

  // Initialisation BLE
  BLEDevice::init(BLE_DEVICE_NAME);
  pServer = BLEDevice::createServer();
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
}

void loop() {
  unsigned long currentMillis = millis();

  // Lire les données du MPU6050 toutes les 20ms
  if (currentMillis - lastReadTime >= readIntervalIMU) {
    lastReadTime = currentMillis;

    int16_t ax, ay, az, gx, gy, gz;

    // Lecture des données du MPU6050
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

    // Conversion des données
    float ax_g = ax / 16.384;
    float ay_g = ay / 16.384;
    float az_g = az / 16.384;

    float gx_deg = gx / 131.0;
    float gy_deg = gy / 131.0;
    float gz_deg = gz / 131.0;

    // Lecture de la tension de la batterie
    int adcValue = analogRead(batteryPin);
    batteryVoltage = adcValue * (3.52 / 0.89 / 4095.0); // Conversion en tension (3.6V max pour ADC_11db)

    if (batteryVoltage < 3.5){
      digitalWrite(buzzerPin, HIGH);
    }else{
      digitalWrite(buzzerPin, LOW);
    }

    // Construction d'une chaîne de données
    String data = "left," +
                  String(ax_g, 4) + "," +
                  String(ay_g, 4) + "," +
                  String(az_g, 4) + "," +
                  String(gx_deg, 4) + "," +
                  String(gy_deg, 4) + "," +
                  String(gz_deg, 4) + "," +
                  String(batteryVoltage, 2);

    // Envoi des données via BLE
    pCharacteristic->setValue(data.c_str());
    pCharacteristic->notify(); // Notification pour les clients connectés

    Serial.println(data); // Affichage sur le moniteur série
  }
}
