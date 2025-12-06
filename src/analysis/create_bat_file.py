########################################################################################################################
# create_bat_file.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Simple script that constructs a .bat file that can be used to run the cf_all_sites.py script.
########################################################################################################################

import arcpy, sys, os

python_exe = os.path.join(sys.base_prefix, "python.exe")
python_script = os.path.join(os.path.dirname(__file__), "cf_all_sites.py")

bat_path = sys.argv[1]
try:
    proj = arcpy.mp.ArcGISProject("CURRENT")
    workspace = proj.defaultGeodatabase
except OSError:
    workspace = sys.argv[11]

cmd = " ".join([python_exe, python_script] + sys.argv[2:11] + [workspace])
cmd += "\npause\n"

with open(bat_path, "w") as f:
    f.write("@echo off\n")
    f.write(cmd)

arcpy.AddMessage(f"To run circuity analysis, run the .bat file found at {bat_path}")