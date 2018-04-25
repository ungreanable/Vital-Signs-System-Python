#! /usr/bin/python

import pyrebase
import threading
import sys
import paho.mqtt.client as mqtt
from random import randrange, uniform

config = {
  "apiKey": "AIzaSyChanfamKiT0sFGlFPgUlLwTQZQnm4sT4I",
  "authDomain": "vital-sign-system.firebaseapp.com",
  "databaseURL": "https://vital-sign-system.firebaseio.com",
  "storageBucket": ""
}

def on_connect(client, userdeta, rc):
    print("Connected to broker.hivemq.com with result code " + str(rc))
	
client = mqtt.Client()
client.on_connect = on_connect

#client.username_pw_set("try","try")

if len(sys.argv) != 3:
    print("{} <RaspberryPi_x> <Room>".format(sys.argv[0]))
    print("Ex. {} <RaspberryPi_1> <Room1>".format(sys.argv[0]))
    sys.exit(1)

raspID = sys.argv[1] #"RaspberryPi_1"
room = sys.argv[2] #"Room1"
queryMonitorRoom = "Monitoring/{0}".format(room)
queryRasp = "IoT/{0}/".format(raspID)

def getHeartRate():
    return(randrange(80, 120))

def getBodyTemperature():
    return(round(uniform(36.5, 37.5),1))

def monitorFirebase():
    t = threading.Timer(5.0, monitorFirebase)
    t.start()
    getStatus_firebase = db.child(queryRasp + "RaspStatus").get().val()
    if(getStatus_firebase == "Active"):
        all_sensors = db.child(queryRasp + "Sensor").get()
        for sensor in all_sensors.each():
            sensors = db.child(queryRasp + "Sensor/" + sensor.key() + "/Status").get()
            if(sensors.val() == "Active"):
                sensorName = db.child(queryRasp + "Sensor/" + sensor.key() + "/Name").get().val()
                sensorID = db.child(queryRasp + "Sensor/" + sensor.key() + "/SensorID").get().val()
                if(sensorName == "Heart Rate"):
                    heart = getHeartRate()
                    data = {"SensorID": sensorID, "Type": str(sensorName), "Value": heart}
                    db.child(queryMonitorRoom).push(data)
                elif(sensorName == "Body Temperature"):
                    temperature = getBodyTemperature()
                    data = {"SensorID": sensorID, "Type": str(sensorName), "Value": temperature}
                    db.child(queryMonitorRoom).push(data)

def monitorMQTT():
    t2 = threading.Timer(1.0, monitorMQTT)
    t2.start()
    getStatus_mqtt = db.child(queryRasp + "RaspStatus").get().val()
    if(getStatus_mqtt == "Active"):
        all_sensors = db.child(queryRasp + "Sensor").get()
        for sensor in all_sensors.each():
            sensors = db.child(queryRasp + "Sensor/" + sensor.key() + "/Status").get()
            if(sensors.val() == "Active"):
                sensorName = db.child(queryRasp + "Sensor/" + sensor.key() + "/Name").get().val()
                sensorID = db.child(queryRasp + "Sensor/" + sensor.key() + "/SensorID").get().val()
                sensorTopic = db.child(queryRasp + "Sensor/" + sensor.key() + "/Topic").get().val()
                if(sensorName == "Heart Rate"):
                    heart = getHeartRate()
                    client.publish("{}".format(sensorTopic),heart)
                elif(sensorName == "Body Temperature"):
                    temperature = getBodyTemperature()
                    client.publish("{}".format(sensorTopic),temperature)

firebase = pyrebase.initialize_app(config)
db = firebase.database()
monitorFirebase()
monitorMQTT()
print("Smart eHealth System is running...")
client.connect("broker.hivemq.com", 1883, 60)
