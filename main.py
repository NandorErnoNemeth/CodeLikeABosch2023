import pandas as pd
import math
import argparse
from typing import List

parser = argparse.ArgumentParser()
parser.add_argument("csv_path", type=str, help="Path to the .csv file")


def convert_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renameing the columns to a format of N_"""
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
    """Calculate the SI values with the provided prompts"""
    old_columns = df.columns.to_list()
    obj_dist = [elem for elem in old_columns if "ObjectDistance" in elem]
    df[obj_dist] = df[obj_dist] / 128
    speeds = [elem for elem in old_columns if "Speed" in elem]
    df[speeds] = df[speeds] / 256
    df["YawRate"] = df["YawRate"] * (180 / math.pi)

    return df


def get_preprocessed_data(csv_path: str) -> pd.DataFrame:
    """Rename object columns to a format of N_, and convert values to SI"""
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
    """
    Calculate Time-to-Collision (TTC)
    https://www.spaceacademy.net.au/flight/emg/colltime.htm
    """
    ttc = math.sqrt(object.x_distance ** 2 + object.y_distance ** 2) / max(
        object.relative_speed, 1e-10
    )
    return ttc


def get_current_objects(data: pd.DataFrame, timestamp: float) -> ObjectWithMotion:
    """We get ObjectWithMotion objects for the given timestamp"""
    data_current = data[data["Timestamp"] == timestamp]
    object_motions = create_object_motion(data_current)
    return object_motions


def create_object_motion(row: pd.DataFrame) -> List[ObjectWithMotion]:
    """Create ObjectWithMotion objects for each id in the current row, with data provided in the dataframe"""
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
    """Get all the Ids in the current row of the dataframe"""
    ids = []
    for col in row.columns:
        if "ObjectDistance_X" in col:
            ids.append(col.split("_")[0])
    return ids


def get_current_events_scenario(
    data: pd.DataFrame, timestamp: float, object_id: int
) -> str:
    """We decide which scenario is most likely given the provided data"""
    current_available_data = data[data["Timestamp"] <= timestamp]
    filtered_data = get_relevant_columns_only(current_available_data, object_id)
    scenario = get_current_scenario(filtered_data, object_id)
    return scenario


def get_relevant_columns_only(data: pd.DataFrame, object_id: int) -> pd.DataFrame:
    """Filters the dataframe such way only the relevant columns remain"""
    selected_columns = [
        col
        for col in data.columns
        if str(object_id) in col or col in ["VehicleSpeed", "YawRate"]
    ]
    filtered_df = data[selected_columns]
    return filtered_df


def get_current_scenario(
    data: pd.DataFrame, object_id: int, range_to_check: int = 60
) -> str:
    """Based on the available data, classifies the scenario"""
    last_n_rows = data.tail(range_to_check)
    last_n_yaw_rate_change = last_n_rows["YawRate"].max() - last_n_rows["YawRate"].min()
    if last_n_yaw_rate_change > 15:
        return "CPTA"

    last_n_x_change = (
        last_n_rows[f"{object_id}_ObjectDistance_X"].max()
        - last_n_rows[f"{object_id}_ObjectDistance_X"].min()
    )
    last_n_y_change = (
        last_n_rows[f"{object_id}_ObjectDistance_Y"].max()
        - last_n_rows[f"{object_id}_ObjectDistance_Y"].min()
    )

    if last_n_y_change > last_n_x_change:
        return "CPNCO"
    else:
        return "CPLA"


def classify_event(data: pd.DataFrame) -> ObjectWithMotion:
    """Classifying which event is relevant to us in a Automatic Emergency Brake (AEB) viewpoint"""
    relevant_object = None
    scenario = "No_Scenario"
    scenario_timestamp = -1
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
                    scenario = get_current_events_scenario(data, timestamp, object.id)
                    scenario_timestamp = timestamp
    return relevant_object, scenario, scenario_timestamp

def save_scenario(csv_path: str, data: pd.DataFrame, relevant_event: ObjectWithMotion, scenario: str, scenario_timestamp: float):
    """Saves the scenario to the .csv file"""
    data['Scenario'] = None
    index_to_update = data[data['Timestamp'] == scenario_timestamp].index[0]
    data.loc[index_to_update, 'Scenario'] = f'{relevant_event.id}_{scenario}'
    data.to_csv(csv_path)

def main():
    args = parser.parse_args()
    data = get_preprocessed_data(args.csv_path)
    relevant_event, scenario, scenario_timestamp = classify_event(data)
    print(
        f"At {scenario_timestamp}: object {relevant_event.id} got into scenario {scenario}"
    )
    save_scenario(args.csv_path, data, relevant_event, scenario, scenario_timestamp)


if __name__ == "__main__":
    main()
