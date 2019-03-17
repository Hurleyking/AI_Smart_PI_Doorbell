# AI Smart Doorbell

[![N|Solid](https://i.ibb.co/5GPzx4h/Webp-net-resizeimage.png)]()

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)]()

Bell was created with the intention of using minimal local physical resources in this way every notification process is by MQTT

Diagram:
[![N|Solid](https://i.ibb.co/3TPp3xc/Untitled-Diagram-7-1.jpg)]()

# Features
  - Face Recgonition via azure
  - Notification by MQTT
  - Action Callback by  MQTT
    - Live 
    - Snapshot
    - Playsound 
    - Add new person to Face Recognition
   - Call and receive Voipcall 

### Hardware

In my case I used raspberry pi zero, but could use any other raspberry or orangepi PC (in the case of orangepi pc do not need to buy microphone and usb sound)

| Hardware | Notes |
| ------ | ------ |
| Raspberry pi zero  | You can by another version   |
| Power suply | Power supply you need to provide 5v for raspberry and 5v for speaker (in my case I put 12v converter with two outputs of 5v) |
| usb sound card (speakers and microphone) |  Before buying any of them check if is compatible with raspberry, in the aliexpress there is a usb sound card 7.1 for 1 euro |
| touch button | It is advisable touch button becouse of rain, this being under the acrylic avoiding water leakage. |
| Raspcam Infrared | There are several camera to raspberry with various angles, should buy what suits for your front door. |
|Another machine | You need another machine on your internal network with mqtt server, http server with HTTP Basic authentication configure, node-red or homeassistant to send notifications wherever you want |

### Installation

Some python requirements or libraries may be missing if you find any steps failed please tell me.

#### First (External HTTP server)

Copy the index.html file to the http folder of the external server and in turn fill with your data. Note: The server must have HTTP Basic authentication

#### Second (Configure Raspberry)

Install all dependencies

```sh
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python-gpiozero
sudo apt-get install python-pip
sudo apt-get install sox
sudo apt-get install sox libsox-fmt-all
sudo apt-get install ffmpeg
sudo apt-get install subversion
sudo apt-get install -y gpac
sudo apt-get install linphone
sudo apt-get install lighttpd
```


Run the following command
```sh
sudo chmod 777 /var/www/html
```
Edit file lighttpd.conf and change server.stat-cache-engine  to "disable"
```sh
sudo nano /etc/lighttpd/ lighttpd.conf 
```

Edit file "/etc/network/interfaces" to ensure wifi connection start in boot.
 Something like this:

```
auto lo
iface lo inet loopback
iface eth0 inet dhcp
auto wlan0
allow-hotplug wlan0
 
iface wlan0 inet static
    address 192.168.1.120
    netmask 255.255.255.0
    network 192.168.1.254
    broadcast 192.168.1.255
    gateway 192.168.1.254
    wpa-ssid "SIID_WIFI"
    wpa-psk "Password_wifi"
```
Run Github command in the user pi folder (/ home/pi) 
```sh
git clone https://github.com/Hurleyking/AI_Smart_PI_Doorbell
```

To ensure WiFi is always on top in case of failure, copy the following file to the directory indicated below:
```sh
cp checkwifi.sh  /usr/local/bin/checkwifi.sh
```

Check alsa if this is using correct device (in my case usb1)
```sh
alsamixer
```
Edit the fixed variables in the files auto_healing.py and doorbell_pi_start.py:
```
http_server = 'http_server_adress_and_port_file'
http_password = 'username'
http_user = 'password'
```



`Notice:` To use face recognition it is necessary create groupId new, for do that you need discomment the line 348 from  file doorbell_pi_start.py "#person_group_create_v2()" to "person_group_create_v2()"  after run script you need comment again,  otherwise try to always create new groupid whenever script starts


Add follow lines in crontab(sudo crontab -e)
```
*/5 * * * * /usr/bin/sudo -H /usr/local/bin/checkwifi.sh >> /dev/null 2>&1
*/10 * * * * python /home/pi/doorbell_pi/auto_healing.py
```

Ready to use. 


### MQTT instructions:

To get notification, subscribe to **doorbell/ring**

To get status from doorbell,  subscribe to **Doorbell/Temperature** and **Doorbell/rssi** .

Publish **doorbell/live**:

>Payload with the String **live_30sec** - Action:  Record 30 seconds of live broadcast and save mp4 to folder /var/www/html/ live_30sec.mp4

>Payload with the String **live_30sec_alexa**  - Action:  Record 30 seconds of live broadcast and save mp4 to folder /var/www/html/ live_30sec.mp4  (for alexa node-red)

>Payload with the String **photo**  - Action: takes a photo realtime and saves it in the folder/var/www/html/last_ring.jpg 

>Payload with the String **{"new_person":"True","name":"marco"}**   - Action: 
add new person for facial recognition based on the last photo taken (/var/www/html/last_ring.jpg)

### Todos

 - Add created groupid automatic
 - tell me more function


**Free Software, Hell Yeah!**
