import can
import cantools
import asyncio
from typing import List
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import datetime
import paho.mqtt.client as mqtt
from pprint import pprint
from hashlib import sha256
from random import randbytes

# influxDb config
influx_token = os.environ.get('INFLUX_TOKEN')
influx_bucket = os.environ.get('INFLUX_BUCKET')
influx_org = os.environ.get('INFLUX_ORGANIZATION')
influx_url = "http://localhost:8086"
influx_client = InfluxDBClient(
    url = influx_url, 
    org = influx_org,
    token = influx_token,
    debug = True
)
influx_write_api = influx_client.write_api(write_options = SYNCHRONOUS)

# load DBCs
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


# Generate hash to delineate data recording sessions
session_hash = str(sha256(randbytes(32)).hexdigest())
print("Sesssion hash: " + session_hash)


# MQTT publisher setup
clientName = "daq"


def on_connect(client, userdata, flags, reason_codes, properties):
    print("Connected with result code " + str(rc))


def on_publish(client, userdata, result):
    print("MQTT data published")
    pass


mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, clientName)
mqttClient.on_connect = on_connect
mqttClient.on_publish = on_publish

mqttClient.connect("localhost", 1883)


# CAN Bus stuff
def decode_and_broadcast(msg: can.Message) -> None:
    db = dbs[arbitration_id_to_db_name_map[msg.arbitration_id]] # hashmap; constant lookup time 
    decoded = db.decode_message(msg.arbitration_id, msg.data)
    board_name = db.get_message_by_frame_id(msg.arbitration_id).name
    body = { 
        "measurement": board_name,
        "time": datetime.datetime.utcnow(),
        "fields": decoded,
        "tags": {
            "session_hash": session_hash
        }
    }
    data_point = Point.from_dict(body)
    influx_write_api.write(bucket = influx_bucket, record = data_point)
    for reading in decoded:
        mqttStr = f"{board_name}/{reading}"
        mqttClient.publish(mqttStr, decoded[reading])


async def blocking_reader(reader: can.AsyncBufferedReader) -> None:
    while True:
        await reader.get_message()


async def blocking_session_hash_broadcaster() -> None:
    while True:
        mqttClient.publish("telemetry/session_hash", session_hash)
        await asyncio.sleep(1/10) # once per 100 ms


filters = [
    # the mask is applied to the filter to determine which bits in the ID to check (https://forum.arduino.cc/t/filtering-and-masking-in-can-bus/586068/3)
    {"can_id": 259, "can_mask": 0xFFF, "extended": False}, # sensor board 2_1
    {"can_id": 260, "can_mask": 0xFFF, "extended": False}, # sensor board 2_2
    {"can_id": 261, "can_mask": 0xFFF, "extended": False}, # sensor board 1_1
    {"can_id": 262, "can_mask": 0xFFF, "extended": False}, # sensor board 1_2
    {"can_id": 2196807762, "can_mask": 0xFFFFFFF, "extended": True}, # M152_AccData2
    {"can_id": 2196807760, "can_mask": 0xFFFFFFF, "extended": True}, # M150_AccData1
    {"can_id": 2196807732, "can_mask": 0xFFFFFFF, "extended": True}, # M134_MotorTorqueData8
    {"can_id": 2196807730, "can_mask": 0xFFFFFFF, "extended": True}, # M132_MotorTorqueData7
    {"can_id": 2196807728, "can_mask": 0xFFFFFFF, "extended": True}, # M130_MotorTorqueData6
    {"can_id": 2196807720, "can_mask": 0xFFFFFFF, "extended": True}, # M128_MotorTorqueData5
    {"can_id": 2196807704, "can_mask": 0xFFFFFFF, "extended": True}, # M118_VehicleInputs4
    {"can_id": 2196807702, "can_mask": 0xFFFFFFF, "extended": True}, # M116_VehicleInputs3
    {"can_id": 2196807684, "can_mask": 0xFFFFFFF, "extended": True}, # M104_VCU_States3
    {"can_id": 2196807744, "can_mask": 0xFFFFFFF, "extended": True}, # M140_MotorSpeedData3
    {"can_id": 2196807748, "can_mask": 0xFFFFFFF, "extended": True}, # M144_VCU_FaultStates1
    {"can_id": 2196807682, "can_mask": 0xFFFFFFF, "extended": True}, # M102_VCU_States2
    {"can_id": 2196807688, "can_mask": 0xFFFFFFF, "extended": True}, # M108_DriverInputs2
    {"can_id": 2196807700, "can_mask": 0xFFFFFFF, "extended": True}, # M114_VehicleInputs2
    {"can_id": 2196807736, "can_mask": 0xFFFFFFF, "extended": True}, # M138_MotorSpeedData2
    {"can_id": 2196807734, "can_mask": 0xFFFFFFF, "extended": True}, # M136_MotorSpeedData1
    {"can_id": 2196807718, "can_mask": 0xFFFFFFF, "extended": True}, # M126_MotorTorqueData4
    {"can_id": 2196807716, "can_mask": 0xFFFFFFF, "extended": True}, # M124_MotorTorqueData3
    {"can_id": 2196807714, "can_mask": 0xFFFFFFF, "extended": True}, # M122_MotorTorqueData2
    {"can_id": 2196807712, "can_mask": 0xFFFFFFF, "extended": True}, # M120_MotorTorqueData1
    {"can_id": 2196807698, "can_mask": 0xFFFFFFF, "extended": True}, # M112_VehicleInputs1
    {"can_id": 2196807680, "can_mask": 0xFFFFFFF, "extended": True}, # M100_VCU_States1
    {"can_id": 2196807686, "can_mask": 0xFFFFFFF, "extended": True}  # M106_DriverInputs1
]

# start an interface using the socketcan interface, using the can0 physical device at a 500KHz frequency with the above filters
# bus_one = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=500000, can_filters=filters) # BMS CAN network bus
# bus_two = can.interface.Bus(bustype='socketcan', channel='can1', bitrate=500000, can_filters=filters) # Inverter CAN network bus

# Use the virtual CAN interface in lieu of a physical connection
bus_one = can.interface.Bus(bustype="socketcan", channel="vcan0", filter=filters[0])
bus_two = can.interface.Bus(bustype="socketcan", channel="vcan1", filter=filters[1])

async def main() -> None:
    reader_bus_one = can.AsyncBufferedReader()
    reader_bus_two = can.AsyncBufferedReader()

    # Logger can be used to log to Influx, it just has to be made (see logic in listeners.py)
    logger = can.Logger("logfile.asc")

    listeners_bus_one: List[can.notifier.MessageRecipient] = [
        decode_and_broadcast,  # Callback function
        reader_bus_one,  # AsyncBufferedReader() listener
        logger,  # Regular Listener object
    ]

    listeners_bus_two: List[can.notifier.MessageRecipient] = [
        decode_and_broadcast, 
        reader_bus_two,  
        logger, 
    ]

    # Create Notifier with an explicit loop to use for scheduling of callbacks
    loop = asyncio.get_running_loop()
    notifier_bus_one = can.Notifier(bus_one, listeners_bus_one, loop=loop)
    notifier_bus_two = can.Notifier(bus_two, listeners_bus_two, loop=loop)

    # Right now, this will be running until the car is turned off, so no end 
    await asyncio.gather(
        blocking_reader(reader_bus_one),
        blocking_reader(reader_bus_two),
        blocking_session_hash_broadcaster()
    )


if __name__ == "__main__":
    asyncio.run(main())
