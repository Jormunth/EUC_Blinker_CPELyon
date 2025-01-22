/*
 * To use these examples you need to connect the VL53L8CX satellite sensor directly to the Nucleo board with wires as explained below:
 * pin 1 (SPI_I2C_N) of the VL53L8CX satellite connected to pin GND of the Nucleo board
 * pin 2 (LPn) of the VL53L8CX satellite connected to pin 2 of the Nucleo board
 * pin 3 (NCS) not connected
 * pin 4 (MISO) not connected
 * pin 5 (MOSI_SDA) of the VL53L8CX satellite connected to pin 21 (SDA) of the Nucleo board
 * pin 6 (MCLK_SCL) of the VL53L8CX satellite connected to pin 22 (SCL) of the Nucleo board
 * pin 7 (PWREN) of the VL53L8CX satellite connected to pin 12 of the Nucleo board
 * pin 8 (I0VDD) of the VL53L8CX satellite not connected
 * pin 9 (3V3) of the VL53L8CX satellite not connected
 * pin 10 (1V8) of the VL53L8CX satellite not connected
 * pin 11 (5V) of the VL53L8CX satellite connected to 5V of the Nucleo board
 * GPIO1 of VL53L8CX satellite connected to A2 pin of the Nucleo board (not used)
 * GND of the VL53L8CX satellite connected to GND of the Nucleo board
 *
 * V1 : allume les led gauche droite en fonction des moyennes des valeurs du capteurs
 * 
 * /

/* Includes ------------------------------------------------------------------*/

#include <vl53l8cx.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>



#define SDA_PIN 21
#define SCL_PIN 22
#define DEV_I2C Wire 
#define LED_LEFT_PIN 13   // Pin pour la LED des zones de gauche
#define LED_RIGHT_PIN 15  // Pin pour la LED des zones de droite

#define SerialPort Serial

#define LPN_PIN 2
#define PWREN_PIN 12

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"  // UUID du service
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"  // UUID de la caractéristique


void print_result(VL53L8CX_ResultsData *Result);
void clear_screen(void);
void handle_cmd(uint8_t cmd);
void display_commands_banner(void);

// Components.
VL53L8CX sensor_vl53l8cx_top(&DEV_I2C, LPN_PIN);

bool EnableAmbient = false;
bool EnableSignal = false;
uint8_t res = VL53L8CX_RESOLUTION_8X8;
char report[256];
uint8_t status;
BLECharacteristic *pCharacteristic;  // Déclaration globale


/* Setup ---------------------------------------------------------------------*/
void setup()
{
  // Initialisation BLE
  BLEDevice::init("ESP32_EUC_VL53L8CX_Sensor");  // Nom de l'appareil BLE
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ |
    BLECharacteristic::PROPERTY_NOTIFY
  );
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->start();
  SerialPort.println("BLE prêt et en mode publicité !");


  // Enable PWREN pin if present
  if (PWREN_PIN >= 0) {
    pinMode(PWREN_PIN, OUTPUT);
    digitalWrite(PWREN_PIN, HIGH);
    delay(10);
  }

  // Initialize serial for output.
  SerialPort.begin(115200);

  DEV_I2C.begin(SDA_PIN, SCL_PIN);

  pinMode(LED_LEFT_PIN, OUTPUT);
  pinMode(LED_RIGHT_PIN, OUTPUT);

  // Éteindre les LEDs au démarrage
  digitalWrite(LED_LEFT_PIN, LOW);
  digitalWrite(LED_RIGHT_PIN, LOW);



  // Configure VL53L8CX component.
  sensor_vl53l8cx_top.begin();
  status = sensor_vl53l8cx_top.init();
  status = sensor_vl53l8cx_top.set_resolution(res);


  // Start Measurements
  status = sensor_vl53l8cx_top.start_ranging();
}

void loop()
{
  VL53L8CX_ResultsData Results;
  uint8_t NewDataReady = 0;

  do {
    status = sensor_vl53l8cx_top.check_data_ready(&NewDataReady);
  } while (!NewDataReady);

  if ((!status) && (NewDataReady != 0)) {
    status = sensor_vl53l8cx_top.get_ranging_data(&Results);
    print_result(&Results);
  }

  if (Serial.available() > 0) {
    handle_cmd(Serial.read());
  }
}

void print_result(VL53L8CX_ResultsData *Result)
{
  int8_t j, l;
  uint8_t zones_per_line = (res == 16) ? 4 : 8;
  String data = "";
  
  // Variables pour les moyennes des distances
  int left_sum = 0, right_sum = 0, left_count = 0, right_count = 0;

  for (j = 0; j < res; j += zones_per_line) {
    for (l = 0; l < VL53L8CX_NB_TARGET_PER_ZONE; l++) {
      for (int i = 0; i < zones_per_line; i++) {
        if ((j + i) < res && Result->nb_target_detected[j + i] > 0) {
          int distance = Result->distance_mm[(VL53L8CX_NB_TARGET_PER_ZONE * (j + i)) + l];
          
          // Ajouter la distance et le statut au message
          data += String(distance) + ":" + 
                  String(Result->target_status[(VL53L8CX_NB_TARGET_PER_ZONE * (j + i)) + l]) + ",";
          
          // Calcul des moyennes des distances pour gauche et droite
          if ((j + i) % zones_per_line < zones_per_line / 2) { // Zones de gauche
            left_sum += distance;
            left_count++;
          } else { // Zones de droite
            right_sum += distance;
            right_count++;
          }
        } else {
          // Si aucune cible détectée, ajoutez "X:X"
          data += "X:X,";
        }
      }
    }
  }

  // Calcul des moyennes
  int left_avg = (left_count > 0) ? (left_sum / left_count) : 0;
  int right_avg = (right_count > 0) ? (right_sum / right_count) : 0;

  // Allumer/éteindre les LEDs en fonction des moyennes
  if (left_avg > 0 && left_avg < 1200) {
    digitalWrite(LED_LEFT_PIN, HIGH);
  } else {
    digitalWrite(LED_LEFT_PIN, LOW);
  }

  if (right_avg > 0 && right_avg < 1200) {
    digitalWrite(LED_RIGHT_PIN, HIGH);
  } else {
    digitalWrite(LED_RIGHT_PIN, LOW);
  }

  // Envoi des données BLE
  pCharacteristic->setValue(data.c_str());  // Met à jour la valeur de la caractéristique
  pCharacteristic->notify();  // Envoie la notification aux clients connectés

  // Affichage des données sur le port série pour le débogage
  SerialPort.println(data);
}


void toggle_resolution(void)
{
  status = sensor_vl53l8cx_top.stop_ranging();

  switch (res) {
    case VL53L8CX_RESOLUTION_4X4:
      res = VL53L8CX_RESOLUTION_8X8;
      break;

    case VL53L8CX_RESOLUTION_8X8:
      res = VL53L8CX_RESOLUTION_4X4;
      break;

    default:
      break;
  }
  status = sensor_vl53l8cx_top.set_resolution(res);
  status = sensor_vl53l8cx_top.start_ranging();
}

void toggle_signal_and_ambient(void)
{
  EnableAmbient = (EnableAmbient) ? false : true;
  EnableSignal = (EnableSignal) ? false : true;
}

void clear_screen(void)
{
  snprintf(report, sizeof(report), "%c[2J", 27); /* 27 is ESC command */
  SerialPort.print(report);
}

void display_commands_banner(void)
{
  snprintf(report, sizeof(report), "%c[2H", 27); /* 27 is ESC command */
  SerialPort.print(report);

  Serial.print("53L8A1 Simple Ranging demo application\n");
  Serial.print("--------------------------------------\n\n");

  Serial.print("Use the following keys to control application\n");
  Serial.print(" 'r' : change resolution\n");
  Serial.print(" 's' : enable signal and ambient\n");
  Serial.print(" 'c' : clear screen\n");
  Serial.print("\n");
}

void handle_cmd(uint8_t cmd)
{
  switch (cmd) {
    case 'r':
      toggle_resolution();
      clear_screen();
      break;

    case 's':
      toggle_signal_and_ambient();
      clear_screen();
      break;

    case 'c':
      clear_screen();
      break;

    default:
      break;
  }
}