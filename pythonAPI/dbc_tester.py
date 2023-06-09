import can
import cantools
import os
from pprint import pprint

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


test_data = bytearray([0x00, 0x00, 0x00, 0x00, 0xD6, 0x60, 0x00, 0x00])
test_msg = can.Message(is_extended_id=False, data=test_data, arbitration_id=0x104)
decoded = dbs[arbitration_id_to_db_name_map[0x104]].decode_message(0x104, test_msg.data)
print(decoded)