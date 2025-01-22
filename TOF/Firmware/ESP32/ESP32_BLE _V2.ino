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
 */

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
  // Répartition des zones et points
  const int left_zones_1pt[] = {7, 15, 23, 31, 39, 47};  // Zones gauche, 1 point
  const int left_zones_2pt[] = {6, 14, 22, 30, 38, 46};  // Zones gauche, 2 points
  const int right_zones_1pt[] = {0, 8, 16, 24, 32, 40};  // Zones droite, 1 point
  const int right_zones_2pt[] = {1, 9, 17, 25, 33, 41};  // Zones droite, 2 points

  const int left_1pt_count = sizeof(left_zones_1pt) / sizeof(left_zones_1pt[0]);
  const int left_2pt_count = sizeof(left_zones_2pt) / sizeof(left_zones_2pt[0]);
  const int right_1pt_count = sizeof(right_zones_1pt) / sizeof(right_zones_1pt[0]);
  const int right_2pt_count = sizeof(right_zones_2pt) / sizeof(right_zones_2pt[0]);

  int left_score = 0, right_score = 0;

  // Fonction pour ajouter des points si conditions respectées
  auto add_points = [&](const int zones[], int count, int points, int &score) {
    for (int i = 0; i < count; i++) {
      int zone = zones[i];
      if (Result->nb_target_detected[zone] > 0) {
        int distance = Result->distance_mm[VL53L8CX_NB_TARGET_PER_ZONE * zone];
        if (distance >= 400 && distance <= 1200) {  // Conditions de distance
          score += points;
        }
      }
    }
  };

  // Calcul des scores gauche et droite
  add_points(left_zones_1pt, left_1pt_count, 10, left_score);
  add_points(left_zones_2pt, left_2pt_count, 20, left_score);
  add_points(right_zones_1pt, right_1pt_count, 10, right_score);
  add_points(right_zones_2pt, right_2pt_count, 20, right_score);

  // Allumer/éteindre les LEDs selon les scores
  digitalWrite(LED_LEFT_PIN, (left_score > 60) ? HIGH : LOW);
  digitalWrite(LED_RIGHT_PIN, (right_score > 60) ? HIGH : LOW);

  // Affichage pour le débogage
  SerialPort.print("Score Gauche: ");
  SerialPort.println(left_score);
  SerialPort.print("Score Droite: ");
  SerialPort.println(right_score);
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