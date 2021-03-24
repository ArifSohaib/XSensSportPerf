"""
get files from Xsens data folder and convert to normal timestamp
"""
#%%
import colorama
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
colorama.init()
data_paths = [Path("D:\\repos\\XSensProject\\Xsens DOT Data Exporter_2020.2.0_win\\data")]
base_path = Path("D:\\repos\\XSensProject\\Xsens DOT Data Exporter_2020.2.0_win\\")
files_to_read = []
#%%
while len(data_paths) != 0:
    curr_path = data_paths.pop(0)
    print(colorama.Fore.LIGHTBLUE_EX+ f"Curr Path {curr_path}")
    for item in curr_path.iterdir():
        if item.is_dir():
            print(colorama.Fore.LIGHTRED_EX+str(item.absolute()))
            data_paths.append(item)
        else:
            print(str(item.absolute()))
            files_to_read.append(str(item.absolute()))
#%%
increment = timedelta(microseconds=100000)
for csv_file in files_to_read:
    data = pd.read_csv(csv_file,skiprows=1)
    print(colorama.Fore.LIGHTGREEN_EX+f"file: {csv_file}")
    print(colorama.Fore.LIGHTCYAN_EX)
    #print(data.head())
    #get the SampleTimeFine
    #print(data["SampleTimeFine"].values)
    #set first value to timestamp obtained by the filename
    time_components = Path(csv_file).name.split("_")
    initial_date = time_components[-2]
    initial_time = time_components[-1].split(".")[0]
    
    formatted_date = initial_date[:4]+"-"+initial_date[4:6]+"-"+initial_date[6:]
    formatted_time = initial_time[:2]+":"+initial_time[2:4]+":"+initial_time[4:]
    
    file_datetime = datetime.strptime(formatted_date + " " + formatted_time,"%Y-%m-%d %H:%M:%S")
    print(f"when was data collected: {file_datetime}")
    print(f"timestamp for start of data collection: {file_datetime.timestamp()}")
    #add new column to data which adds the timestamp
    timestamps = []
    prev_datetime = file_datetime
    for i in range(len(data["SampleTimeFine"].values)):
        new_datetime = prev_datetime + increment
        timestamps.append(new_datetime)
        prev_datetime = new_datetime
    data["timestamps"] = timestamps
    print(data.head())
    print(f'final timestamp: {timestamps[-1]}')

    input_file_path = Path(csv_file)
    parent_dir = str(input_file_path.parent.absolute()).split("\\")[-1]
    save_dir = Path(base_path,"updated_data",parent_dir)
    #path to save file to 
    if not Path.exists(save_dir):
        Path.mkdir(save_dir)
    save_path = Path(base_path,"updated_data",parent_dir,input_file_path.name)
    print(f"saving to {save_path}")
    data.to_csv(str(save_path.absolute()),index=None)
print(colorama.Style.RESET_ALL)


# %%
