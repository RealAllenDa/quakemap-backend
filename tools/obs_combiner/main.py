"""
 QuakeMap - Tools - obs_combiner
 Outputs observation_points.json.
 NOTES:
    - Before running, make sure that following files are present in this folder:
        - Stations.csv
 Stations.csv format - Delimiter ';':
    ID ; / ; / ; TYPE ; NAME ; REGION ; SUBREGION CODE ; REGION CODE ; LONGITUDE ; LATITUDE ; PIXEL X ; PIXEL Y
"""
import csv
import json
import traceback


def run():
    try:
        content_stations: list[dict[str, str]] = []
        with open("Stations.csv", "r", encoding="utf-8") as f:
            station_reader = csv.reader(f, delimiter=';')
            for row in station_reader:
                content_stations.append({
                    "Type": row[3],
                    "Name": row[4],
                    "Region": row[5],
                    "SubRegionCode": row[6],
                    "RegionCode": row[7],
                    "IsSuspended": False,
                    "Location": {
                        "Latitude": row[9],
                        "Longitude": row[8]
                    },
                    "OldLocation": None,
                    "Point": {
                        "X": row[10],
                        "Y": row[11]
                    },
                    "ClassificationId": None,
                    "PrefectureClassificationId": None
                })
            f.close()
    except Exception:
        print("Failed to open station.txt. Check file existence.")
        traceback.print_exc()
        return
    print(f"Total stations: {len(content_stations)}")
    with open("../../assets/centroid/observation_points.json", "w+", encoding="utf-8") as f:
        f.write(json.dumps(content_stations))
        f.close()


if __name__ == "__main__":
    run()
