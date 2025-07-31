########################################################################################################################
# bootstrap_analysis.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Repeatedly samples using bootstrapping to collect multiplier data, produces a circuity factor
########################################################################################################################

import sys, arcpy, csv, os, random
import distance_calculator as dc
import datetime
import statsmodels.api as sm
import numpy as np
import pandas as pd

sample_size_csv = sys.argv[1]
sl_dist_csv = sys.argv[2]
output_dir = sys.argv[3]
network_dataset = sys.argv[4]
sawmills = sys.argv[5]
harvest_sites = sys.argv[6]
keep_output_paths = sys.argv[7]
calculate_road_distances = sys.argv[8]
if keep_output_paths.lower() == "true":
    keep_output_paths = True
else:
    keep_output_paths = False

if calculate_road_distances.lower() == "true":
    calculate_road_distances = True
else:
    calculate_road_distances = False

if not calculate_road_distances and output_dir == "":
    raise arcpy.ExecuteError("An directory input is required if road distances are not to be calculated.")

try:
    proj = arcpy.mp.ArcGISProject("CURRENT")
    workspace = proj.defaultGeodatabase
except OSError:
    workspace = sys.argv[9]

arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True

#read in sample sizes
ss_dict = {}
ss_in = open(sample_size_csv, "r", newline="\n")
csv_reader = csv.reader(ss_in)
for row in csv_reader:
    ss_dict[row[0]] = row[1]
ss_in.close()

#dict to store straight line distance and ids
dist_id_dict = {
    "Lumber/Solid Wood": {},
    "Pellet": {},
    "Chip": {},
    "Pulp/Paper": {},
    "Composite Panel/Engineered Wood Product": {},
    "Plywood/Veneer": {}
}

#Setup output directory
if output_dir != "#":
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
else:
    output_dir = workspace + "/../" + f"outputs/bootstrap_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_dir = os.path.abspath(output_dir)

#read in straight line distances then calculate road distances using read in sample sizes
dc.read_sl_distance_csv(sl_dist_csv, dist_id_dict)
if calculate_road_distances:
    dc.calculate_road_distances(
        dist_id_dict, ss_dict, output_dir, harvest_sites, sawmills, network_dataset, keep_output_paths
    )

# dictionary to store multipliers
rd_dict = {
    "Lumber/Solid Wood": [],
    "Pellet": [],
    "Chip": [],
    "Pulp/Paper": [],
    "Composite Panel/Engineered Wood Product": [],
    "Plywood/Veneer": []
}

for sm_type in rd_dict:
    csv_in = os.path.join(output_dir, f"{sm_type[:3]}_distance.csv")
    try:
        rd_in = open(csv_in, "r", newline="\n")
    except FileNotFoundError:
        arcpy.AddError("Road distance csv files not found, rerun script tool with calculations.")
        raise arcpy.ExecuteError()
    rd_reader = csv.reader(rd_in)
    for row in rd_reader:
        multiplier = float(row[3]) / float(row[2])
        rd_dict[sm_type].append((multiplier, row[3], row[2]))
    rd_in.close()

mean_multipliers_out = os.path.join(os.path.abspath(output_dir), "mean_multipliers.csv")
csv_out = open(mean_multipliers_out, "w", newline="\n")
csv_writer = csv.writer(csv_out)

rd_list = []
ed_list = []

for i in range(0, 10000):
    total_multiplier_list = []
    for sm_type in rd_dict:
        random_sample = random.choices(rd_dict[sm_type], k=len(rd_dict[sm_type]))
        multiplier_list = [float(t[0]) for t in random_sample]
        rd_sample_list = [float(t[1]) for t in random_sample]
        ed_sample_list = [float(t[2]) for t in random_sample]
        total_multiplier_list.extend(multiplier_list)
        rd_list.extend(rd_sample_list)
        ed_list.extend(ed_sample_list)
    sample_mean = sum(total_multiplier_list) / len(total_multiplier_list)
    csv_writer.writerow([sample_mean])
csv_out.close()

arcpy.AddMessage(f"Results can be found in {output_dir}")

road_distance = np.array(rd_list)
euclidean_distance = np.array(ed_list)

df = pd.DataFrame({
    'sl': euclidean_distance,
    'sl_sq': euclidean_distance ** 2,
    'rd': road_distance
})

X1 = sm.add_constant(df[['sl', 'sl_sq']])
y = df['rd']

model1 = sm.OLS(y, X1).fit()

X2 = sm.add_constant(df[['sl']])
model2 = sm.OLS(y, X2).fit()

X3 = df[['sl']]
model3 = sm.OLS(y, X3).fit()

b1 = model3.params['sl']
arcpy.AddMessage(f"Circuity Factor: {b1}")

results_file = open(os.path.join(output_dir, "circuity_factor.txt"), "w+")
results_file.write(str(model1.summary()) + "\n")
results_file.write(str(model2.summary()) + "\n")
results_file.write(str(model3.summary()) + "\n")
results_file.write(f"Circuity factor: {b1}")
results_file.close()
