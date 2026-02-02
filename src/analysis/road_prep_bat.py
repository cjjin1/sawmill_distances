########################################################################################################################
# road_prep_bat.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Simple script that constructs a .bat file that can be used to run the road_prep_bat.py script.
########################################################################################################################

import arcpy, sys, os

python_exe = os.path.join(sys.base_prefix, "python.exe")

bat_path = sys.argv[3]
python_script = os.path.join(os.path.dirname(__file__), "road_prep.py")
params = sys.argv[1:3]

cmd = ["\"" + path + "\"" for path in [python_exe, python_script] + params]
cmd = " ".join(cmd)
cmd += "\npause\n"

with open(bat_path, "w") as f:
    f.write("@echo off\n")
    f.write(cmd)

arcpy.AddMessage(f"To prepare the network dataset, run the .bat file found at {bat_path}")