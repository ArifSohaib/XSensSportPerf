"""
get files from Xsens data folder and convert to normal timestamp
"""
import colorama
import csv
from pathlib import Path
colorama.init()
data_paths = [Path("D:\\repos\\XSensProject\\Xsens DOT Data Exporter_2020.2.0_win\\data")]

while len(data_paths) > 0:
    curr_path = data_paths.pop(0)
    print(colorama.Fore.LIGHTBLUE_EX+ f"Curr Path {curr_path}")
    for item in curr_path.iterdir():
        if item.is_dir():
            print(colorama.Fore.LIGHTRED_EX+str(item.absolute()))
            data_paths.append(item)
        else:
            print(str(item.absolute()))
print(colorama.Style.RESET_ALL)