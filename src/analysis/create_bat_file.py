########################################################################################################################
# create_bat_file.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Simple script that constructs a .bat file that can be used to run the cf_all_sites.py script.
########################################################################################################################

import arcpy, sys, os

python_exe = os.path.join(sys.base_prefix, "python.exe")

bat_path = sys.argv[1]
sampling = sys.argv[2]
if sampling.lower() == "true":
    params = sys.argv[3:8] + ["30"] + sys.argv[8:12]
    python_script = os.path.join(os.path.dirname(__file__), "circuity_factor.py")
else:
    params = sys.argv[3:12]
    python_script = os.path.join(os.path.dirname(__file__), "cf_all_sites.py")

try:
    proj = arcpy.mp.ArcGISProject("CURRENT")
    workspace = proj.defaultGeodatabase
except OSError:
    workspace = sys.argv[12]

cmd = ["\"" + path + "\"" for path in [python_exe, python_script] + params + [workspace]]
cmd = " ".join(cmd)
cmd += "\npause\n"

with open(bat_path, "w") as f:
    f.write("@echo off\n")
    f.write(cmd)

arcpy.AddMessage(f"To run circuity analysis, run the .bat file found at {bat_path}")