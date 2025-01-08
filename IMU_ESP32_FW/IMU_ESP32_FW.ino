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

// Pins pour les LEDs de clignotement
#define LEFT_BLINKER_PIN 18
#define RIGHT_BLINKER_PIN 19

// Variables pour le clignotement
bool isBlinkingL = false;
bool isBlinkingR = false;

// Timing variables for MPU6050 data reading
unsigned long lastReadTime = 0;
const unsigned long readInterval = 20;  // 20ms

BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic = NULL;

void setup() {
  Serial.begin(115200);

  // Initialisation des LEDs
  pinMode(LEFT_BLINKER_PIN, OUTPUT);
  pinMode(RIGHT_BLINKER_PIN, OUTPUT);
  digitalWrite(LEFT_BLINKER_PIN, LOW);  // LED éteinte au départ
  digitalWrite(RIGHT_BLINKER_PIN, LOW); // LED éteinte au départ

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
  unsigned long currentMillis = millis();

  // Lire les données du MPU6050 toutes les 20ms
  if (currentMillis - lastReadTime >= readInterval) {
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

    if (gy_deg > 200){
      activateRightBlinker();
      deactivateLeftBlinker();
    }else if(gy_deg < -200){
      activateLeftBlinker();
      deactivateRightBlinker();
    }
  }

  // Gestion du clignotement des LEDs
  if (isBlinkingL) {
    digitalWrite(LEFT_BLINKER_PIN, (millis() % 1000) < 500);  // Clignote toutes les 500ms
  } else {
    digitalWrite(LEFT_BLINKER_PIN, LOW);  // LED éteinte
  }

  if (isBlinkingR) {
    digitalWrite(RIGHT_BLINKER_PIN, (millis() % 1000) < 500);  // Clignote toutes les 500ms
  } else {
    digitalWrite(RIGHT_BLINKER_PIN, LOW);  // LED éteinte
  }

  delay(100); // Petite pause pour éviter de saturer le processeur
}

// Exemple de fonctions pour activer les clignotants (peut être appelé depuis une autre partie du programme)
void activateLeftBlinker() {
  isBlinkingL = true;
}

void deactivateLeftBlinker() {
  isBlinkingL = false;
}

void activateRightBlinker() {
  isBlinkingR = true;
}

void deactivateRightBlinker() {
  isBlinkingR = false;
}
