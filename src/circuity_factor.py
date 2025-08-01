########################################################################################################################
# circuity_factor.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Finds the road circuity factor from between road distance and straight-line distance from harvest sites to
#          sawmills.
########################################################################################################################

import sys, arcpy, csv, os, random, time, gc
import distance_calculator as dc
import statsmodels.api as sm
import numpy as np
import pandas as pd
import datetime

sl_dist_csv = sys.argv[1]
output_dir = sys.argv[2]
network_dataset = sys.argv[3]
sawmills = sys.argv[4]
harvest_sites = sys.argv[5]
pairs_per_type = int(sys.argv[6])
single_sawmill_type = sys.argv[7]
keep_output_paths = sys.argv[8]
calculate_road_distances = sys.argv[9]

#set string inputs to proper boolean values
if keep_output_paths.lower() == "true":
    keep_output_paths = True
else:
    keep_output_paths = False
if calculate_road_distances.lower() == "true":
    calculate_road_distances = True
else:
    calculate_road_distances = False

#check if calculate_road_distances and output_dir are valid
if not calculate_road_distances and output_dir == "#":
    raise arcpy.ExecuteError("An directory input is required if road distances are not to be calculated.")

#convert harvest sites to points if given as polygons
desc = arcpy.Describe(harvest_sites)
if desc.shapeType == "Polygon":
    if arcpy.Exists("hs_points"):
        arcpy.management.Delete("hs_points")
    arcpy.management.FeatureToPoint(harvest_sites, "hs_points", "INSIDE")
    harvest_sites = "hs_points"
elif desc.shapeType != "Point":
    raise arcpy.ExecuteError("Invalid harvest site: site must be polygon or point")

#set workspace
try:
    proj = arcpy.mp.ArcGISProject("CURRENT")
    workspace = proj.defaultGeodatabase
except OSError:
    workspace = sys.argv[10]
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True
arcpy.env.addOutputsToMap = False

#Setup output directory
if output_dir != "#":
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
else:
    output_dir = workspace + "/../" + f"outputs/circuity_factor_{datetime.datetime.now().strftime('%m%d_%H%M')}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_dir = os.path.abspath(output_dir)

# convert harvest sites to points if given as polygons
desc = arcpy.Describe(harvest_sites)
if desc.shapeType == "Polygon":
    if arcpy.Exists("hs_points"):
        arcpy.management.Delete("hs_points")
    arcpy.management.FeatureToPoint(harvest_sites, "hs_points", "INSIDE")
    harvest_sites = "hs_points"
elif desc.shapeType != "Point":
    raise arcpy.ExecuteError("Invalid harvest site: site must be polygon or point")

# dict to store straight line distance and ids
dist_id_dict = {
    "Lumber/Solid Wood": {},
    "Pellet": {},
    "Chip": {},
    "Pulp/Paper": {},
    "Composite Panel/Engineered Wood Product": {},
    "Plywood/Veneer": {}
}

# dictionary to store multipliers
multi_dict = {
    "Lumber/Solid Wood": [],
    "Pellet": [],
    "Chip": [],
    "Pulp/Paper": [],
    "Composite Panel/Engineered Wood Product": [],
    "Plywood/Veneer": []
}

#read in straight line distances
dc.read_sl_distance_csv(sl_dist_csv, dist_id_dict)

#remove all other sawmill types from dictionaries
if single_sawmill_type != "All":
    temp_dict = dist_id_dict[single_sawmill_type]
    dist_id_dict = {single_sawmill_type: temp_dict}
    multi_dict = {single_sawmill_type: []}

# Z-score and margin of error values
z = 1.96
E = 0.1

if calculate_road_distances:
    arcpy.AddMessage("Starting Road Distance Calculations")
    for sm_type in dist_id_dict:
        arcpy.AddMessage(f"Starting Calculations for {sm_type}")
        # output file for distance results so the full script doesn't have to run every time
        csv_out = os.path.join(output_dir, f"{sm_type[:3]}_distance.csv")
        output_file = open(csv_out, "w+", newline="\n")
        output_writer = csv.writer(output_file)

        oid_list = list(dist_id_dict[sm_type].keys())
        rand_id_list = random.sample(oid_list, len(oid_list))
        sample_size = pairs_per_type
        count = 0
        for i, rand_id in enumerate(rand_id_list):
            if count == pairs_per_type:
                #calculate new sample size based on first pairs_per_type number of samples
                #if less than originally set sample size
                std_dev = np.std(multi_dict[sm_type])
                n = (z ** 2 * float(std_dev) ** 2) / E ** 2
                n = round(n)
                if n > sample_size:
                    sample_size = n
                    arcpy.AddMessage(f"Calculated sample size for {sm_type} is greater than {pairs_per_type}.")
                    arcpy.AddMessage(f"New sample size for {sm_type} is {n}.")
            if count == sample_size:
                break
            try:
                #calculate route distance between harvest site and sawmill
                #store results in dictionary and CSV file
                time.sleep(0.5)
                gc.collect()
                arcpy.management.MakeFeatureLayer(harvest_sites, f"harvest_site_{rand_id}")
                arcpy.management.MakeFeatureLayer(sawmills, f"sawmill_layer_{rand_id}")
                arcpy.management.SelectLayerByAttribute(
                    f"harvest_site_{rand_id}",
                    "NEW_SELECTION",
                    f"OBJECTID = {rand_id}"
                )
                arcpy.management.SelectLayerByAttribute(
                    f"sawmill_layer_{rand_id}",
                    "NEW_SELECTION",
                    f"OBJECTID = {dist_id_dict[sm_type][rand_id][0]}"
                )
                out_path = os.path.join(arcpy.env.workspace, f"path_{sm_type[:3]}_{rand_id}")
                road_dist = dc.calculate_route_distance(
                    f"harvest_site_{rand_id}",
                    network_dataset,
                    f"sawmill_layer_{rand_id}",
                    out_path
                )
                time.sleep(0.25)
                gc.collect()
                if not keep_output_paths:
                    arcpy.management.Delete(out_path)
                if road_dist == 0:
                    raise arcpy.ExecuteError("Solve resulted in failure")
                output_writer.writerow(
                    [rand_id,
                    dist_id_dict[sm_type][rand_id][0],
                    dist_id_dict[sm_type][rand_id][1],
                    road_dist]
                )
                multiplier = road_dist / float(dist_id_dict[sm_type][rand_id][1])
                multi_dict[sm_type].append(multiplier)
            except arcpy.ExecuteError as e:
                arcpy.AddWarning(f"{sm_type}:{rand_id},{dist_id_dict[sm_type][rand_id][0]} failed: {str(e)}")
                if i < len(rand_id_list) - 1:
                    arcpy.AddMessage(
                        f"Attempting new ID: {rand_id_list[i + 1]}, {dist_id_dict[sm_type][rand_id_list[i + 1]][0]}"
                    )
                    continue
                else:
                    arcpy.AddWarning("No more IDs to try, skipping this distance calculation")
                    break
            finally:
                # delete temporary layers, feature classes, and solvers
                arcpy.management.Delete(f"harvest_site_{rand_id}")
                arcpy.management.Delete(f"sawmill_layer_{rand_id}")
                for name in arcpy.ListDatasets("*Solver*"):
                    arcpy.management.Delete(name)
                time.sleep(0.25)
                gc.collect()
                arcpy.management.ClearWorkspaceCache()
            count += 1
            if count % 5 == 0:
                arcpy.AddMessage(f"{count} calculations done for {sm_type}.")
        arcpy.AddMessage(f"{sm_type} calculations have been completed. Sample size has been set to {sample_size}.")
        output_file.close()
else:
    arcpy.AddMessage(f"Reading existing road distance csv files: {os.path.abspath(output_dir)}")

rd_list = []
ed_list = []

#find circuity factor for individual sawmill types
for sm_type in multi_dict:
    csv_in = os.path.join(output_dir, f"{sm_type[:3]}_distance.csv")
    input_file = open(csv_in, "r", newline="\n")
    in_reader = csv.reader(input_file)
    for row in in_reader:
        rd_list.append(float(row[3]))
        ed_list.append(float(row[2]))
    input_file.close()
    dc.calculate_circuity_factor_from_csv(csv_in, f"{sm_type[:3]}_circuity_factor.txt", output_dir)

#find circuity factor for all sawmill types combined
if single_sawmill_type == "All":
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
    arcpy.AddMessage(f"Circuity Factor for all types: {b1}")

    results_file = open(os.path.join(output_dir, "circuity_factor_all.txt"), "w+")
    results_file.write(str(model1.summary()) + "\n")
    results_file.write(str(model2.summary()) + "\n")
    results_file.write(str(model3.summary()) + "\n")
    results_file.write(f"Circuity factor: {b1}")
    results_file.close()