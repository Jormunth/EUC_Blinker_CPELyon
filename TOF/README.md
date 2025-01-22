# ToF Solution  
## System Description  
The ToF approach uses the `SATEL-VL53L8CX` multi-zone distance sensor to detect hand and arm gestures. This solution provides gesture mapping through an 8x8 or 4x4 zone grid.  

## Features and Progress  
- **Visualization and Data Archiving**  
  - Connects via BLE and serial interfaces to archive gesture data in JSON or CSV formats.  
- **Neural Network Integration**  
  - Train a neural network to classify gestures (e.g., Left, Right, None).  



SDA PB7
SCL PB6

USART RX PA10

USART TX PA9

Pour lire en série UArt depuis un terminal Linux

stty -F /dev/ttyACM0 115200 
cat /dev/ttyACM0

Logs : 
06/01
Test communication serial entre F401RE et PC (linux)
Code test communication :
```c
/* Lire l'état actuel du bouton */
uint8_t button_current_state = HAL_GPIO_ReadPin(B1_GPIO_Port, B1_Pin);

/* Si le bouton est pressé (passage de HIGH à LOW) */
if (button_previous_state == GPIO_PIN_SET && button_current_state == GPIO_PIN_RESET)
{
/* Envoyer un message via UART */
char message[] = "Bouton appuyé, envoi du signal UART\n";
HAL_UART_Transmit(&huart2, (uint8_t *)message, sizeof(message) - 1, HAL_MAX_DELAY);
}

/* Mettre à jour l'état précédent du bouton */
button_previous_state = button_current_state;
HAL_Delay(50); // Attendre 50 ms pour éviter les rebonds
```

Instalation des drivers du TOF VL53L8 (dossier dans docs projet)
Ajouter les .h et .c de VL53L8CX_ULD_API et les platform.h/platform.c

07/01

Connecter le TOF au PC :     
- EXT_5V <---> 5V
- EXT 1V8 NC
- EXT_3.3V NC
- EXT IOVDD NC
- PWR_EN <—--> D11
- SCL <—--> D15
- SDA <—--> D14
- EXT MISO NC
- I2C_RST (NCS) NC
- EXT LPn <—--> A3
- EXT SPI_I2C <--—> GND
- GPIO1 <---> A2
- GPIO2 NC
- GND <—--> GND

stty -F /dev/ttyACM0 460800 
cat /dev/ttyACM0

  - Baud Rate: 460800
  - Data Bits: 8
  - Parity: None
  - Stop Bits: 1

Connéxion au TOF visualisation des valeurs.
Valeur capteur TOF : capteur_valor.png

création du tof GUI (Graphique user interface) en connectique serial (vidéo capteur_tof)

debut du portage en connectique BLE

08/01

Essais connectique uart entre stm32 et ESP32 marche pas 
début du portage VL53L5CX avec ESP32
Utilisation d'un boust pour passer du 3.3V de la ESP32 au 5V du TOF
Essai avec la stm32 le tof ne fonctionne pas en 3,3V
Branchement et code : https://github.com/stm32duino/VL53L8CX/blob/main/examples/VL53L8CX_HelloWorld_I2C/VL53L8CX_HelloWorld_I2C.ino

09/01

TOF fonctionel avec la TTGO T dispay

10/01 
connection TOF BLE fonctionel 
GUI fonctionnel fichuier csv fonctionel

13/01

GUI Couple
attention ajout d'un time delta (d'une heure dans get_video-timestamp) car probleme d'enregistrement et décalage d'un heure

14/01
Modification de GUI couple pour pouvoir labélisé les données et créer un nouveau fichier csv

16/01
BLE_CSV car TOF BLE probléme non résolvable.

17/01 
création du support pour les cartest de test
acquisition de données

18/01 
Modification de GUI COuple pour support windows et labellisation des données

TODO : 

 - labelissation
 - créer un fichier csv à partir des autres
 - Entrainement
 - Implémentation
 - modélisation 3D pour le support


Source : https://github.com/nkolban/ESP32_BLE_Arduino

