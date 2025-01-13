import os
import json
import csv
from datetime import datetime

class Archiver:
    def __init__(self):
        self.archive_folder_json = "Archives_json"
        self.archive_folder_csv = "Archives_csv"
        os.makedirs(self.archive_folder_json, exist_ok=True)
        os.makedirs(self.archive_folder_csv, exist_ok=True)
        self.archive_filename_json = os.path.join(self.archive_folder_json, f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        self.archive_filename_csv = os.path.join(self.archive_folder_csv, f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    def archive_data(self, data):
        timestamp = datetime.now().isoformat()
        archive_entry = {"timestamp": timestamp, "data": data}

        # JSON Archiving
        try:
            with open(self.archive_filename_json, "r") as file:
                archive = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            archive = []

        archive.append(archive_entry)
        with open(self.archive_filename_json, "w") as file:
            json.dump(archive, file, indent=4)

        # CSV Archiving
        file_exists = os.path.isfile(self.archive_filename_csv)
        with open(self.archive_filename_csv, "a", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            if not file_exists:
                csv_writer.writerow(["Timestamp", "Data"])
            csv_writer.writerow([timestamp] + data.split(','))
