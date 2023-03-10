import can
import os
from influxdb import InfluxDBClient
import datetime
import paho.mqtt.client as mqtt

# influxDb config
ifuser = "grafana"
ifpass = "Admin"
ifdb = "home"
ifhost = "127.0.0.1"
ifport = 8086
graphName = "SensorBoard1"
ifclient = InfluxDBClient(host='127.0.0.1', port=8086,
                          username='grafana', password='admin', database='home')


# MQTT publisher setup
clientName = "daq"


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))


def on_publish(client, userdata, result):
    print("data published")
    pass


mqttClient = mqtt.Client(clientName)
mqttClient.on_connect = on_connect
mqttClient.on_publish = on_publish

mqttClient.connect("localhost")

# CAN Bus stuff
filters = [
    # the mask is applied to the filter to determine which bits in the ID to check (https://forum.arduino.cc/t/filtering-and-masking-in-can-bus/586068/3)
    {"can_id": 0x036, "can_mask": 0xFFF, "extended": False}
]
# start an interface using the socketcan interface, using the can0 physical device at a 500KHz frequency with the above filters
bus = can.interface.Bus(bustype='socketcan', channel='can0',
                        bitrate=500000, can_filters=filters)

print("reading Can Bus:")
for msg in bus:
    os.system('clear')
    hub1 = [0 for x in range(8)]
    if msg.arbitration_id == 54:
        for i in range(8):
            hub1[i] = msg.data[i]
    time = datetime.datetime.utcnow()
    body = [
        {
            "measurement": graphName,
            "time": time,

            "fields": {
                "Sensor 1": hub1[0],
                "Sensor 2": hub1[1],
                "Sensor 3": hub1[2],
                "Sensor 4": hub1[3],
                "Sensor 5": hub1[4],
                "Sensor 6": hub1[5],
                "Sensor 7": hub1[6],
                "Sensor 8": hub1[7],

            }
        }
    ]
    ifclient.write_points(body)
    mqttClient.publish("SensorBoard1/sensor1", hub1[0])
    mqttClient.publish("SensorBoard1/sensor2", hub1[1])
    mqttClient.publish("SensorBoard1/sensor3", hub1[2])
    mqttClient.publish("SensorBoard1/sensor4", hub1[3])
    mqttClient.publish("SensorBoard1/sensor5", hub1[4])
    mqttClient.publish("SensorBoard1/sensor6", hub1[5])
    mqttClient.publish("SensorBoard1/sensor7", hub1[6])
    mqttClient.publish("SensorBoard1/sensor8", hub1[7])
    print("Sensor Hub 1:")
    for i, sensorValue in enumerate(hub1):
        print(f"Sensor {i+1}: {sensorValue}")
    print("\r")
