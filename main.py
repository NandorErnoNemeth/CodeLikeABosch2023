import pandas as pd
import math
import argparse
from typing import List

parser = argparse.ArgumentParser()
parser.add_argument("csv_path", type=str, help="Path to the .csv file")


def convert_columns(df: pd.DataFrame) -> pd.DataFrame:

    old_columns = df.columns.to_list()
    obj_dist_x = [elem for elem in old_columns if "ObjectDistance_X" in elem]
    obj_dist_y = [elem for elem in old_columns if "ObjectDistance_Y" in elem]

    rename_dist_x = [f"{e+1}_ObjectDistance_X" for e in range(len(obj_dist_x))]
    rename_dist_y = [f"{e+1}_ObjectDistance_Y" for e in range(len(obj_dist_y))]

    obj_speed_x = [elem for elem in old_columns if "ObjectSpeed_X" in elem]
    obj_speed_y = [elem for elem in old_columns if "ObjectSpeed_Y" in elem]

    rename_speed_x = [f"{e+1}_ObjectSpeed_X" for e in range(len(obj_speed_x))]
    rename_speed_y = [f"{e+1}_ObjectSpeed_Y" for e in range(len(obj_speed_y))]

    from_columns = obj_dist_x + obj_dist_y + obj_speed_x + obj_speed_y
    to_columns = rename_dist_x + rename_dist_y + rename_speed_x + rename_speed_y

    columns = {from_columns[i]: to_columns[i] for i in range(len(from_columns))}
    df = df.rename(columns=columns)

    return df


def change_to_si(df: pd.DataFrame) -> pd.DataFrame:
    old_columns = df.columns.to_list()
    obj_dist = [elem for elem in old_columns if "ObjectDistance" in elem]
    df[obj_dist] = df[obj_dist] / 128
    speeds = [elem for elem in old_columns if "Speed" in elem]
    df[speeds] = df[speeds] / 256
    df["YawRate"] = df["YawRate"] * (180 / math.pi)

    return df


def get_preprocessed_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = convert_columns(df)
    df = change_to_si(df)
    return df


class ObjectWithMotion:
    def __init__(self, id, x_distance, y_distance, x_speed, y_speed):
        self.id = id
        self.x_distance = x_distance
        self.y_distance = y_distance
        self.relative_speed = math.sqrt(x_speed ** 2 + y_speed ** 2)


def calculate_ttc(object: ObjectWithMotion) -> float:
    ttc = math.sqrt(object.x_distance ** 2 + object.y_distance ** 2) / max(
        object.relative_speed, 1e-10
    )
    return ttc


def get_current_objects(data: pd.DataFrame, timestamp: float) -> ObjectWithMotion:
    data_current = data[data["Timestamp"] == timestamp]
    object_motions = create_object_motion(data_current)
    return object_motions


def create_object_motion(row: pd.DataFrame) -> List[ObjectWithMotion]:
    objects_with_motion = []
    object_ids = get_object_ids(row)
    for object_id in object_ids:
        id = object_id
        x_distance = row[f"{object_id}_ObjectDistance_X"]
        y_distance = row[f"{object_id}_ObjectDistance_Y"]
        x_speed = row[f"{object_id}_ObjectSpeed_X"]
        y_speed = row[f"{object_id}_ObjectSpeed_Y"]
        objects_with_motion.append(
            ObjectWithMotion(id, x_distance, y_distance, x_speed, y_speed)
        )
    return objects_with_motion


def get_object_ids(row: pd.DataFrame) -> List[int]:
    ids = []
    for col in row.columns:
        if "ObjectDistance_X" in col:
            ids.append(col.split("_")[0])
    return ids


def classify_event(data: pd.DataFrame) -> ObjectWithMotion:
    relevant_object = None
    min_ttc = float("inf")
    timestamps = data["Timestamp"].to_list()

    for timestamp in timestamps:
        current_objects = get_current_objects(
            data, timestamp
        )  # To make sure we dont look into the future
        for object in current_objects:
            if object.relative_speed > 0:
                ttc = calculate_ttc(object)
                if ttc < min_ttc:
                    min_ttc = ttc
                    relevant_object = object
    return relevant_object


def main():
    args = parser.parse_args()
    data = get_preprocessed_data(args.csv_path)
    relevant_event = classify_event(data)
    print(relevant_event.id)


if __name__ == "__main__":
    main()
