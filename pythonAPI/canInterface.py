import can
import os
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
    print("Sensor Hub 1:")
    for i, sensorValue in enumerate(hub1):
        print(f"Sensor {i+1}: {sensorValue}")
    print("\r")
