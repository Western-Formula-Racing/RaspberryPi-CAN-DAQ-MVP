from influxdb_client import InfluxDBClient, Dialect
import csv 
import zipfile
import os

from motec_conversion.data_log import DataLog
from motec_conversion.motec_log import MotecLog

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

    # Return a tuple containing the last_time of measurement, and the file_names of all generated CSVs 
    def _generateAllDataPointsCSV(self, tag) -> (str, list[str]):
        # each MEASUREMENT (i.e., CAN device) will have an equal number of datapoints for all devices (CAN signals), 
        # because each datapoint represents a segment of a single CAN frame. On that CAN frame, there will always be values
        # for all other signals

        device_signals = self._query_api.query(f'from(bucket: "RaceData") |> range(start: -6h) |> filter(fn: (r) => r.session_hash=="{tag}") |> group(columns: ["_measurement", "_field"])')
        if len(device_signals) < 1:
            # return an empty zip file when no data is present
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
        return device_signals[0].records[0].get_stop(), file_names

    # Currently this is pretty slow when there's a lot of data. A method of increasing the speed is to 
    # use multithreading: find out how many devices (measurements) there are first, spawn threads for each measurement,
    # transform and write all points to a CSV for each signal on that device, have a running consumer thread that zips
    # each file upon completion, close the zip after all CSV-writing threads finish, and return the name. Still probably will
    # take a while, but less time. Maybe consider query optimization also so influx formats the data in the most congruent form for CSV
    # writing, as I think most of the time comes from that processing portion.  
    def writeAllDataPointsWithTagCSV(self, tag) -> str:
        last_time, file_names = self._generateAllDataPointsCSV(tag)
        zip_name = self._generateZip(last_time, file_names)
        self._deleteFiles(file_names)
        return zip_name

    def writeAllDataPointsWithTagMotec(self, tag) -> str: 
        last_time, file_names = self._generateAllDataPointsCSV(tag)
        i = 0
        for file_name in file_names:
            with open(file_name, "r") as f:
                lines = f.readlines()

            # Set the data log object
            data_log = DataLog()
            data_log.from_csv_log(lines)
            data_log.resample(20.0) # experimental value in Hz I think
            
            # Set metadata fields for the motec log object
            motec_log = MotecLog()
            motec_log.driver = "Maybe Samya?"
            motec_log.vehicle_id = "WFR24"
            motec_log.vehicle_weight = 0
            motec_log.vehicle_type = "FSAE"
            motec_log.vehicle_comment = "Built with Love"
            motec_log.venue_name = ""
            motec_log.event_name = ""
            motec_log.event_session = ""
            motec_log.long_comment = ""
            motec_log.short_comment = ""

            motec_log.initialize()
            motec_log.add_all_channels(data_log)
            
            # Save the motec log
            ld_filename = os.path.join(file_name[0:-3] + "ld") # "./blahblah.csv" -> "./blahblah.ld"
            file_names[i] = ld_filename
            i += 1
            motec_log.write(ld_filename)

        zip_name = self._generateZip(last_time, file_names)
        self._deleteFiles(file_names)
        return zip_name
