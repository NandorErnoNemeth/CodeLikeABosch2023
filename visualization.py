import pandas as pd
import matplotlib.pyplot as plt

def count_objects(list : list):
    cnt = 0
    for l in list:
        if 'ObjectDistance_X' in l:
            cnt += 1
    return cnt

df = pd.read_csv('test.csv')

df = df[df['VehicleSpeed'] > 0]

obj_count = count_objects(df.columns.to_list())
columns = df.columns.to_list()

fig, ax = plt.subplots()

current_idx = 0

def update_plot(idx):
    ax.clear()
    
    row = df.iloc[idx]
    obj_pos_cols = [elem for elem in columns if 'ObjectDistance' in elem]

    coordinates = [(0,0)]
    for i in range(0, len(obj_pos_cols), 2):
        if row[obj_pos_cols[i]] != 0 and row[obj_pos_cols[i+1]] != 0:
            coordinates.append((row[obj_pos_cols[i]], row[obj_pos_cols[i+1]]))
        
    y_values = [x[0] for x in coordinates]
    x_values = [x[1] for x in coordinates]
    
    ax.scatter(x_values, y_values, color='red')
    for i, txt in enumerate(coordinates):
        ax.annotate(txt, (x_values[i], y_values[i]))

    ax.set_xlabel('Y-values (m)')
    ax.set_ylabel('X-values (m)')
    ax.set_title(f"Plot of Points t={row['Timestamp']}")
    ax.grid(True)

    ax.set_xlim(-15, 15)
    ax.set_ylim(0, 120)
    
    plt.draw()

update_plot(current_idx)

def on_key(event):
    global current_idx
    if event.key == 'right':
        current_idx += 1
        if current_idx >= len(df):
            current_idx = 0
    elif event.key == 'left':
        current_idx -= 1
        if current_idx < 0:
            current_idx = len(df) - 1
    update_plot(current_idx)

fig.canvas.mpl_connect('key_press_event', on_key)
plt.show()
input('Press enter to end this...')
