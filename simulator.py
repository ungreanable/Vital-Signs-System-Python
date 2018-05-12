#! /usr/bin/python

import pyrebase
import sys
import datetime
import paho.mqtt.client as mqtt

config = {
  "apiKey": "AIzaSyChanfamKiT0sFGlFPgUlLwTQZQnm4sT4I",
  "authDomain": "vital-sign-system.firebaseapp.com",
  "databaseURL": "https://vital-sign-system.firebaseio.com",
  "storageBucket": ""
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

def on_connect(client, userdeta, flags, rc):
    print("Connected to MQTT (broker.hivemq.com:1883) successful")

client = mqtt.Client()
client.on_connect = on_connect
client.connect("broker.hivemq.com", 1883, 60)

if len(sys.argv) != 5:
    print("{} <IoT_x> <Room> <heartrate|bloodpressure|bodytemp> <Value>".format(sys.argv[0]))
    print("Ex. {} IoT_1 101 heartrate 100".format(sys.argv[0]))
    print("Ex. {} IoT_1 101 bloodpressure 80/120".format(sys.argv[0]))
    print("Ex. {} IoT_1 101 bodytemp 37".format(sys.argv[0]))
    sys.exit(1)

IoTID = sys.argv[1] # IoTID IoT_1
room = sys.argv[2] # Room 101
type = sys.argv[3] # Type of Vital Signs
value = sys.argv[4] # Value or Analyze

queryIoT = "IoT/{}/".format(IoTID)

try:
    getStatusIoT = db.child(queryIoT + "IoTStatus").get().val()
    getRoomID = db.child(queryIoT + "IoTID").get().val()
    if(getStatusIoT == "Active"):
        for sensor in db.child("Sensor").get().each():
            sensorsStatus = db.child("Sensor/" + sensor.key() + "/Status").get().val()
            sensorsRoomID = db.child("Sensor/" + sensor.key() + "/Room").get().val()
            sensorsName = db.child("Sensor/" + sensor.key() + "/Name").get().val()
            sensorsID = db.child("Sensor/" + sensor.key() + "/SensorID").get().val()
            sensorsTopic = db.child("Sensor/" + sensor.key() + "/Topic").get().val()
            if(sensorsStatus == "Active" and getRoomID == sensorsRoomID and getRoomID == room and type == sensorsName):
                data = {"SensorID": sensorsID, "Type": str(sensorsName), "Value": value,"MonitorDate": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                db.child("Monitoring/{}".format(room)).push(data)
                client.publish("{}".format(sensorsTopic),value)
                print("MQTT Publish to Topic: {}, Value: {}".format(sensorsTopic,value))
                for patient in db.child("Patient").get().each():
                    getPatientRoom = db.child("Patient/" + patient.key() + "/Room").get().val()
                    getPatientStatus = db.child("Patient/" + patient.key() + "/Status").get().val()
                    if(room == getPatientRoom and getPatientStatus == "Active"):
                        if(type == "heartrate"):
                            HR_Low = db.child("Patient/" + patient.key() + "/HR_Low").get().val()
                            HR_High = db.child("Patient/" + patient.key() + "/HR_High").get().val()
                            if(int(value) >= 0 and int(value) <= 200):
                                if(int(value) < HR_Low):
                                    alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "Bradycardia", "Value": value, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                    db.child("Log").push(alertFirebase)
                                    print("Bradycardia Value Added to Alert")
                                if(int(value) > HR_High):
                                    alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "Tachycardia", "Value": value, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                    db.child("Log").push(alertFirebase)
                                    print("Tachycardia Value Added to Alert")
                            else:
                                errorDataFirebase = {"SensorName": sensorsName,"SensorID": sensorsID,"Room": room, "Status": 0, "Type": "Error", "TypeName": "Out of Range Value", "Value": value}
                                db.child("Log").push(errorDataFirebase)
                               
                        elif(type == "bloodpressure"):
                            BPTop_Low = db.child("Patient/" + patient.key() + "/BPTop_Low").get().val()
                            BPTop_High = db.child("Patient/" + patient.key() + "/BPTop_High").get().val()
                            BPBot_Low = db.child("Patient/" + patient.key() + "/BPBot_Low").get().val()
                            BPBot_High = db.child("Patient/" + patient.key() + "/BPBot_High").get().val()
                            top,bot = value.split('/')
                            if( (int(top) >= 70 and int(top) <= 190) or (int(bot) >= 40 and int(bot) <= 100) ):
                                if(int(top) < BPTop_Low or int(bot) < BPBot_Low):
                                    alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "Hypotension", "Value": value, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                    db.child("Log").push(alertFirebase)
                                    print("Hypotension Value Added to Alert")
                                if(int(top) > BPTop_High or int(bot) > BPBot_High):
                                    alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "Hypertension", "Value": value, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                    db.child("Log").push(alertFirebase)
                                    print("Hypertension Value Added to Alert")
                            else:
                                errorDataFirebase = {"SensorName": sensorsName,"SensorID": sensorsID,"Room": room, "Status": 0, "Type": "Error", "TypeName": "Out of Range Value", "Value": value}
                                db.child("Log").push(errorDataFirebase)
                        elif(type == "bodytemp"):    
                            BT_Low = db.child("Patient/" + patient.key() + "/BT_Low").get().val()
                            BT_High = db.child("Patient/" + patient.key() + "/BT_High").get().val()
                            if(float(value) >= 30.0 and float(value) <= 45.0):   
                                if(float(value) < BT_Low):
                                    alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "Hypothermia", "Value": value, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                    db.child("Log").push(alertFirebase)
                                    print("Hypothermia Value Added to Alert")
                                if(float(value) > BT_High):
                                    alertFirebase = {"Room": room, "Status": 0, "Type": "Alert", "Description": "Hyperthermia", "Value": value, "LogDateTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                    db.child("Log").push(alertFirebase)
                                    print("Hyperthermia Value Added to Alert")
                            else:
                                errorDataFirebase = {"SensorName": sensorsName,"SensorID": sensorsID,"Room": room, "Status": 0, "Type": "Error", "TypeName": "Out of Range Value", "Value": value}
                                db.child("Log").push(errorDataFirebase)
                        #print("HR_Low = {}\nHR_High = {}".format(HR_Low,HR_High))
                        #print("BPTop_Low = {}\nBPTop_High = {}".format(BPTop_Low,BPTop_High))
                        #print("BPBot_Low = {}\nBPBot_High = {}".format(BPBot_Low,BPBot_High))
                        #print("BT_Low = {}\nBT_High = {}".format(BT_Low,BT_High))
                        break
            elif(sensorsStatus != "Active" and getRoomID == sensorsRoomID and type == sensorsName):
                print("{} Status: Deactive".format(db.child("Sensor/" + sensor.key() + "/Name").get().val()))
    else:
        print("{} Status: Deactive".format(IoTID))
except Exception as exception:
    name = repr(exception).split('(')[0]
    print(exception)
    errorDataFirebase = {"Room": room, "Status": 0, "Type": "Error", "TypeName": name}
    db.child("Log").push(errorDataFirebase)
