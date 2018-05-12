#! /usr/bin/python

import pyrebase
import sys
import paho.mqtt.client as mqtt
import datetime
import time
from random import randrange, uniform

config = {
  "apiKey": "AIzaSyChanfamKiT0sFGlFPgUlLwTQZQnm4sT4I",
  "authDomain": "vital-sign-system.firebaseapp.com",
  "databaseURL": "https://vital-sign-system.firebaseio.com",
  "storageBucket": ""
}

def getHeartRate():
    random = randrange(1,200)
    if(random == 199):
        return(randrange(35, 59))
    elif(random == 200):
        return(randrange(140,180))
    else:
        return(randrange(60, 120))

def getBloodPressure():
    random = randrange(1,200)
    if(random == 199):
        bloodpressure = [randrange(70,90),randrange(40,60)]
    elif(random == 200):
        bloodpressure = [randrange(140,190),randrange(90,100)]
    else:
        bloodpressure = [randrange(91,119),randrange(61,80)]
    return bloodpressure    

def getBodyTemperature():
    random = randrange(1,200)
    if(random == 199):
        return(round(uniform(35.0, 35.9),1))
    elif(random == 200):
        return(round(uniform(38.0, 41.0),1))
    else:
        return(round(uniform(36.0, 37.5),1))

def on_connect(client, userdeta, flags, rc):
    print("Connected to MQTT (broker.hivemq.com:1883) successful")

if len(sys.argv) != 3:
    print("{} <IoT_x> <Room>".format(sys.argv[0]))
    print("Ex. {} <IoT_1> <101>".format(sys.argv[0]))
    sys.exit(1)

IoTID = sys.argv[1] #"IoT_1"
room = sys.argv[2] #"Room1"
queryMonitorRoom = "Monitoring/{}".format(room)
queryIoT = "IoT/{}/".format(IoTID)

HRList = []
BTList = []
BP_TOP_List = []
BP_BOT_List = []
AvgHR = 0
AvgBT = 0
AvgBP_TOP = 0
AvgBP_BOT = 0

HR_Low = 0
HR_High = 0
BPTop_Low = 0
BPTop_High = 0
BPBot_Low = 0
BPBot_High = 0
BT_Low = 0
BT_High = 0

def monitorFirebase():
    global HRList,BTList,BP_TOP_List,BP_BOT_List,AvgHR,AvgBT,AvgBP_TOP,AvgBP_BOT
    try:
        getStatus_firebase = db.child(queryIoT + "IoTStatus").get().val()
        getRoomID_firebase = db.child(queryIoT + "IoTID").get().val()
        if(getStatus_firebase == "Active"):
            for sensor_firebase in db.child("Sensor").get().each():
                sensorsStatus_firebase = db.child("Sensor/" + sensor_firebase.key() + "/Status").get().val()
                sensorsRoomID_firebase = db.child("Sensor/" + sensor_firebase.key() + "/Room").get().val()
                if(sensorsStatus_firebase == "Active" and getRoomID_firebase == sensorsRoomID_firebase):
                    sensorName_firebase = db.child("Sensor/" + sensor_firebase.key() + "/Name").get().val()
                    sensorID_firebase = db.child("Sensor/" + sensor_firebase.key() + "/SensorID").get().val()
                    if(sensorName_firebase == "Heart Rate"):
                        AvgHR = 0
                        countHR = len(HRList)
                        for HR in HRList:
                            AvgHR += HR
                        AvgHR = AvgHR // countHR
                        data = {"Count": countHR,"SensorID": sensorID_firebase, "Type": str(sensorName_firebase), "AvgValue": AvgHR,"MonitorDate": datetime.datetime.now().strftime('%H:%M:%S')}
                        db.child(queryMonitorRoom).push(data)
                            
                    elif(sensorName_firebase == "Body Temperature"):
                        AvgBT = 0
                        countBT = len(BTList)
                        for BT in BTList:
                            AvgBT += BT
                        AvgBT = AvgBT / countBT
                        data = {"Count": countBT,"SensorID": sensorID_firebase, "Type": str(sensorName_firebase), "AvgValue": round(AvgBT,1),"MonitorDate": datetime.datetime.now().strftime('%H:%M:%S')}
                        db.child(queryMonitorRoom).push(data) 
                        
                    elif(sensorName_firebase == "Blood Pressure"):
                        AvgBP_TOP = 0
                        AvgBP_BOT = 0
                        countBP_TOP = len(BP_TOP_List)
                        countBP_BOT = len(BP_BOT_List)

                        for BP_TOP in BP_TOP_List:
                            AvgBP_TOP += BP_TOP
                        AvgBP_TOP = AvgBP_TOP // countBP_TOP
                        for BP_BOT in BP_BOT_List:
                            AvgBP_BOT += BP_BOT
                        AvgBP_BOT = AvgBP_BOT // countBP_BOT
                        bloodpressure = "{}/{}".format(AvgBP_TOP,AvgBP_BOT)
                        BPCount = "{}/{}".format(countBP_TOP,countBP_BOT)
                        data = {"Count": BPCount,"SensorID": sensorID_firebase, "Type": str(sensorName_firebase), "AvgValue": bloodpressure,"MonitorDate": datetime.datetime.now().strftime('%H:%M:%S')}
                        db.child(queryMonitorRoom).push(data)
                        
            HRList = []
            BTList = []
            BP_TOP_List = []
            BP_BOT_List = []
            data = {}
    except Exception as exception:
        name = repr(exception).split('(')[0]
        print(exception)
        errorDataFirebase = {"Room": room, "Status": 0, "Type": "ErrorFirebase", "TypeName": name}
        db.child("Log").push(errorDataFirebase)

def monitorMQTT():
    global HRList,BTList,BP_TOP_List,BP_BOT_List,AvgHR,AvgBT,AvgBP_TOP,AvgBP_BOT
    try:
        getStatus_mqtt = db.child(queryIoT + "IoTStatus").get().val()
        getRoomID_mqtt = db.child(queryIoT + "IoTID").get().val()
        if(getStatus_mqtt == "Active"):
            for sensor_mqtt in db.child("Sensor").get().each():
                sensorsStatus_mqtt = db.child("Sensor/" + sensor_mqtt.key() + "/Status").get().val()
                sensorsRoomID_mqtt = db.child("Sensor/" + sensor_mqtt.key() + "/Room").get().val()
                if(sensorsStatus_mqtt == "Active" and getRoomID_mqtt == sensorsRoomID_mqtt):          
                    sensorName_mqtt = db.child("Sensor/" + sensor_mqtt.key() + "/Name").get().val()
                    sensorTopic_mqtt = db.child("Sensor/" + sensor_mqtt.key() + "/Topic").get().val()
                    if(sensorName_mqtt == "Heart Rate"):
                        heart = getHeartRate()
                        if(heart >= 35 and heart <= 59):
                            alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "Bradycardia", "Value": heart, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            db.child("Log").push(alertFirebase)
                        elif(heart >= 140 and heart <= 180):
                            alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "Tachycardia", "Value": heart, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            db.child("Log").push(alertFirebase)
                        HRList.append(heart)
                        client.publish("{}".format(sensorTopic_mqtt),heart)
                    elif(sensorName_mqtt == "Body Temperature"):
                        bodytemp = getBodyTemperature()
                        if( bodytemp >= 35.0 and bodytemp <= 35.9 ):
                            alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "Low-grade fever", "Value": bodytemp, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            db.child("Log").push(alertFirebase)
                        elif( bodytemp >= 38.0 and bodytemp <= 41.0 ):
                            alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "High-grade fever", "Value": bodytemp, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            db.child("Log").push(alertFirebase)
                        BTList.append(bodytemp)
                        client.publish("{}".format(sensorTopic_mqtt),bodytemp)
                    elif(sensorName_mqtt == "Blood Pressure"):
                        bp = getBloodPressure()
                        top = bp[0]
                        BP_TOP_List.append(top)
                        bot = bp[1]
                        BP_BOT_List.append(bot)
                        blood_pressure = "{}/{}".format(top,bot)
                        if(top >= 140 and top <= 190):
                            alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "High Blood Pressure", "Value": blood_pressure, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            db.child("Log").push(alertFirebase)
                        elif(top >= 70 and top <= 90):
                            alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "Low Blood Pressure", "Value": blood_pressure, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            db.child("Log").push(alertFirebase)
                        client.publish("{}".format(sensorTopic_mqtt),blood_pressure)
    except Exception as exception:
        name = repr(exception).split('(')[0]
        print(exception)
        errorDataFirebase = {"Room": room, "Status": 0, "Type": "ErrorMQTT", "Description": name}
        db.child("Log").push(errorDataFirebase)

def getValueToAlert():
    global HR_Low,HR_High,BPTop_Low,BPTop_High,BPBot_Low,BPBot_High,BT_Low,BT_High
    for patient in db.child("Patient").get().each():
        print(patient.key())
        getRoom = db.child("Patient/" + patient.key() + "/Room").get().val()
        getPatientStatus = db.child("Patient/" + patient.key() + "/Status").get().val()
        if(room == getRoom and getPatientStatus == "Active"):
            HR_Low = db.child("Patient/" + patient.key() + "/HR_Low").get().val()
            HR_High = db.child("Patient/" + patient.key() + "/HR_High").get().val()

            BPTop_Low = db.child("Patient/" + patient.key() + "/BPTop_Low").get().val()
            BPTop_High = db.child("Patient/" + patient.key() + "/BPTop_High").get().val()
            BPBot_Low = db.child("Patient/" + patient.key() + "/BPBot_Low").get().val()
            BPBot_High = db.child("Patient/" + patient.key() + "/BPBot_High").get().val()

            BT_Low = db.child("Patient/" + patient.key() + "/BT_Low").get().val()
            BT_High = db.child("Patient/" + patient.key() + "/BT_High").get().val()
            print("HR_Low = {}\nHR_High = {}".format(HR_Low,HR_High))
            print("BPTop_Low = {}\nBPTop_High = {}".format(BPTop_Low,BPTop_High))
            print("BPBot_Low = {}\nBPBot_High = {}".format(BPBot_Low,BPBot_High))
            print("BT_Low = {}\nBT_High = {}".format(BT_Low,BT_High))
            break

firebase = pyrebase.initialize_app(config)
db = firebase.database()
client = mqtt.Client()
client.on_connect = on_connect
client.connect("broker.hivemq.com", 1883, 60)
#client.loop_start()
monitorMQTT()
getValueToAlert()
print("================= Version : Beta =================")
print("Smart eHealth System is running...")
print("Firebase Monitor is will run in every 60 seconds...")
print("MQTT Monitor is running...")
print("==================================================")
