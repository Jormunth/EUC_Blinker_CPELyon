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

BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic = NULL;

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
  BLEDevice::init("ESP32_EUC_Right_Hand");
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
}

void loop() {
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

  // Construction d'une chaîne de données
  String data = String(ax_g, 4) + "," +
                String(ay_g, 4) + "," +
                String(az_g, 4) + "," +
                String(gx_deg, 4) + "," +
                String(gy_deg, 4) + "," +
                String(gz_deg, 4) ;

  // Envoi des données via BLE
  pCharacteristic->setValue(data.c_str());
  pCharacteristic->notify(); // Notification pour les clients connectés

  Serial.println(data); // Affichage sur le moniteur série

  delay(500); // Attente d'une seconde entre les envois
}
