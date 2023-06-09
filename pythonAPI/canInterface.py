import can
import cantools
import asyncio
from typing import List
import os
from influxdb import InfluxDBClient
import datetime
import paho.mqtt.client as mqtt
from idMaps import CAN_ID_TO_SENSOR_BOARD_LUT
from can.notifier import MessageRecipient
from pprint import pprint

# influxDb config
ifuser = "grafana"
ifpass = "Admin"
ifdb = "home"
ifhost = "127.0.0.1"
ifport = 8086
graphName = "SensorBoard1"
ifclient = InfluxDBClient(
    host="127.0.0.1", port=8086, username="grafana", password="admin", database="home"
)

# load DBs
dbs = {}
arbitration_id_to_db_name_map = {}
for file_name in os.listdir('./dbc'):
    if file_name[-3:] == "dbc":
        dbs[f"{file_name[0:-4]}"] = cantools.database.load_file(f"dbc/{file_name}")
        # map the arbitration IDs to the device name
        for message in dbs[file_name[0:-4]].messages:
            arbitration_id_to_db_name_map[message.frame_id] = file_name[0:-4]


# print out info
for db_name in dbs:
    db = dbs[db_name]
    print(f"db {db_name} messages:")
    messages = db.messages
    pprint(messages)
    for message in messages:
        print(f"{message.name} signals:")
        pprint(db.get_message_by_name(message.name).signals)


# MQTT publisher setup
clientName = "daq"


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))


def on_publish(client, userdata, result):
    #print("MQTT data published")
    pass


mqttClient = mqtt.Client(clientName)
mqttClient.on_connect = on_connect
mqttClient.on_publish = on_publish

mqttClient.connect("localhost", 1883)


# CAN Bus stuff
def decode_and_broadcast(msg: can.Message) -> None:
    #print(msg)
    db = dbs[arbitration_id_to_db_name_map[msg.arbitration_id]] # hashmap; constant lookup time 
    decoded = db.decode_message(msg.arbitration_id, msg.data)
    board_name = db.get_message_by_frame_id(msg.arbitration_id).name
    body = [{ # I don't know why this object is an array https://influxdb-python.readthedocs.io/en/latest/examples.html
        "measurement": board_name,
        "time": datetime.datetime.utcnow(),
        "fields": decoded
    }]
    ifclient.write_points(body)
    for reading in decoded:
        mqttStr = f"{board_name}/{reading}"
        mqttClient.publish(mqttStr, decoded[reading])


async def blocking_reader(reader: can.AsyncBufferedReader) -> None:
    while True:
        await reader.get_message()


filters = [
    # the mask is applied to the filter to determine which bits in the ID to check (https://forum.arduino.cc/t/filtering-and-masking-in-can-bus/586068/3)
    {"can_id": 0x103, "can_mask": 0xFFF, "extended": False},  # sensor board 1
    {"can_id": 0x104, "can_mask": 0xFFF, "extended": False},  # sensor board 2
]

# start an interface using the socketcan interface, using the can0 physical device at a 500KHz frequency with the above filters
bus_one = can.interface.Bus(bustype='socketcan', channel='can1', bitrate=500000, can_filters=filters) # Inverter CAN network bus

# Use the virtual CAN interface in lieu of a physical connection
#bus_one = can.interface.Bus(bustype="socketcan", channel="vcan0", filter=filters[0])
#bus_two = can.interface.Bus(bustype="socketcan", channel="vcan1", filter=filters[1])

async def main() -> None:
    reader_bus_one = can.AsyncBufferedReader()
    # reader_bus_two = can.AsyncBufferedReader()

    # Logger can be used to log to Influx, it just has to be made (see logic in listeners.py)
    logger = can.Logger("logfile.asc")

    listeners_bus_one: List[MessageRecipient] = [
        decode_and_broadcast,  # Callback function
        reader_bus_one,  # AsyncBufferedReader() listener
        logger,  # Regular Listener object
    ]

    # listeners_bus_two: List[MessageRecipient] = [
    #     decode_and_broadcast, 
    #     reader_bus_two,  
    #     logger, 
    # ]

    # Create Notifier with an explicit loop to use for scheduling of callbacks
    loop = asyncio.get_running_loop()
    notifier_bus_one = can.Notifier(bus_one, listeners_bus_one, loop=loop)
    #notifier_bus_two = can.Notifier(bus_two, listeners_bus_two, loop=loop)

    # Right now, this will be running until the car is turned off, so no end 
    await asyncio.gather(
        blocking_reader(reader_bus_one),
        #blocking_reader(reader_bus_two),
    )


if __name__ == "__main__":
    asyncio.run(main())
