from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import influxdb_client
import paho.mqtt.client as mqtt
import socket

session_hash = ""

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("telemetry/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    if msg.topic == "telemetry/session_hash":
        global session_hash
        session_hash = msg.payload.decode()


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect("mqtt_broker", 1883, 5)

# Maintain connection to mqtt_broker on a new thread
mqttc.loop_start()

app = Flask(__name__)

# Do this to tell flask's built-in server we're behind the nginx proxy
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

@app.route("/", methods=['GET'])
def connection_status():
    # If you're not connected then you'll just get no return lol 
    return { "status": "Connected" }


@app.route("/session_hash/latest", methods=['GET'])
def current_session_hash_get():
    return { "session_hash": session_hash }
