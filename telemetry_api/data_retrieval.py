from influxdb_client import InfluxDBClient, Dialect
import csv 
import zipfile
import os

class InfluxDataRetrieval:
    def __init__(self, url, token, org):
        self._influx_client = InfluxDBClient(url=url, token=token, org=org)
        self._query_api = self._influx_client.query_api()

    def _writeToCsv(self, device_name: str, header: list[str], rows: dict[str, list]) -> str:
        with open(f'{device_name}.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in list(rows):
                r = [row]
                for dp in rows[row]:
                    r.append(dp)

                writer.writerow(r) # timestamp, value1, value2, ...

        return f'{device_name}.csv'

    def _generateZip(self, title: str, file_names: list[str]) -> str:
        with zipfile.ZipFile(f'./static/{title}.zip', 'w') as zf:
            for file_name in file_names:
                zf.write(f'{file_name}')

            zf.close()
        
        return f'{title}.zip'

    def _deleteFiles(self, file_names: list[str]) -> None:
        for file_name in file_names:
            os.remove(file_name)

    def printAllDataPointsWithTagCSV(self, tag) -> str:
        # each MEASUREMENT (i.e., CAN device) will have an equal number of datapoints for all devices (CAN signals), 
        # because each datapoint represents a segment of a single CAN frame. On that CAN frame, there will always be values
        # for all other signals

        device_signals = self._query_api.query(f'from(bucket: "RaceData") |> range(start: -6h) |> filter(fn: (r) => r.session_hash=="{tag}") |> group(columns: ["_measurement", "_field"])')
        if len(device_signals) < 1:
            # print an empty csv for this device (_measurement)
            return self._generateZip("no_data", [])

        this_device_name = device_signals[0].records[0].get_measurement()
        this_signal_name = ""
        header = ["timestamp"]
        rows: dict[str, list] = {} # {"[timestamp]": [signal values]}
        file_names = []

        for device_signal in device_signals:
            if device_signal.records[0].get_measurement() != this_device_name:
                file_names.append(self._writeToCsv(this_device_name, header, rows))
                header = ["timestamp"]
                rows = {}        
                this_device_name = device_signal.records[0].get_measurement()

            time = ""
            for signal_datapoint in device_signal.records:
                if signal_datapoint.get_field() != this_signal_name:
                    this_signal_name = signal_datapoint.get_field()
                    header.append(this_signal_name)
                
                time = signal_datapoint.get_time()
                if time in rows:
                    rows[time].append(signal_datapoint.get_value())
                else:
                    rows[time] = [signal_datapoint.get_value()]
        
        file_names.append(self._writeToCsv(this_device_name, header, rows)) # handle the last device
        zip_name = self._generateZip(device_signals[0].records[0].get_stop(), file_names)
        self._deleteFiles(file_names)
        return zip_name

