import re 
import csv 

def raw_to_normalized(fname: str) -> None:
    raw_file_reference = open(f"raw/{fname}.log", 'r', encoding="utf-8")
    normalized_file_reference = open(f"normalized/{fname}.csv", 'w', newline='')
    
    writer = csv.writer(normalized_file_reference)
    writer.writerow(["timestamp", "arbitration_id", "data"])
    
    raw_data = raw_file_reference.read()
    for line in raw_data.splitlines():
        arr = line.strip().split()
        id_and_data = arr[2].split('#')
        row = [
            arr[0][1:-1], # remove parentheses from time
            id_and_data[0], # id
            id_and_data[1], # data
        ]
        writer.writerow(row)

    normalized_file_reference.close()
    raw_file_reference.close()


raw_to_normalized("daq_vcan0")
raw_to_normalized("daq_vcan1")
raw_to_normalized("candump_vcan0")
raw_to_normalized("candump_vcan1")