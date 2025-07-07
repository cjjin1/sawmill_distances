########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Finds the road circuity factor given a list of harvest sites
########################################################################################################################

import sys, arcpy, csv, os
import distance_calculator
import statsmodels.api as sm
import numpy as np
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

#runs the calculate_distance() function for every harvest site
print("starting distance calculations at: ", datetime.now())
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
        rd_list.append(dist)
        ed_list.append(euclidean_dist)
        output_writer.writerow([oid, dist, euclidean_dist])
    except arcpy.ExecuteError as e:
        print(f"Harvest site {oid} could not find a path to a sawmill: {e}")
        output_writer.writerow([oid, "n/a", "n/a"])
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

#create an array of Euclidean distance squared
euclidean_dist_sq = euclidean_distance ** 2

#ordinary least squares regression
X = np.column_stack((euclidean_distance, euclidean_dist_sq))
X = sm.add_constant(X)
model = sm.OLS(road_distance, X).fit()

#print output and write to text file
print(model.summary())
results_file = open(os.path.join(output_dir, "OLS_results.txt"), "w+")
results_file.write(str(model.summary()))
results_file.close()

