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

Connéxion au TOF viluasilation des valeurs.
Valeur capteur TOF : capteur_valor.png

création du tof GUI (Graphique user interface) en connectique serial (vidéo capteur_tof)

debut du portage en connectique BLE



TODO : 

- TOF_ble_gui
- calibrer et detecter un semblant de gauche/droite
- LED
- Intégration avec led 
- adaptation de l'alimentation d'entré
- modélisation 3D pour le support
