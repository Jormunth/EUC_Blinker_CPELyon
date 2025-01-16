#include <Wire.h>
#include <MPU6050.h>
#include <BLEDevice.h>
#include <BLEClient.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// Création de l'objet MPU6050
MPU6050 mpu;

// UUIDs pour le service et la caractéristique BLE
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define BLE_DEVICE_NAME     "ESP32_EUC_Centre"

// Pins pour les LEDs de clignotement
#define LEFT_BLINKER_PIN 18
#define RIGHT_BLINKER_PIN 19

// Variables pour le clignotement
bool isBlinkingL = false;
bool isBlinkingR = false;
const unsigned long BLINKER_FREQUENCY = 1;  // Hz
const unsigned long BLINKER_PERIOD = 1000 / BLINKER_FREQUENCY;  // ms

// BLE client variables
BLEClient* pClient = nullptr;
BLERemoteCharacteristic* pRemoteCharacteristic = nullptr;

// Callback to handle notifications
class MyClientCallback : public BLEClientCallbacks {
  void onConnect(BLEClient* pClient) {
    Serial.println("[BLE] Connected to server.");
  }

  void onDisconnect(BLEClient* pClient) {
    Serial.println("[BLE] Disconnected from server.");
    isBlinkingL = false;
    isBlinkingR = false;
  }
};

// Handle notifications from the "hand module"
void notificationCallback(BLERemoteCharacteristic* pCharacteristic, uint8_t* data, size_t length, bool isNotify) {
  String receivedData = String((char*)data).substring(0, length);
  Serial.print("[BLE] Received: ");
  Serial.println(receivedData);

  if (receivedData == "2") {
    activateRightBlinker();
  } else if (receivedData == "1") {
    deactivateRightBlinker();
  }
}

// Connect to the "hand module" BLE server
void connectToServer(const char* address) {
  pClient = BLEDevice::createClient();
  pClient->setClientCallbacks(new MyClientCallback());
  
  // Convert the address string to BLEAddress
  BLEAddress bleAddress(address);

  if (pClient->connect(bleAddress)) {
    Serial.println("[BLE] Connected to BLE server.");

    BLERemoteService* pRemoteService = pClient->getService(SERVICE_UUID);
    if (pRemoteService) {
      pRemoteCharacteristic = pRemoteService->getCharacteristic(CHARACTERISTIC_UUID);
      if (pRemoteCharacteristic) {
        if (pRemoteCharacteristic->canNotify()) {
          pRemoteCharacteristic->registerForNotify(notificationCallback);
          Serial.println("[BLE] Notification enabled.");
        }
      } else {
        Serial.println("[BLE] Characteristic not found.");
      }
    } else {
      Serial.println("[BLE] Service not found.");
    }
  } else {
    Serial.println("[BLE] Failed to connect to server.");
  }
}

void setup() {
  Serial.begin(115200);

  // Initialisation des LEDs
  pinMode(LEFT_BLINKER_PIN, OUTPUT);
  pinMode(RIGHT_BLINKER_PIN, OUTPUT);
  digitalWrite(LEFT_BLINKER_PIN, LOW);
  digitalWrite(RIGHT_BLINKER_PIN, LOW);

  // Initialisation BLE
  BLEDevice::init(BLE_DEVICE_NAME);
  connectToServer("F8:B3:B7:22:2E:3A");  // Replace with your "hand module" address
}

void loop() {
  unsigned long currentMillis = millis();

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

  // Reconnect if disconnected
  if (pClient && !pClient->isConnected()) {
    connectToServer("F8:B3:B7:22:2E:3A");
  }
}

// Example functions to control blinkers
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
