#!/usr/bin/env python3
#Made by Hurleyking
#https://github.com/Hurleyking/AI_Smart_PI_Doorbell

import paho.mqtt.client as mqttClient
from subprocess import check_output
import subprocess
from re import findall
import requests
import json
import psutil
import os
import argparse

#Variables
http_server = '192.168.1.84:8008'
http_password = 'hurley'
http_user = 'hurley'

def get_credential():
        response = requests.get('http://'+http_server, auth=(http_user, http_password))
        credential = str(response.text.decode('utf-8'))
        credential = json.loads(credential)
        global subscription_key
        subscription_key = credential
        return subscription_key



def get_temp():
        temp = check_output(["vcgencmd","measure_temp"]).decode("UTF-8")
        return(findall("\d+\.\d+",temp)[0])

def send_mqtt_message(topic,message):
        broker_address= subscription_key['ip_server_mqtt']
        port = 1883
        user = subscription_key['User_mqtt']
        password =  subscription_key['Password_mqtt']
        client = mqttClient.Client("Python_auto_healing")               #create new instance
        client.username_pw_set(user, password=password)    #set username and password
        #client.on_connect= on_connect                      #attach function to callback
        client.connect(broker_address, port=port,keepalive=30)          #connect to broker
        msg_info = client.publish(topic,message,qos=0)
        if msg_info.is_published() == False:
                        msg_info.wait_for_publish()
        client.disconnect()

def  state_service():
        state_service = 0
        PROCNAME = "doorbell_pi_start.py"
        for proc in psutil.process_iter():
                Pid = str(proc.cmdline())
                if Pid.find(PROCNAME) > 0:
                        print(proc)
                        state_service = 1
        if state_service <> 1:
                print "Subir servico"
                subprocess.Popen(['nohup','python','/home/pi/doorbell_pi/doorbell_pi_start.py'],
                 stdout=open('/dev/null', 'w'),
                 stderr=open('logfile.log', 'a'),
                 preexec_fn=os.setpgrp
                 )
                #subprocess.call(["nohup", "python doorbell_pi_start.py"])

def  state_rssi_wifi():
        parser = argparse.ArgumentParser(description='Display WLAN signal strength.')
        parser.add_argument(dest='interface', nargs='?', default='wlan0', help='wlan interface (default: wlan0)')
        args = parser.parse_args()
        cmd = subprocess.Popen('/sbin/iwconfig %s' % args.interface, shell=True, stdout=subprocess.PIPE)
        dbm = 0
        for line in cmd.stdout:
                if 'Link Quality' in line:
                        dbm = line.split('=')
                        dbm = int(dbm[2].replace(' dBm',''))
                elif 'Not-Associated' in line:
                        print 'No signal'
        return dbm

get_credential()
temp = get_temp()
print(temp)
send_mqtt_message("Doorbell/Temperature", temp)
rssi = state_rssi_wifi()
print(rssi)
send_mqtt_message("Doorbell/rssi", rssi)
state_service()