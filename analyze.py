#! /usr/bin/python

import pyrebase
import sys
from datetime import datetime
import paho.mqtt.client as mqtt

config = {
  "apiKey": "AIzaSyChanfamKiT0sFGlFPgUlLwTQZQnm4sT4I",
  "authDomain": "vital-sign-system.firebaseapp.com",
  "databaseURL": "https://vital-sign-system.firebaseio.com",
  "storageBucket": ""
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

if len(sys.argv) != 2:
    print("{} <Room>".format(sys.argv[0]))
    print("Ex. {} 101".format(sys.argv[0]))
    sys.exit(1)

room = sys.argv[1] # Room 101
monitorQuery = "Monitoring/{}".format(room)
analyzeQuery = "Analyze/{}".format(room)

date_format = '%Y-%m-%d %H:%M:%S'
currentTime = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), date_format)
try:
    countHR = 0
    sumHR = 0
    minHR = 0
    maxHR = 0
    
    countBP = 0
    sum_Top_BP = 0
    sum_Bot_BP = 0
    min_Top_BP = 0
    max_Top_BP = 0
    min_Bot_BP = 0
    max_Bot_BP = 0
    
    countBT = 0
    sumBT = 0.0
    minBT = 0
    maxBT = 0
    
    for monitor in db.child(monitorQuery).get().each():
        monitorDate = db.child("Monitoring/{}/".format(room) + monitor.key() + "/MonitorDate").get().val()
        monitorValue = db.child("Monitoring/{}/".format(room) + monitor.key() + "/Value").get().val()
        monitorType = db.child("Monitoring/{}/".format(room) + monitor.key() + "/Type").get().val()
        getMonitorDate = datetime.strptime(monitorDate,date_format)
        diff = currentTime - getMonitorDate
        diff_hours = diff.seconds / 3600
        if(diff_hours <= 4.0):
            #print(monitorDate,monitorValue,monitorType)
            if(monitorType == "heartrate"):
                if(countHR == 0):
                    minHR = int(monitorValue)
                    maxHR = int(monitorValue)
                    
                if(minHR > int(monitorValue)):
                    minHR = int(monitorValue)
                if(maxHR < int(monitorValue)):
                    maxHR = int(monitorValue)
                    
                sumHR += int(monitorValue)
                countHR += 1
            if(monitorType == "bloodpressure"):
                top,bot = monitorValue.split('/')
                if(countBP == 0):
                    min_Top_BP = int(top)
                    max_Top_BP = int(top)

                    min_Bot_BP = int(bot)
                    max_Bot_BP = int(bot)
    
                if(min_Top_BP > int(top)):
                    min_Top_BP = int(top)
                if(max_Top_BP < int(top)):
                    max_Top_BP = int(top)

                if(min_Bot_BP > int(bot)):
                    min_Bot_BP = int(bot)
                if(max_Bot_BP < int(bot)):
                    max_Bot_BP = int(bot)
                
                sum_Top_BP += int(top)
                
                sum_Bot_BP += int(bot)

                
                countBP += 1
            if(monitorType == "bodytemp"):
                if(countBT == 0):
                    minBT = float(monitorValue)
                    maxBT = float(monitorValue)
                    
                if(minBT > float(monitorValue)):
                    minBT = float(monitorValue)
                if(maxBT < float(monitorValue)):
                    maxBT = float(monitorValue)
                    
                sumBT += float(monitorValue)
                countBT += 1
    print("MinHR = {},MaxHR = {},AvgHR = {}".format(minHR,maxHR,sumHR/countHR))
    print("MinTopBP = {},MaxTopBP = {},AvgTopBP = {}".format(min_Top_BP,max_Top_BP,sum_Top_BP/countBP))
    print("MinBotBP = {},MaxBotBP = {},AvgBotBP = {}".format(min_Bot_BP,max_Bot_BP,sum_Bot_BP/countBP))
    print("MinBT = {},MaxBT = {},AvgBT = {}".format(minBT,maxBT,sumBT/countBT))
    analyze = {"AvgBodyTemperature": sumBT/countBT, "AvgBottomBloodPressure": sum_Bot_BP/countBP, "AvgHeartRate": sumHR/countHR, "AvgTopBloodPressure": sum_Top_BP/countBP,
               "MaxBodyTemperature": maxBT, "MaxBottomBloodPressure": max_Bot_BP, "MaxHeartRate": maxHR, "MaxTopBloodPressure": max_Top_BP, "MinBodyTemperature": minBT,
               "MinBottomBloodPressure": min_Bot_BP, "MinHeartRate": minHR, "MinTopBloodPressure": min_Top_BP}
    db.child(analyzeQuery).update(analyze)
        
except Exception as exception:
    name = repr(exception).split('(')[0]
    print(exception)
    errorDataFirebase = {"Room": room, "Status": 0, "Type": "Error", "TypeName": name}
    db.child("Log").push(errorDataFirebase)
