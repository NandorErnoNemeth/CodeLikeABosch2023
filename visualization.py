import pandas as pd
import matplotlib.pyplot as plt
import math 

# Init subplots
fig, (ax, ax_speed, ax_path) = plt.subplots(1, 3, figsize=(20, 6))


N = 5  # Set this to the number of previous plots you want to display

# FLAGS AND PARAMS
current_idx = 0
play_mode = False  # Flag to check if video mode is on
timer = fig.canvas.new_timer(interval=50) 

# Compute path based on speed and yaw rate
def convert_df() -> pd.DataFrame:
    df = pd.read_excel('DevelopmentData.xlsx')

    if 'Unnamed: 0' in df.columns.to_list():
        df = df.drop(columns=['Unnamed: 0'])
    
    old_columns = df.columns.to_list()

    obj_dist = [elem for elem in old_columns if 'ObjectDistance' in elem]

    df[obj_dist] = df[obj_dist] / 128

    speeds = [elem for elem in old_columns if 'Speed' in elem]

    df[speeds] = df[speeds] / 256

    return df

def calculate_coordinates(speed, yaw, timestamps):
    x, y = 0, 0
    coordinates = [(x, y)]
    
    for i in range(1, len(timestamps)):
        delta_t = timestamps[i] - timestamps[i-1]
        
        #rad
        delta_x = speed[i] * math.cos(yaw[i]) * delta_t
        delta_y = speed[i] * math.sin(yaw[i]) * delta_t
        
        x += delta_x
        y += delta_y
        
        coordinates.append((x, y))
    
    return coordinates

def plot_row(idx, ax, alpha_val, color, annotate=True):
    row = df.iloc[idx]
    obj_pos_cols = [elem for elem in columns if 'ObjectDistance' in elem]
    coordinates = [(0,0)]

    for i in range(0, len(obj_pos_cols), 2):
        if row[obj_pos_cols[i]] != 0 and row[obj_pos_cols[i+1]] != 0:
            coordinates.append((row[obj_pos_cols[i]], row[obj_pos_cols[i+1]]))
        
    y_values = [x[0] for x in coordinates]
    x_values = [x[1] for x in coordinates]

    ax.scatter(x_values, y_values, color=color, alpha=alpha_val)
    if annotate:
        for i, txt in enumerate(coordinates):
            ax.annotate(txt, (x_values[i], y_values[i]))

def update_plot(idx):
    ax.clear()
    ax_speed.clear()
    ax_path.clear()

    # Plotting previous N positions
    for n in range(1, N+1):
        if idx - n >= 0:
            plot_row(idx - n, ax, alpha_val=(1.0 - (n/N)*0.6), color=plt.cm.jet(1.0 - n/N), annotate=False)

    # Current position
    plot_row(idx, ax, alpha_val=1.0, color='red', annotate=True)
    ax.set_xlabel('Y-values (m)')
    ax.set_ylabel('X-values (m)')
    ax.set_title("Radar view")
    ax.grid(True)
    ax.set_xlim(-15, 15)
    ax.set_ylim(0, 120)
    
    # Speed plot
    ax_speed.plot(df['Timestamp'], df['VehicleSpeed'], color='blue')
    ax_speed.scatter(df.iloc[idx]['Timestamp'], df.iloc[idx]['VehicleSpeed'], color='red')
    ax_speed.set_xlabel('Timestamp')
    ax_speed.set_ylabel('Vehicle Speed (m/s)')
    ax_speed.set_title('Speed over Time')
    ax_speed.grid(True)

    # Car path plot
    #x_path, y_path = zip(*path)
    y_path, x_path = zip(*path)
    
    ax_path.plot(x_path, y_path, color='blue')
    ax_path.scatter(x_path[idx], y_path[idx], color='red', s=100)  # Current position
    ax_path.set_xlabel('Y Position (m)')
    ax_path.set_ylabel('X Position (m)')
    ax_path.set_title('Car Path')
    ax_path.grid(True)

    # Display current speed, yaw, and timestamp on top-right corner
    info_text = f"Speed: {df.iloc[idx]['VehicleSpeed']:.2f} m/s\n"
    info_text += f"Yaw: {df.iloc[idx]['YawRate']:.2f} rad\n"
    info_text += f"Timestamp: {df.iloc[idx]['Timestamp']}"
    fig.text(0.85, 0.10, info_text, va='top', ha='left', fontsize=10, bbox=dict(boxstyle="square", facecolor='white'))

    fig.canvas.draw()

def on_key(event):
    global current_idx, play_mode
    
    if event.key in ['right', 'left']:
        timer.stop()
        play_mode = False
        if event.key == 'right':
            current_idx += 1
            if current_idx >= len(df):
                current_idx = 0
        else:
            current_idx -= 1
            if current_idx < 0:
                current_idx = len(df) - 1
                
        update_plot(current_idx)
        
    elif event.key == 'up':
        play_mode = not play_mode
        if play_mode:
            timer.start()
        else:
            timer.stop()

def auto_play(*args):
    global current_idx
    current_idx += 1
    if current_idx >= len(df):
        current_idx = 0
    update_plot(current_idx)

# How to use the plotter
print("Next image press right arrow")
print("Prev image press left arrow")
print("Auto play press upper arrow")

df = convert_df()
columns = df.columns.to_list()

# Extracting speeds, yaw rates, and timestamps
speeds = df['VehicleSpeed'].to_list()
yaw_rates = df['YawRate'].to_list()
timestamps = df['Timestamp'].to_list()
path = calculate_coordinates(speeds, yaw_rates, timestamps)

timer.add_callback(auto_play)

fig.canvas.mpl_connect('key_press_event', on_key)
plt.tight_layout()
update_plot(current_idx)
plt.show()
