# Map sensor board CAN IDs to the associated sensor boards

CAN_ID_TO_SENSOR_BOARD_LUT = {
    0x023: {
        "board_name": "SensorBoard1",
        "sensors": [  # the order of the sensors in this array matters, because data is added sequentially based on receival order
            {"sensor_name": "TempSensor1"},
            {"sensor_name": "TempSensor2"},
            {"sensor_name": "TirePressureSensor1"},
            {"sensor_name": "TirePressureSensor2"},
        ],
    },
    0x036: {
        "board_name": "SensorBoard2",
        "sensors": [  # the order of the sensors in this array matters, because data is added sequentially based on receival order
            {"sensor_name": "TempSensor1"},
            {"sensor_name": "TempSensor2"},
            {"sensor_name": "TirePressureSensor1"},
            {"sensor_name": "TirePressureSensor2"},
        ],
    },
}