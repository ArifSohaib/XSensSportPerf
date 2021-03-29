"""
get files from Xsens data folder and convert to normal timestamp
"""
#%%
import colorama
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
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
def read_input_files(filename:str)->pd.DataFrame:
    x = []
    sep = ''
    with open(filename) as f:
        for i, line in enumerate(f):
            if i == 0:
                sep = line.rstrip()[-1]
            if i > 0:
                x.append(line.rstrip().split(','))
    x = pd.DataFrame(data=x[1:], columns=x[0])
    return x
#%%
def convert_to_radians(angle:float):
    return np.radians(angle)

def rotate(vector:np.array,psi:float, theta:float, sigma:float):
    """
    vector: input matrix to rotate, must be size 3
    sigma: angle in radians 
    theta: angle in radians 
    psi: angle in radians
    """
    sigma = np.radians(sigma)
    theta = np.radians(theta)
    psi = np.radians(psi)
    R_1 = [np.cos(theta)*np.cos(psi), (np.sin(sigma)*np.sin(theta)*np.cos(psi))-(np.cos(sigma)*np.sin(psi)), (np.cos(sigma)*np.sin(theta)*np.cos(psi))-(np.sin(sigma)*np.sin(psi))]
    R_2 = [np.cos(theta)*np.sin(psi), (np.sin(sigma)*np.sin(theta)*np.sin(psi))-(np.cos(sigma)*np.cos(psi)), (np.cos(sigma)*np.sin(theta)*np.sin(psi))-(np.sin(sigma)*np.cos(psi))]
    R_3 = [-1*np.sin(theta),np.sin(psi)*np.cos(theta),np.cos(sigma)*np.cos(theta)]
    R = np.array([R_1,R_2,R_3])
    R = R.T
    if len(vector) == 3:
        result = np.dot(vector , R)
        return R, result
    return R

#%%
increment = timedelta(microseconds=100000)
for csv_file in files_to_read:
    data = read_input_files(csv_file)#pd.read_csv(csv_file,skiprows=1)
    data = data.astype({'Euler_X':'float','Euler_Y':'float','Euler_Z':'float',
                        'Acc_X':'float','Acc_Y':'float','Acc_Z':'float',
                        'Gyr_X':'float','Gyr_Y':'float','Gyr_Z':'float'})
    print(colorama.Fore.LIGHTGREEN_EX+f"file: {csv_file}")
    print(colorama.Fore.LIGHTCYAN_EX)
    print(f"columns before update: {data.columns}")
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
        timestamps.append(new_datetime.time())
        prev_datetime = new_datetime
    
    data.loc[:,"Time"] = timestamps
    global_reference_vals = []
    act_x = []
    act_y = []
    act_z = []
    for i in range(len(data["SampleTimeFine"].values)):
        vals = np.array([data["Acc_X"].values[i],data["Acc_Y"].values[i],data["Acc_Z"].values[i]])
        R, global_val = rotate(vals, data["Gyr_X"].values[i],data["Gyr_Y"].values[i],data["Gyr_Z"].values[i])
        #print(global_val)
        # act_x.append(np.mean(global_val[0] -  np.array([0,0,9.81])))
        # act_y.append(np.mean(global_val[1] -  np.array([0,0,9.81])))
        # act_z.append(np.mean(global_val[2] -  np.array([0,0,9.81])))
        
        global_val = np.array([np.mean(global_val[0]),np.mean(global_val[1]),np.mean(global_val[2])])
        act_x.append(global_val[0])
        act_y.append(global_val[1])
        act_z.append(global_val[2])
        global_reference_vals.append(np.mean(global_val+np.array([0,0,-9.81])))
        
    print(f"columns after update: {data.columns}")
    print(f'final timestamp: {timestamps[-1]}')
    data.loc[:,"free_acc_x"] = act_x
    data.loc[:,"free_acc_y"] = act_y
    data.loc[:,"free_acc_z"] = act_z
    data.loc[:,"activity"] = global_reference_vals
    data.loc[:,~data.columns.str.match("Unnamed")]
    print(data.describe())
    print(data.head())

    input_file_path = Path(csv_file)
    parent_dir = str(input_file_path.parent.absolute()).split("\\")[-1]
    save_dir = Path(base_path,"updated_data",parent_dir)
    #path to save file to 
    if not Path.exists(save_dir):
        Path.mkdir(save_dir)
    save_path = Path(save_dir,input_file_path.name)
    print(f"saving to {save_path}")
    data.to_csv(str(save_path.absolute()),index=None)
print(colorama.Style.RESET_ALL)


# %%

