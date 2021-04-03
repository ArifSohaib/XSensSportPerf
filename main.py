from datetime import datetime, timedelta
import colorama
from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.widget import Widget
from kivy.uix.filechooser import FileChooserIconView, FileChooser
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from pathlib import Path
import json
import pandas as pd
import numpy as np

class ActivityGeneratorLayout(Widget):
    msg_lbl = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        colorama.init()
        self.xsens_dir = "D:\\repos\\XSensProject\\Xsens DOT Data Exporter_2020.2.0_win\\"
        self.increment = timedelta(microseconds=100000)
        #self.ids.xsens_base_path.text = "D:\\repos\\XSensProject\\Xsens DOT Data Exporter_2020.2.0_win\\"
        self.settings_file = Path("act_gen_settings.txt")
        self.open_or_reset_settings()

    def open_or_reset_settings(self):
        if Path.exists(self.settings_file):
            with open(Path(self.settings_file),'r') as f:
                settings = json.load(f)
                self.ids.xsens_base_path.text = settings["xsens_dir"]
                try:
                    self.settings_dir = Path(settings["xsens_dir"])
                except:
                    self.ids.msg_lbl.text = "invalid settings dir"
        else:
            settings = {}
            settings["xsens_dir"] = self.xsens_dir
            settings_json = json.dumps(settings)
            with open(self.settings_file,'w') as f:
                f.write(settings_json)  
              
    @staticmethod
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

    @staticmethod
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

    def get_activity_data(self):
        self.ids.msg_lbl.text = "processing" 
        self.open_or_reset_settings()
        self.data_paths = [Path(self.xsens_dir,"data")]
        self.files_to_read = []
        while len(self.data_paths) != 0:
            curr_path = self.data_paths.pop(0)
            print(colorama.Fore.LIGHTBLUE_EX+ f"Curr Path {curr_path}")
            for item in curr_path.iterdir():
                if item.is_dir():
                    print(colorama.Fore.LIGHTRED_EX+str(item.absolute()))
                    self.data_paths.append(item)
                else:
                    print(str(item.absolute()))
                    self.files_to_read.append(str(item.absolute()))
        print(self.files_to_read)
        for csv_file in self.files_to_read:
            data = self.read_input_files(csv_file)#pd.read_csv(csv_file,skiprows=1)
            data = data.astype({'Euler_X':'float32','Euler_Y':'float32','Euler_Z':'float32',
                                'Acc_X':'float32','Acc_Y':'float32','Acc_Z':'float32',
                                'Gyr_X':'float32','Gyr_Y':'float32','Gyr_Z':'float32'})
            print(colorama.Fore.LIGHTGREEN_EX+f"file: {csv_file}")
            print(colorama.Fore.LIGHTCYAN_EX)
            print(f"columns before update: {data.columns}")
            time_components = Path(csv_file).name.split("_")
            initial_date = time_components[-2]
            initial_time = time_components[-1].split(".")[0]
            
            formatted_date = initial_date[:4]+"-"+initial_date[4:6]+"-"+initial_date[6:]
            formatted_time = initial_time[:2]+":"+initial_time[2:4]+":"+initial_time[4:]
            
            file_datetime = datetime.strptime(formatted_date + " " + formatted_time,"%Y-%m-%d %H:%M:%S")
            print(f"when was data collected: {file_datetime}")
            print(f"timestamp for start of data collection: {file_datetime.timestamp()}")
            timestamps = []
            prev_datetime = file_datetime
            for i in range(len(data["SampleTimeFine"].values)):
                new_datetime = prev_datetime + self.increment
                timestamps.append(new_datetime.time())
                prev_datetime = new_datetime
            
            data.loc[:,"Time"] = timestamps
            global_reference_vals = []
            activity_diff = []
            act_x = []
            act_y = []
            act_z = []
            for i in range(len(data["SampleTimeFine"].values)):
                vals = np.array([data["Acc_X"].values[i],data["Acc_Y"].values[i],data["Acc_Z"].values[i]])
                R, global_val = self.rotate(vals, data["Gyr_X"].values[i],data["Gyr_Y"].values[i],data["Gyr_Z"].values[i])
                #print(global_val)
                # act_x.append(np.mean(global_val[0] -  np.array([0,0,9.81])))
                # act_y.append(np.mean(global_val[1] -  np.array([0,0,9.81])))
                # act_z.append(np.mean(global_val[2] -  np.array([0,0,9.81])))
                
                global_val = np.array([np.mean(global_val[0]),np.mean(global_val[1]),np.mean(global_val[2])])
                act_x.append(global_val[0])
                act_y.append(global_val[1])
                act_z.append(global_val[2]-9.81)
                global_reference_vals.append(np.mean(np.abs(global_val)+np.array([0,0,-9.81])))
            print(f"columns after update: {data.columns}")
            print(f'final timestamp: {timestamps[-1]}')
            data.loc[:,~data.columns.str.match("Unnamed")]
            data.loc[:,"free_acc_x"] = act_x
            data.loc[:,"free_acc_y"] = act_y
            data.loc[:,"free_acc_z"] = act_z
            data.loc[:,"activity"] = global_reference_vals
            difference = np.abs(np.diff(global_reference_vals)).tolist()
            data.loc[:,"activity_diff"] = [0.0] + difference
            data.loc[:,"absolute_activity"] = np.abs(global_reference_vals)
            data.loc[:,"activity_g"] = np.array(global_reference_vals) / 9.81
            data.loc[:,"activity_diff_g"] = np.array(data["activity_diff"].values)/9.81
            #print(colorama.Fore.LIGHTYELLOW_EX+f"{difference[:10]}" f"{len(difference)}")
            
            print(colorama.Fore.LIGHTCYAN_EX+f"{data.describe()}")
            print(data.head())
            input_file_path = Path(csv_file)
            parent_dir = str(input_file_path.parent.absolute()).split("\\")[-1]
            save_dir = Path(self.xsens_dir,"updated_data",parent_dir)
            #path to save file to 
            if not Path.exists(save_dir):
                Path.mkdir(save_dir)
            save_path = Path(save_dir,input_file_path.name)
            print(f"saving to {save_path}")
            data.to_csv(str(save_path.absolute()),index=None)
        print(colorama.Style.RESET_ALL)
        self.ids.msg_lbl.text = "processing complete"

class ActivityGeneratorApp(App):
    def build(self):
        return ActivityGeneratorLayout()


if __name__ == '__main__':
    ActivityGeneratorApp().run()