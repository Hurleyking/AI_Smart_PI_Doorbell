#Made by Hurleyking
#https://github.com/Hurleyking/AI_Smart_PI_Doorbell

import requests
import uuid
#import cv2
from gtts import gTTS
import os
import subprocess
from subprocess import call
import json
import time
from gpiozero import Button
from time import sleep
from datetime import datetime
import paho.mqtt.client as mqttClient
from picamera import PiCamera
from signal import pause
from threading import Thread
import uuid
import base64


#Global Variables
global sucess_press_button_time
global http_server
global http_password
global http_user
global client_listen
global play_sound_type
global personGroupId
global personId
global faces_list
global face_identify
global faces_on_photo

#Variables
http_server = '192.168.1.84:8008'
http_password = 'hurley'
http_user = 'hurley'

#Function  enable/disable
Call_voip_if_ring = 'False'
face_recognition_state = 'True'


#Fix Variables
sucess_press_button_time =  datetime.now()

def get_credential_and_settings():
        response = requests.get('http://'+http_server, auth=(http_user, http_password))
        credential_and_settings = str(response.text.decode('utf-8'))
        credential_and_settings = json.loads(credential_and_settings)
        global subscription_key
        subscription_key = credential_and_settings
        print('get_credential_and_settings Finish.')
        return subscription_key

get_credential_and_settings()
assert subscription_key

def detect():
        global faces_on_photo
        img_file = '/var/www/html/last_ring.jpg'
        with open(img_file, 'rb') as f:
                binary = f.read()
        f.close()
        face_api_url = subscription_key['API_Endpoint_azure']+'/detect'
        headers = {'Ocp-Apim-Subscription-Key': subscription_key['API_key_azure'], "Content-Type" :'application/octet-stream'}
        params = {
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'false',
        'returnFaceAttributes': 'age,gender,headPose,smile,facialHair,glasses,' +
        'emotion,hair,makeup,occlusion,accessories,blur,exposure,noise'
        }
        response = requests.post(face_api_url, params=params, headers=headers, data=binary)
        faces_on_photo = response.json()
        return faces_on_photo


def person_group_create_v2():
        global personGroupId
        name = 'DOORBELL'
        personGroupId = str(uuid.uuid4())
        endpoint = subscription_key['API_Endpoint_azure']+'/persongroups/{}'.format(personGroupId)
        headers = {"Ocp-Apim-Subscription-Key": subscription_key['API_key_azure']}
        json = { 'name': name }
        r = requests.put(endpoint, json=json,headers=headers)
        if r.status_code != 200:
                print('error:' + r.text)
        else:
                print('Person group created with ID: '+personGroupId)

def get_persongroup_list():
        global personGroupId
        endpoint = subscription_key['API_Endpoint_azure']+'/persongroups'
        headers = {"Ocp-Apim-Subscription-Key": subscription_key['API_key_azure']}
        r=requests.get(endpoint,headers=headers)
        if r.status_code != 200:
                print('error:' + r.text)
        else:
                personGroupId =r.json()
                personGroupId = str(personGroupId[0]['personGroupId'])
                return personGroupId

def person_create(personName):
        global personGroupId
        global personId
        endpoint = subscription_key['API_Endpoint_azure']+'/persongroups/{}'.format(personGroupId)+'/persons'
        headers = {"Ocp-Apim-Subscription-Key": subscription_key['API_key_azure']}
        json = {
        'name': personName
        }
        r = requests.post(endpoint, json=json,headers=headers)
        if r.status_code != 200:
                print('error:' + r.text)
        else:
                res=r.json()
                personId = res['personId']
                print('Person created: '+ personName+'with ID: '+personId)
                return personId


def person_addface(path_face):
        global personGroupId
        global personId
        endpoint = subscription_key['API_Endpoint_azure']+'/persongroups/{}/persons/{}/persistedFaces'.format(personGroupId, personId)
        headers = {"Ocp-Apim-Subscription-Key": subscription_key['API_key_azure'], "Content-Type": "application/octet-stream"}
        img_file = path_face
        with open(img_file, 'rb') as f:
                binaryImage = f.read()
        f.close()        
        r = requests.post(endpoint, headers=headers,data=binaryImage)
        if r.status_code != 200:
                print('error:' + r.text)
        else:
                res=r.json()
                if res.get('persistedFaceId'):
                        persistedFaceId = res['persistedFaceId']
                        print('A Face Added to the person with ID: '+personId)
                        print(persistedFaceId)
                        return persistedFaceId
                else:
                        print('no persistedfaceid found')


def identify():
        global personGroupId
        global face_identify
        global faces_on_photo
        face_api_url = subscription_key['API_Endpoint_azure']+'/identify'
        headers = {'Ocp-Apim-Subscription-Key': subscription_key['API_key_azure']}
        try:
                params = {
                "personGroupId": personGroupId,
                "faceIds": [faces_on_photo[0]['faceId']],
                "maxNumOfCandidatesReturned": 1,
                "confidenceThreshold": 0.5
                }
                response = requests.post(face_api_url, params=params, headers=headers,json=params)
                if response.status_code == 200:
                        check_faces = response.json()
                        for check_face in  check_faces:
                                for know_face in faces_list:
                                        if know_face['personId'] == check_face['candidates'][0]['personId']:
                                                face_identify = know_face['name'] 
                                                print face_identify
                else:
                        face_identify = 'Stranger'
        except:
                face_identify = 'Stranger'
        return face_identify



def faces_list():
        global personGroupId
        global faces_list
        endpoint = subscription_key['API_Endpoint_azure']+'/persongroups/'+personGroupId+'/persons'
        headers = {"Ocp-Apim-Subscription-Key": subscription_key['API_key_azure']}
        r=requests.get(endpoint,headers=headers)
        if r.status_code != 200:
                print('error:' + r.text)
        else:
                faces_list=r.json()
                return faces_list

def persongroup_train():
        global personGroupId
        endpoint = subscription_key['API_Endpoint_azure']+'/persongroups/{}'.format(personGroupId)+'/train'
        headers = {"Ocp-Apim-Subscription-Key": subscription_key['API_key_azure']}
        r=requests.post(endpoint,headers=headers)
        if r.status_code != 202:
                print('error:' + r.text)
        else:
                print('Training is succesfully completed')


def TEXT_TO_SPEECH(mytext):
        global play_sound_type
        mytext = 'Ola, estou contatar meus Proprietarios, por favor aguarde.'
        language = 'PT'
        myobj = gTTS(text=mytext, lang=language, slow=False)
        myobj.save("generic.mp3")
        play_sound_type = 'generic'

def voip_call():
        print "call"
        #subprocess.call(["linphonecsh", "init"])
        subprocess.call(["linphonecsh", "generic", "call sip:"+subscription_key['voip_call_number']])

def button_ring():
        global sucess_press_button_time
        global play_sound_type
        global face_identify
        last_press_button_time = datetime.now()
        diff_time_press_button = last_press_button_time - sucess_press_button_time
        if diff_time_press_button.seconds > 30:
                sucess_press_button_time = datetime.now()
                take_picture('last_ring')
                play_sound_type = 'welcome'
                if subscription_key['face_recognition_state'] == 'True':
                        detect()
                        identify()
                        send_mqtt_message('doorbell/ring','{"ring": "True","face_recognition_state": "True","Name": "'+face_identify+'"}')
                else:
                        send_mqtt_message('doorbell/ring','{"ring": "True","face_recognition_state": "False"}')
                print("ring ring ring")

def send_mqtt_message(topic,message):
        broker_address= subscription_key['ip_server_mqtt']
        port = 1883
        user = subscription_key['User_mqtt']
        password =  subscription_key['Password_mqtt']
        client = mqttClient.Client("Python_ringbell_send")              
        client.username_pw_set(user, password=password)
        client.connect(broker_address, port=port)
        msg_info = client.publish(topic,message,qos=0)
        if msg_info.is_published() == False:
                msg_info.wait_for_publish()
        client.disconnect()

def take_picture(name):
        camera = PiCamera()
        camera.resolution = (1024, 768)
        sleep(2)
        camera.capture('/var/www/html/'+name+'.jpg')
        camera.close()

            

def record_video(name,resolution):
        output_video_rasp = '/var/www/html/'+name+'.h264'
        camera = PiCamera()
        camera.resolution = (640, 480)
        sleep(2)
        camera.start_recording(output_video_rasp)
        sleep(15)
        camera.stop_recording()
        camera.close()
        output_video_mp4  = '/var/www/html/'+name+'.mp4'
        retcode = call(["MP4Box", "-add", output_video_rasp,"-new" ,output_video_mp4,"-out",output_video_mp4])
        sleep(1)

def listen_mqtt_message():
        global client_listen
        broker_address= subscription_key['ip_server_mqtt']
        port = 1883
        user = subscription_key['User_mqtt']
        password =  subscription_key['Password_mqtt']
        client_listen = mqttClient.Client("Python_ringbell_loop")
        client_listen.username_pw_set(user, password=password)
        client_listen.connect(broker_address, port=port,keepalive=30)
        client_listen.subscribe("doorbell/live")
        client_listen.on_message = on_message
        client_listen.loop_forever()

def on_message(client_listen, userdata, msg):
        if msg.payload.decode() == "live_30sec":
                print("Yes! Live 30sec")
                record_video('live_30sec','480, 320')
                send_mqtt_message('doorbell/live','live_30sec_ready')
        if msg.payload.decode() == "live_30sec_alexa":
                print("Yes! Live 30sec from alexa")
                record_video('live_30sec','480, 320')
                send_mqtt_message('doorbell/live','live_30sec_alexa_ready')
        if msg.payload.decode() == "live_stream":
                print("Yes! Live STream")
        if msg.payload.decode() == "photo":
                print("Yes! Open Photo")
                take_picture('last_ring')
                send_mqtt_message('doorbell/live','photo_ready')
                print("Done! Open Photo")
        if msg.payload.decode() == "open_gate":
                print("Yes! Open Gate")
        if '"new_person":"True"' in msg.payload.decode() :
                print("Creating new person")
                new_person = json.loads(msg.payload.decode())
                auto_provision_new_faces(new_person[name])
                send_mqtt_message('doorbell/live','Add new person with sucess')



def wait_press():
        button_start = Button(26)
        button_start.when_pressed = button_ring
        pause()

def play_sounds():
        global play_sound_type
        while True:
                if play_sound_type ==  'welcome':
                        os.system("play welcome.mp3")
                        if subscription_key['Call_voip_if_ring'] == 'True':
                                voip_call()
                        else:
                                play_sound_type = 'ring'
                        sleep(0.1)
                if play_sound_type ==  'ring':
                        play_sound_type = 'Bye'
                        os.system("play ring.wav")
                        sleep(2)
                if play_sound_type == 'Bye':
                        play_sound_type = 'none'
                        os.system("play bye.mp3")
                if play_sound_type == 'start':
                        play_sound_type = 'none'
                        os.system("play start.mp3")
                        print('start sound ok')
                if play_sound_type == 'generic':
                        play_sound_type = 'none'
                        os.system("play generic.mp3")
                        sleep(0.2)

def auto_provision_new_faces(name):
        global personGroupId
        get_persongroup_list()
        detect()
        person_create(name)
        person_addface('/var/www/html/last_ring.jpg')
        persongroup_train()
        identify()
        print('Finish')


if subscription_key['face_recognition_state'] == 'True':
        #discomment function person_group_create_v2 to create the first groupid (after run script comment again please)
        #person_group_create_v2() 
        get_persongroup_list()
        faces_list()
        #detect()
        #identify()


#LOOP

play_sound_type = 'start'
print('Start')
if __name__ == '__main__':
        Thread(target = wait_press).start()
        Thread(target = listen_mqtt_message).start()
        Thread(target = play_sounds).start()

#LOOP END
