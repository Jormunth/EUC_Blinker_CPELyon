#include <Wire.h>
#include <MPU6050.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <math.h>

// Création de l'objet MPU6050
MPU6050 mpu;

#define ENABLE_IMU 1
#define ENABLE_BATTERY_MONITORING 1
#define ENABLE_MOTION_RECOGNITION 1
#define DEBUG_SEND_IMU_DATA 0

// UUIDs pour le service et la caractéristique BLE
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define BLE_DEVICE_NAME "ESP32_EUC_Right_Hand"

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

// Define buffers and constants
#define BUFFER_SIZE 52
int32_t acc_x_buffer[BUFFER_SIZE];
int32_t acc_y_buffer[BUFFER_SIZE];
int32_t acc_z_buffer[BUFFER_SIZE];
int32_t gyro_x_buffer[BUFFER_SIZE];
int32_t gyro_y_buffer[BUFFER_SIZE];
int32_t gyro_z_buffer[BUFFER_SIZE];
unsigned int bufferIndex = 0;

int32_t prev_classification = 0;

// Classification thresholds
#define ACC_STD_THRESHOLD 100.0
#define GYRO_STD_THRESHOLD 1000.0

// Declare the BLE characteristic globally
BLECharacteristic *pCharacteristic;
BLEServer *pServer;
bool BLEConnected = false;

bool IMUConnected = false;
bool buzzerState = false;  // Keeps track of the buzzer state

// To calculate millis from micros only once
unsigned long startMicros;

// BLE Server callback to track connection status
// BLE Server callback to track connection status
class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    BLEConnected = true;
    Serial.println("[BLE] Client connecté.");
    digitalWrite(buzzerPin, HIGH);
    delay(50);
    digitalWrite(buzzerPin, LOW);
  }

  void onDisconnect(BLEServer* pServer) {
    BLEConnected = false;
    Serial.println("[BLE] Client déconnecté.");
    pServer->getAdvertising()->start();  // Redémarrer la publicité
    Serial.println("[BLE] Publicité BLE redémarrée.");
    for (int8_t i = 0; i < 2; i++){
      digitalWrite(buzzerPin, HIGH);
      delay(50);
      digitalWrite(buzzerPin, LOW);
      delay(50);
    }
  }
};

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

void calculateNorm(const int32_t *xBuffer, const int32_t *yBuffer, const int32_t *zBuffer, float *normBuffer) {
  for (int i = 0; i < BUFFER_SIZE; i++) {
    normBuffer[i] = sqrt(pow(xBuffer[i], 2) + pow(yBuffer[i], 2) + pow(zBuffer[i], 2));
  }
}

float calculateStd(float data[], int size) {
  if (size == 0) return 0.0;

  // Step 1: Calculate the mean
  float mean = 0.0;
  for (int i = 0; i < size; i++) {
    mean += data[i];
  }
  mean /= size;

  // Step 2: Calculate the variance
  float variance = 0.0;
  for (int i = 0; i < size; i++) {
    variance += pow(data[i] - mean, 2);
  }
  variance /= size;

  // Step 3: Return the square root of the variance (standard deviation)
  return sqrt(variance);
}

float calculateMean(int32_t data[], int size) {
  if (size == 0) return 0.0;

  // Step 1: Calculate the mean
  float mean = 0.0;
  for (int i = 0; i < size; i++) {
    mean += data[i];
  }
  mean /= size;

  return mean;
}

float calculatePTP(int32_t data[], int size) {
  if (size == 0) return 0.0;

  // Initialize variables for the minimum and maximum values
  int32_t minVal = data[0];
  int32_t maxVal = data[0];

  // Iterate through the array to find the min and max values
  for (int i = 1; i < size; i++) {
    if (data[i] < minVal) {
      minVal = data[i];
    }
    if (data[i] > maxVal) {
      maxVal = data[i];
    }
  }

  // Return the peak-to-peak value
  return maxVal - minVal;
}

// Function to apply low-pass filter with forward and backward passes
void applyLowPassFilter(float data[], float filteredData[], float alpha) {
    if (data == NULL || filteredData == NULL || BUFFER_SIZE == 0) return;

    // Temporary array to hold the filtered values
    float tempData[BUFFER_SIZE];

    // Forward pass: Apply the filter
    tempData[0] = data[0];  // Initialize with the first value
    for (int i = 1; i < BUFFER_SIZE; ++i) {
        tempData[i] = alpha * data[i] + (1 - alpha) * tempData[i - 1];
    }

    // Backward pass: Apply the filter in reverse direction
    filteredData[BUFFER_SIZE - 1] = tempData[BUFFER_SIZE - 1];  // Initialize with the last filtered value
    for (int i = BUFFER_SIZE - 2; i >= 0; --i) {
        filteredData[i] = alpha * tempData[i] + (1 - alpha) * filteredData[i + 1];
    }
}

// Function to calculate alpha based on cutoff frequency and sampling frequency
float calculateAlpha(float fs, float cutoff) {
    float tau = 1.0 / (2.0 * 3.14159265358979 * cutoff);  // Time constant
    float dt = 1.0 / fs;  // Sampling period
    return dt / (tau + dt);  // Alpha calculation
}

int countPeaks(float data[], float threshold = 1.5) {
  // Derivative array to store the changes between consecutive values
  float derivative[BUFFER_SIZE];
  
  // Calculate the derivative of the acceleration data
  derivative[0] = 0;  // First derivative value is set to 0
  for (int i = 1; i < BUFFER_SIZE; i++) {
    derivative[i] = data[i] - data[i - 1];
  }
  
  // Initialize the peak count
  int peakCount = 0;
  
  // Iterate over the data and check for peaks
  for (int i = 1; i < BUFFER_SIZE - 1; i++) {
    // Check if the derivative changes from positive to negative and the value is above the threshold
    if (derivative[i] > 0 && derivative[i + 1] < 0 && data[i] > threshold) {
      peakCount++;
    }
  }
  
  // Return the number of detected peaks
  return peakCount;
}

// Function to get circular values for accelerometer and gyroscope data
void getAllCircularBufferValues(
    int32_t acc_x_buffer[], int32_t acc_y_buffer[], int32_t acc_z_buffer[],
    int32_t gyro_x_buffer[], int32_t gyro_y_buffer[], int32_t gyro_z_buffer[],
    int bufferIndex,
    int32_t ax[], int32_t ay[], int32_t az[],
    int32_t gx[], int32_t gy[], int32_t gz[]) {

    // Get circular buffer values for accelerometer and gyroscope
    getCircularBufferValues(acc_x_buffer, bufferIndex, ax);
    getCircularBufferValues(acc_y_buffer, bufferIndex, ay);
    getCircularBufferValues(acc_z_buffer, bufferIndex, az);
    getCircularBufferValues(gyro_x_buffer, bufferIndex, gx);
    getCircularBufferValues(gyro_y_buffer, bufferIndex, gy);
    getCircularBufferValues(gyro_z_buffer, bufferIndex, gz);
}

int8_t classify() {
  int32_t ax[BUFFER_SIZE], ay[BUFFER_SIZE], az[BUFFER_SIZE], gx[BUFFER_SIZE], gy[BUFFER_SIZE], gz[BUFFER_SIZE];
  getAllCircularBufferValues(acc_x_buffer, acc_y_buffer, acc_z_buffer, gyro_x_buffer, gyro_y_buffer, gyro_z_buffer, bufferIndex, ax, ay, az, gx, gy, gz);

  // Calculate norms
  float accNorm[BUFFER_SIZE];
  float gyroNorm[BUFFER_SIZE];
  calculateNorm(ax, ay, az, accNorm);
  calculateNorm(gx, gy, gz, gyroNorm);

  float accStdDev = calculateStd(accNorm, BUFFER_SIZE);

  // Decision tree logic
  if (accStdDev < ACC_STD_THRESHOLD) {  
    float gyroStdDev = calculateStd(gyroNorm, BUFFER_SIZE);
    if (gyroStdDev < GYRO_STD_THRESHOLD){
      return 0;
    }
    return 3;
  }

  // Apply low-pass filter to the norm
  float acc_norm_filtered[BUFFER_SIZE];
  float fs = 52;  // Sampling frequency (Hz)
  float cutoff = 10;  // Low-pass filter cutoff frequency (Hz)
  float alpha = calculateAlpha(fs, cutoff); // Calculate alpha based on fs and cutoff
  applyLowPassFilter(accNorm, acc_norm_filtered, alpha);

  int accPeaks = countPeaks(accNorm, 3000.0); // Adjust thresholds as needed

  float acc_xz_mean = calculateMean(ax, BUFFER_SIZE) + calculateMean(az, BUFFER_SIZE);
  float acc_y_mean_abs = abs(calculateMean(ay, BUFFER_SIZE));

  if (accPeaks == 0) {
    return 3;
  } else if (accPeaks == 1) {
    if (acc_xz_mean < acc_y_mean_abs){
      if (calculatePTP(ax, BUFFER_SIZE) > calculatePTP(ay, BUFFER_SIZE)){
        return 1;
      }
    }
  } else if (accPeaks >= 2){
    if (acc_xz_mean < acc_y_mean_abs){
      if (calculatePTP(ay, BUFFER_SIZE) > calculatePTP(ax, BUFFER_SIZE)){
        return 2;
      }
    }
  }

  return 3;
}

void setMpuFS(){
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
}

void setup() {
  Serial.begin(115200);

  // Initialisation du MPU6050
  Wire.begin();
  mpu.initialize();
  if (mpu.testConnection()) {
    IMUConnected = true;
    Serial.println("MPU6050 connection successful");
  } else {
    IMUConnected = false;
    Serial.println("MPU6050 connection failed");
    // while (1);
  }
  setMpuFS();
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
  delay(300);
  digitalWrite(buzzerPin, LOW);

  // Store the initial micros() value
  startMicros = micros();
}

void loop() {
  unsigned long currentMicros = micros() - startMicros;
  unsigned long currentMillis = currentMicros / 1000;  // Convert micros to millis
  // Serial.println("[LOOP] BLE="+String(BLEConnected)+" IMU="+String(IMUConnected));
  // Wait until connected before fetching IMU data
  if (BLEConnected) {
    // Wait until connected to IMU
    if (IMUConnected) {
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

        acc_x_buffer[bufferIndex] = ax_mg;
        acc_y_buffer[bufferIndex] = ay_mg;
        acc_z_buffer[bufferIndex] = az_mg;
        gyro_x_buffer[bufferIndex] = gx_mdps;
        gyro_y_buffer[bufferIndex] = gy_mdps;
        gyro_z_buffer[bufferIndex] = gz_mdps;
        bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;

        if (ENABLE_MOTION_RECOGNITION){
          if (bufferIndex % int(BUFFER_SIZE/10)-1 == 0) {
            // Perform classification
            int32_t classification = classify();
            Serial.println("Classification: " + String(classification));

            // Send classification result over BLE
            if(prev_classification != classification){
              if (BLEConnected){
                pCharacteristic->setValue(String(classification).c_str());
                pCharacteristic->notify();
              }
            }
            prev_classification = classification;
          }
        }

        if (DEBUG_SEND_IMU_DATA){
          // Construct the data string with integer values
          String data = String(currentMicros) + "," +
                        String(ax_mg) + "," + String(ay_mg) + "," + String(az_mg) + "," +
                        String(gx_mdps) + "," + String(gy_mdps) + "," + String(gz_mdps);

          if (BLEConnected){
            // Send data to the connected BLE client
            pCharacteristic->setValue(data.c_str());
            pCharacteristic->notify();
          }
        }
      }

    }
  }
  if (ENABLE_BATTERY_MONITORING){
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
