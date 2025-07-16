########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Finds the road circuity factor given a list of harvest sites
########################################################################################################################

import sys, arcpy, csv, os, random
import distance_calculator
import statsmodels.api as sm
import numpy as np
import pandas as pd
from datetime import datetime

#read in inputs
workspace = sys.argv[1]
input_csv = sys.argv[2]
network_dataset = sys.argv[3]
roads_dataset = sys.argv[4]
sawmills = sys.argv[5]
harvest_sites = sys.argv[6]
slope_raster = sys.argv[7]
ofa = sys.argv[8]
output_dir = sys.argv[9]
try:
    simplify = sys.argv[10]
except IndexError:
    simplify = "NO_SIMPLIFY"

#set workspace
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True

#read harvest site csv file and store in a dictionary
#csv file should contain harvest site object id and desired sawmill type
hs_dict = {}
csv_file = open(input_csv, "r", newline="\n")
reader = csv.reader(csv_file)
for row in reader:
    hs_dict[int(row[0])] = row[1]
csv_file.close()

#lists to store road and Euclidean distance
rd_list = []
ed_list = []

#output file for distance results so the full script doesn't have to run every time
output_file = open(os.path.join(output_dir, "distances.csv"), "w+", newline="\n")
output_writer = csv.writer(output_file)

#get list of harvest site IDs from harvest site feature class
id_list = []
sc = arcpy.da.SearchCursor(harvest_sites, ["OBJECTID"])
for row in sc:
    id_list.append(row[0])

#runs the calculate_distance() function for every harvest site
print("starting distance calculations at: ", datetime.now())
count = 0
for oid in hs_dict:
    #selects harvest site using object id
    arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
    arcpy.management.SelectLayerByAttribute(
        "harvest_site_layer", "NEW_SELECTION", f"OBJECTID = {oid}"
    )
    output_path = os.path.join(output_dir, f"path_{oid}.shp")
    #attempts to run distance calculation, appends both distance results to their respective lists
    #if an error is encountered, the script still completes with whatever results exist
    try:
        if simplify == "simplify":
            dist, euclidean_dist = distance_calculator.calculate_road_dist_only(
                "harvest_site_layer",
                network_dataset,
                sawmills,
                output_path,
                hs_dict[oid]
            )
        else:
            dist, euclidean_dist = distance_calculator.calculate_distance(
                "harvest_site_layer",
                roads_dataset,
                network_dataset,
                sawmills,
                slope_raster,
                ofa,
                output_path,
                hs_dict[oid]
            )

        #if the distance ends up being greater than 120 miles, a new object ID is obtained that isn't already being used
        #the loop continues until a path less than 120 miles is found or if a 10 calculation is reached
        #at this point, it is assumed that there are no possible paths less than 120 miles and the script is stopped
        c = 0
        while dist > 120:
            rand_id = random.randint(1, len(id_list))
            while rand_id in hs_dict:
                rand_id = random.randint(1, len(id_list))
            arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
            arcpy.management.SelectLayerByAttribute(
                "harvest_site_layer", "NEW_SELECTION", f"OBJECTID = {rand_id}"
            )
            output_path = os.path.join(output_dir, f"path_{oid}.shp")
            if simplify == "simplify":
                dist, euclidean_dist = distance_calculator.calculate_road_dist_only(
                    "harvest_site_layer",
                    network_dataset,
                    sawmills,
                    output_path,
                    hs_dict[oid]
                )
            else:
                dist, euclidean_dist = distance_calculator.calculate_distance(
                    "harvest_site_layer",
                    roads_dataset,
                    network_dataset,
                    sawmills,
                    slope_raster,
                    ofa,
                    output_path,
                    hs_dict[oid]
                )
            if c > 10:
                raise arcpy.ExecuteError("Too many harvest sites 120 miles away from sawmills")
            c += 1

        rd_list.append(dist)
        ed_list.append(euclidean_dist)
        output_writer.writerow([oid, dist, euclidean_dist])
    except arcpy.ExecuteError as e:
        print(f"Harvest site {oid} could not find a path to a sawmill: {e}")
        if e == "Too many harvest sites 120 miles away from sawmills":
            exit(1)
        output_writer.writerow([oid, "n/a", "n/a"])
    print(f"({count}) Calculated distance for {oid}")
    count += 1
    arcpy.management.Delete("harvest_site_layer")
print("finished distance calculations at: ", datetime.now())
output_file.close()

#checks if either list of distances are of length 0
if len(rd_list) == 0 or len(ed_list) == 0:
    raise arcpy.ExecuteError("No sawmills found for any harvest site, check input data")

#alternate code to be run if distances have already been calculated
# csv_file = open(os.path.join(output_dir, "distances.csv"), "r", newline="\n")
# reader = csv.reader(csv_file)
# for row in reader:
#     rd_list.append(float(row[1]))
#     ed_list.append(float(row[2]))
# csv_file.close()

#convert lists to arrays
road_distance = np.array(rd_list)
euclidean_distance = np.array(ed_list)

df = pd.DataFrame({
    'sl': euclidean_distance,
    'sl_sq': euclidean_distance ** 2,
    'rd': road_distance
})

X1 = sm.add_constant(df[['sl', 'sl_sq']])  # includes intercept
y = df['rd']

model1 = sm.OLS(y, X1).fit()
print(model1.summary())
print()

X2 = sm.add_constant(df[['sl']])
model2 = sm.OLS(y, X2).fit()
print(model2.summary())
print()

X3 = df[['sl']]  # No constant (intercept)
model3 = sm.OLS(y, X3).fit()
print(model3.summary())
print()

b1 = model3.params['sl']
print(b1)

#print output and write to text file
results_file = open(os.path.join(output_dir, "OLS_results.txt"), "w+")
results_file.write(str(model1.summary()) + "\n")
results_file.write(str(model2.summary()) + "\n")
results_file.write(str(model3.summary()) + "\n")
results_file.write(f"Circuity factor: {b1}")
results_file.close()

