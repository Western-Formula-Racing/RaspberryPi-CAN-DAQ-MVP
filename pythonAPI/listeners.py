import can
from can.message import Message
import cantools
from influxdb import InfluxDBClient
import paho.mqtt.client as mqtt
import datetime
from typing import Any

class InfluxLogMQTTBroadcastListener(can.Listener):
    def __init__(self, ifClient: InfluxDBClient, mqttClient: mqtt.Client, thisMessageFormat: cantools.db, *args: Any, **kwargs: Any) -> None:
        self.ifClient = ifClient
        self.mqttClient = mqttClient
        self.messageFormat = thisMessageFormat

    def on_message_received(self, msg: Message) -> None:
        decoded = self.messageFormat.message_decode(msg.arbitration_id, msg.data)
        board_name = self.messageFormat.get_message_by_frame_id(msg.arbitration_id).name
        body = [{ # I don't know why this object is an array https://influxdb-python.readthedocs.io/en/latest/examples.html
            "measurement": board_name, 
            "time": datetime.datetime.utcnow(),
            "fields": decoded
        }]
        self.ifClient.write_points(body)
        for reading in decoded:
            mqttStr = f"{board_name}/{reading}"
            self.mqttClient.publish(mqttStr, decoded[reading])


