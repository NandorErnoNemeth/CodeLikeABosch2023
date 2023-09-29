import pandas as pd
import math

df = pd.read_excel('DevelopmentData.xlsx')
lista = df.columns.to_list()

def convert_columns(df : pd.DataFrame):

    old_columns = df.columns.to_list()
    
    obj_dist_x = [elem for elem in old_columns if 'ObjectDistance_X' in elem]
    obj_dist_y = [elem for elem in old_columns if 'ObjectDistance_Y' in elem]

    rename_dist_x = [f"{e+1}ObjectDistance_X" for e in range(len(obj_dist_x))]
    rename_dist_y = [f"{e+1}ObjectDistance_Y" for e in range(len(obj_dist_y))]

    obj_speed_x = [elem for elem in old_columns if 'FirstObjectSpeed_X' in elem]
    obj_speed_y = [elem for elem in old_columns if 'FirstObjectSpeed_Y' in elem]

    rename_speed_x = [f"{e+1}ObjectSpeed_X" for e in range(len(obj_speed_x))]
    rename_speed_y = [f"{e+1}ObjectSpeed_Y" for e in range(len(obj_speed_y))]

    from_columns = obj_dist_x + obj_dist_y + obj_speed_x + obj_speed_y
    to_columns = rename_dist_x + rename_dist_y + rename_speed_x + rename_speed_y

    columns = {from_columns[i]: to_columns[i] for i in range(len(from_columns))}

    df = df.rename(columns=columns)

    return df

def change_to_si(df: pd.DataFrame):
    old_columns = df.columns.to_list()

    obj_dist = [elem for elem in old_columns if 'ObjectDistance' in elem]

    df[obj_dist] = df[obj_dist] / 128

    speeds = [elem for elem in old_columns if 'Speed' in elem]

    df[speeds] = df[speeds] / 256

    df['YawRate'] = df['YawRate'] * (180 / math.pi)

    return df

convert_columns(df)
