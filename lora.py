#!/usr/bin/env python3
"""RAK811 OTAA demo.

Ajout de la lecture du BME680
Ajout de la pression et de l'humidité
Ajout d'une entrée numérique
Ajout détecteur de mouvement
Remise à zéro du détecteur de mouvement qui se déclenche à chaque paquet

Minimalistic OTAA demo
Copyright 2019 Philippe Vanhaesendonck
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
SPDX-License-Identifier: Apache-2.0
"""
from random import randint
from sys import exit
from time import sleep
import bme680
import datetime
from rak811 import Mode, Rak811
from gpiozero import LED, MotionSensor

#Valeur du curseur au démarrage
curseur = 1010
analog_in = curseur
print ("curseur au départ = ", curseur)

# Configurer LED et détecteur PIR
led = LED(12)
pir = MotionSensor(24)

# Mise à zéro du détecteur de mouvement
detect=0

# Fonction exécutée lors d'une détection de mouvement
def mouvement():
    global detect
    print("Mouvement détecté")
    detect = 1

lora = Rak811()

# Most of the setup should happen only once...
print('Configuration de la liaison')
# Crée le capteur en testant les deux adresses possibles 0x76 et 0x77
try:
    capteur = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except IOError:
    capteur = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

# Initialisations LoRa
lora.hard_reset()
lora.mode = Mode.LoRaWan
lora.band = 'EU868'
lora.set_config(app_eui='70B3D57ED002926F',
                app_key='05C01640904CDF836FA29B8EA632F47F')

print('Connexion au réseau')

i=0
while i<5:
    led.on()
    sleep(0.01)
    led.off()
    sleep(0.3)
    i+=1

lora.join_otaa()
# Note that DR is different from SF and depends on the region
# See: https://docs.exploratory.engineering/lora/dr_sf/
# Set Data Rate to 5 which is SF7/125kHz for EU868
lora.dr = 5

# Réaction à une détection de présence
# Appel de la fonction mouvement qui passe detect à 1
pir.when_motion = mouvement

print("Envoi des paquets toutes les minutes - CTRL + C interromp la boucle")
print("Il est possible d'envoyer des downlinks depuis la console TTN")
#try:
while True:
        # Si les données du capteur sont lues
        if capteur.get_sensor_data():
            # Afficher la température
            Temp = int(10*round(capteur.data.temperature, 1))
#            print(f'Température : {capteur.data.temperature:.1f} °C')
            print('Température : ', Temp/10)
            # Afficher la pression
            Pression = int(10*round(capteur.data.pressure, 1))
            print('Pression : ', Pression/10)
#            print(f'Pression : {capteur.data.pressure:.1f} hPa')
            # Afficher l'humidité relative
            HR = int(2*capteur.data.humidity)
#            print(f'Humidité : {capteur.data.humidity:.1f} %HR')
            print('Humidité : ', HR/2)
            print("==============")

        print('Envoi du paquet de données')
        date=datetime.datetime.now()
        print(date)
        print("==============")

# Valeur du détecteur de mouvement
# Mise à 1 si mouvement détecté
        if detect == 0:
            detect_value = 0
            print("detect_value mise à 0")
        else :
            detect_value = 1
            print("detect_value mise à 1")

# Envoyer les infos dans un paquet LoRa
        print ("valeur curseur avant le send :", curseur)
#        lora.send(bytes.fromhex('0167{:04x}0273{:04x}0368{:02x}0401000503{:04x}0600{:02x}'.format(Temp, Pression, HR, curseur, detect_value)))
        print('0167{:04x}0273{:04x}0368{:02x}0401000503{:04x}0600{:02x}0702{:04x}'.format(Temp, Pression, HR, curseur, detect_value, analog_in))

        lora.send(bytes.fromhex('0167{:04x}0273{:04x}0368{:02x}0401000503{:04x}0600{:02x}0702{:04x}'.format(Temp, Pression, HR, curseur, detect_value, analog_in)))

#        while lora.nb_downlinks:
#            data_recues = lora.get_downlink()['data'].hex()
#            print('Paquet reçu : ', data_recues )
            # Si on reçoit un zéro sur canal 4 Entrée digitale
#            if  (data_recues == "040000ff") or (data_recues == "040064ff") :
#                # Reset du détecteur de présence
#                print ("Remise du détecteur de présence à 0")
#                lora.send(bytes.fromhex('060000'))

# Attendre une minute (pour les tests 10 secondes)
        i=0
        while i<60 :
            led.on()
            sleep(0.01)
            led.off()
            sleep(1)
            i += 1
            print("Boucle ",i)
            while lora.nb_downlinks:
                data_recues = lora.get_downlink()['data'].hex()
                print('Paquet reçu = ', data_recues )
                # Si on reçoit un reset sur canal 4 Entrée digitale
                if  (data_recues == "040000ff") or (data_recues == "040064ff") :
                    # Reset du détecteur de présence
                    print ("Remise du détecteur de présence à 0")
                    detect = 0
                    lora.send(bytes.fromhex('060000'))
                else :
                    # Si on reçoit une valeur depuis le curseur 05
                    print("deux premiers chiffres : ",data_recues[0:2])
                    if data_recues[0:2]=="05" :
                        # La valeur reçue est en hexa
                        chaine_curseur = data_recues[2:6]
                        # On la convertit en entier
                        curseur =int(chaine_curseur,16)
                        print("Température réglée sur :  ", curseur/100)
                        analog_in = curseur

#except:  # noqa: E722
#    pass

print('Cleaning up')
lora.close()
exit(0)
