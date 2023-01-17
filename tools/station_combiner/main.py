"""
 QuakeMap - Tools - station_combiner
 Outputs intensity_stations.csv.
 NOTES:
    - Before running, make sure that following files are present in this folder:
        - allpositions.csv
 allpositions.csv format - Delimiter ';':
    REGION CODE ; / ; / ; / ; / ; / ; NAME ; / ; LATITUDE ; LONGITUDE ; /
 jma_area_centroid.csv format - Delimiter ',':
    CODE ; NAME ; / ; /
"""
import csv
import traceback


def run():
    try:
        stations: list[dict[str, str]] = []
        areas: dict[str, str] = {}
        with open("../../assets/centroid/jma_area_centroid.csv", "r", encoding="utf-8") as f:
            area_reader = csv.reader(f, delimiter=',')
            for row in area_reader:
                areas[row[0]] = row[1]
            f.close()
        with open("./allpositions.csv", "r", encoding="utf-8") as f:
            station_reader = csv.reader(f, delimiter=';')
            for row in station_reader:
                if not row[0].isdigit():
                    # title
                    continue
                region_name = areas.get(row[0])
                if region_name is None:
                    print(f"Region name unknown for {row[6]}, code {row[0]}.")
                    continue
                stations.append({
                    "name": row[6],
                    "region_code": row[0],
                    "region_name": region_name,
                    "latitude": row[8],
                    "longitude": row[9]
                })
            f.close()
    except Exception:
        print("Failed to open allpositions.csv. Check file existence.")
        traceback.print_exc()
        return
    print(f"Total stations: {len(stations)}")
    with open("../../assets/centroid/intensity_stations.csv", "w+", encoding="utf-8") as f:
        for i in stations:
            f.write(f"{i['name']},{i['region_code']},{i['region_name']},{i['latitude']},{i['longitude']}\n")
        f.close()


if __name__ == "__main__":
    run()
