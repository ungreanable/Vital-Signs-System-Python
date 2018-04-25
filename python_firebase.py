#! /usr/bin/python

import pyrebase
import threading
import sys
import paho.mqtt.client as mqtt
import time
from random import randrange, uniform

config = {
  "apiKey": "AIzaSyChanfamKiT0sFGlFPgUlLwTQZQnm4sT4I",
  "authDomain": "vital-sign-system.firebaseapp.com",
  "databaseURL": "https://vital-sign-system.firebaseio.com",
  "storageBucket": ""
}

def on_connect(client, userdeta, flags, rc):
    print("Connected to MQTT (broker.hivemq.com:1883) successful")

client = mqtt.Client()
client.on_connect = on_connect

#client.username_pw_set("try","try")

if len(sys.argv) != 3:
    print("{} <RaspberryPi_x> <Room>".format(sys.argv[0]))
    print("Ex. {} <RaspberryPi_1> <Room1>".format(sys.argv[0]))
    sys.exit(1)

raspID = sys.argv[1] #"RaspberryPi_1"
room = sys.argv[2] #"Room1"
queryMonitorRoom = "Monitoring/{}".format(room)
queryRasp = "IoT/{}/".format(raspID)

def getHeartRate():
    return(randrange(80, 120))

def getBodyTemperature():
    return(round(uniform(36.5, 37.5),1))

def monitorFirebase():
    t = threading.Timer(5.0, monitorFirebase)
    t.start()
    getStatus_firebase = db.child(queryRasp + "RaspStatus").get().val()
    if(getStatus_firebase == "Active"):
        all_sensors_firebase = db.child(queryRasp + "Sensor").get()
        for sensor_firebase in all_sensors_firebase.each():
            sensors_firebase = db.child(queryRasp + "Sensor/" + sensor_firebase.key() + "/Status").get().val()
            if(sensors_firebase == "Active"):
                sensorName_firebase = db.child(queryRasp + "Sensor/" + sensor_firebase.key() + "/Name").get().val()
                sensorID_firebase = db.child(queryRasp + "Sensor/" + sensor_firebase.key() + "/SensorID").get().val()
                if(sensorName_firebase == "Heart Rate"):
                    heart = getHeartRate()
                    data = {"SensorID": sensorID_firebase, "Type": str(sensorName_firebase), "Value": heart}
                    db.child(queryMonitorRoom).push(data)
                elif(sensorName_firebase == "Body Temperature"):
                    temperature = getBodyTemperature()
                    data2 = {"SensorID": sensorID_firebase, "Type": str(sensorName_firebase), "Value": temperature}
                    db.child(queryMonitorRoom).push(data2)

def monitorMQTT():
    t2 = threading.Timer(1.0, monitorMQTT)
    t2.start()
    getStatus_mqtt = db.child(queryRasp + "RaspStatus").get().val()
    if(getStatus_mqtt == "Active"):
        all_sensors_mqtt = db.child(queryRasp + "Sensor").get()
        for sensor_mqtt in all_sensors_mqtt.each():
            sensors_mqtt = db.child(queryRasp + "Sensor/" + sensor_mqtt.key() + "/Status").get().val()
            if(sensors_mqtt == "Active"):
                sensorName_mqtt = db.child(queryRasp + "Sensor/" + sensor_mqtt.key() + "/Name").get().val()
                sensorTopic_mqtt = db.child(queryRasp + "Sensor/" + sensor_mqtt.key() + "/Topic").get().val()
                if(sensorName_mqtt == "Heart Rate"):
                    heart = getHeartRate()
                    client.publish("{}".format(sensorTopic_mqtt),heart)
                elif(sensorName_mqtt == "Body Temperature"):
                    temperature = getBodyTemperature()
                    client.publish("{}".format(sensorTopic_mqtt),temperature)

firebase = pyrebase.initialize_app(config)
db = firebase.database()
client.connect("broker.hivemq.com", 1883, 60)

print("=========== Version : Beta ===========")
print("Smart eHealth System is running...")
monitorFirebase()
print("Firebase Monitor is running...")
client.loop_start()
monitorMQTT()
print("MQTT Monitor is running...")
print("======================================")
loading = True  # a simple var to keep the loading status
loading_speed = 4  # number of characters to print out per second
loading_string = "." * 6  # characters to print out one by one (6 dots in this example)
while loading:
    for index, char in enumerate(loading_string):
        sys.stdout.write(char)  # write the next char to STDOUT
        sys.stdout.flush()  # flush the output
        time.sleep(1.0 / loading_speed)  # wait to match our speed
    index += 1  # lists are zero indexed, we need to increase by one for the accurate count
    sys.stdout.write("\b" * index + " " * index + "\b" * index)
    sys.stdout.flush()  # flush the output
