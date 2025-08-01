########################################################################################################################
# bootstrap_analysis.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Repeatedly samples using bootstrapping to collect multiplier data, produces a circuity factor
########################################################################################################################

import sys, arcpy, csv, os, random
import datetime

output_dir = sys.argv[1]

#set workspace
try:
    proj = arcpy.mp.ArcGISProject("CURRENT")
    workspace = proj.defaultGeodatabase
except OSError:
    workspace = sys.argv[2]
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True
arcpy.env.addOutputsToMap = False

#Setup output directory
if output_dir != "#":
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
else:
    output_dir = workspace + "/../" + f"outputs/bootstrap_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_dir = os.path.abspath(output_dir)

# dictionary to store multipliers
rd_dict = {
    "Lumber/Solid Wood": [],
    "Pellet": [],
    "Chip": [],
    "Pulp/Paper": [],
    "Composite Panel/Engineered Wood Product": [],
    "Plywood/Veneer": []
}

#read in distance calculations from CSV
for sm_type in rd_dict:
    csv_in = os.path.join(output_dir, f"{sm_type[:3]}_distance.csv")
    try:
        rd_in = open(csv_in, "r", newline="\n")
    except FileNotFoundError:
        arcpy.AddError("Road distance csv files not found, rerun Circuity Factor script tool with calculations.")
        raise arcpy.ExecuteError()
    rd_reader = csv.reader(rd_in)
    for row in rd_reader:
        multiplier = float(row[3]) / float(row[2])
        rd_dict[sm_type].append(multiplier)
    rd_in.close()

#resample from the calculated distances, output mean multiplier of each resample to CSV file
mean_multipliers_out = os.path.join(os.path.abspath(output_dir), "mean_multipliers.csv")
csv_out = open(mean_multipliers_out, "w", newline="\n")
csv_writer = csv.writer(csv_out)
csv_writer.writerow(["Lumber/Solid Wood", "Pellet", "Chip", "Pulp/Paper", "Composite Panel/Engineered Wood Product",
                     "Plywood/Veneer", "Combined Average"])

for i in range(0, 10000):
    total_multiplier_list = []
    output_dict = {}
    for sm_type in rd_dict:
        random_sample = random.choices(rd_dict[sm_type], k=len(rd_dict[sm_type]))
        sample_mean = sum(random_sample) / len(rd_dict[sm_type])
        output_dict[sm_type] = sample_mean
        total_multiplier_list.extend(random_sample)
    total_sample_mean = sum(total_multiplier_list) / len(total_multiplier_list)
    csv_writer.writerow([output_dict["Lumber/Solid Wood"],
                         output_dict["Pellet"],
                         output_dict["Chip"],
                         output_dict["Pulp/Paper"],
                         output_dict["Composite Panel/Engineered Wood Product"],
                         output_dict["Plywood/Veneer"],
                         total_sample_mean]
    )
csv_out.close()

arcpy.AddMessage(f"Results can be found in {output_dir}")