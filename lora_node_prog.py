#!/usr/bin/env python3
"""RAK811 OTAA demo.

Ajout de la lecture du BME680
Ajout de la pression et de l'humidité

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

from rak811 import Mode, Rak811
# from ttn_secrets import APP_EUI, APP_KEY

lora = Rak811()

# Most of the setup should happen only once...
print('Setup')
# Crée le capteur en testant les deux adresses possibles 0x76 et 0x77
try:
    capteur = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except IOError:
    capteur = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

# Initialisations LoRa
lora.hard_reset()
lora.mode = Mode.LoRaWan
lora.band = 'EU868'
lora.set_config(app_eui='70xxxxxxxxxxxxxF',
                app_key='05C0xxxxxxxxxxxxxxxxxxxxxxxxxx47F')

print('Joining')
lora.join_otaa()
# Note that DR is different from SF and depends on the region
# See: https://docs.exploratory.engineering/lora/dr_sf/
# Set Data Rate to 5 which is SF7/125kHz for EU868
lora.dr = 5

print('Sending packets every minute - Interrupt to cancel loop')
print('You can send downlinks from the TTN console')
try:
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
        # Cayenne lpp random value as analog
#        lora.send(bytes.fromhex('0167{:04x}'.format(randint(0, 0x7F))))
        lora.send(bytes.fromhex('0167{:04x}0273{:04x}0368{:02x}'.format(Temp, Pression, HR)))

        while lora.nb_downlinks:
            print('Received', lora.get_downlink()['data'].hex())

        sleep(60)
except:  # noqa: E722
    pass

print('Cleaning up')
lora.close()
exit(0)
