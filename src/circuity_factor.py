########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Finds the road circuity factor from between road distance and straight-line distance from harvest sites to
#          sawmills.
########################################################################################################################

import sys, arcpy, csv, os, random
import distance_calculator
import statsmodels.api as sm
import numpy as np
import pandas as pd

workspace = sys.argv[1]
network_dataset = sys.argv[2]
sawmills = sys.argv[3]
harvest_sites = sys.argv[4]
output_dir = sys.argv[5]
pairs_per_type = int(sys.argv[6])
keep_output_paths = sys.argv[7]
if keep_output_paths.lower() == "true":
    keep_output_paths = True
else:
    keep_output_paths = False
sawmill_type = None
if len(sys.argv) == 9 and sys.argv[8] != "#":
    sawmill_type = sys.argv[8]

#set workspace
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True

#convert harvest sites to points if given as polygons
desc = arcpy.Describe(harvest_sites)
if desc.shapeType == "Polygon":
    if arcpy.Exists("hs_points"):
        arcpy.management.Delete("hs_points")
    arcpy.management.FeatureToPoint(harvest_sites, "hs_points", "INSIDE")
    harvest_sites = "hs_points"
elif desc.shapeType != "Point":
    raise arcpy.ExecuteError("Invalid harvest site: site must be polygon or point")

#create list for sawmill types
sm_types = [
    "Lumber/Solid Wood", "Pellet", "Chip", "Pulp/Paper", "Composite Panel/Engineered Wood Product", "Plywood/Veneer"
]

#dict to store straight line distance and ids
dist_id_dict = {
    "Lumber/Solid Wood": {},
    "Pellet": {},
    "Chip": {},
    "Pulp/Paper":{},
    "Composite Panel/Engineered Wood Product": {},
    "Plywood/Veneer": {}
}

#if a specific type is selected, then all other types are removed from the list
if sawmill_type:
    sm_types = [sawmill_type]
    dist_id_dict = {sawmill_type: {}}

#output file for distance results so the full script doesn't have to run every time
output_file = open(os.path.join(output_dir, "distances.csv"), "w+", newline="\n")
output_writer = csv.writer(output_file)

#calculate the distance for every harvest site to every type of sawmill
arcpy.AddMessage("Starting Straight Line Distance Calculations")
sc = arcpy.da.SearchCursor(harvest_sites, ["OBJECTID"])
arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
for row in sc:
    arcpy.management.SelectLayerByAttribute(
        "harvest_site_layer", "NEW_SELECTION", f"OBJECTID = {row[0]}"
    )
    arcpy.analysis.Near(
        sawmills,"harvest_site_layer", "120 Miles", method="PLANAR", distance_unit = "Miles"
    )
    arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
    for sm_type in sm_types:
        #sort by mill type and ensure distance is valid
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            f"Mill_Type = '{sm_type}' AND NEAR_DIST >= 0"
        )
        #get lowest straight line distance and id of nearest sawmill
        sc2 = arcpy.da.SearchCursor(
            "sawmill_layer",
            ["OBJECTID", "NEAR_DIST", "Mill_Type"],
            sql_clause=(None, "ORDER BY NEAR_DIST ASC")
        )
        for n_fid, n_dist, m_type in sc2:
            dist_id_dict[sm_type][row[0]] = (n_fid, n_dist)
            break
        del sc2

    print(f"{row[0]} distances completed")
    arcpy.management.Delete("sawmill_layer")
arcpy.management.Delete("harvest_site_layer")

#lists to store road and Euclidean distance
rd_list = []
ed_list = []

#select m number of random ids from each of the type's lists
#calculate the road distance for each of the ids and sawmill id pairs
#add to rd_list and ed_list, as well as write out to a csv file
arcpy.AddMessage("Starting Road Distance Calculations")
arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
for sm_type in dist_id_dict:
    oid_list = list(dist_id_dict[sm_type].keys())
    rand_id_list = random.sample(oid_list, pairs_per_type)
    remaining_ids = list(set(oid_list) - set(rand_id_list))
    for rand_id in rand_id_list:
        road_dist = None
        id_to_try = rand_id
        while not road_dist:
            try:
                arcpy.management.SelectLayerByAttribute(
                    "harvest_site_layer", "NEW_SELECTION", f"OBJECTID = {id_to_try}"
                )
                arcpy.management.SelectLayerByAttribute(
                    "sawmill_layer",
                    "NEW_SELECTION",
                    f"OBJECTID = {dist_id_dict[sm_type][id_to_try][0]}"
                )
                out_path = os.path.join(output_dir, f"path_{sm_type[:3]}_{id_to_try}.shp")
                road_dist = distance_calculator.calculate_route_distance(
                    "harvest_site_layer", network_dataset, "sawmill_layer", out_path
                )
                rd_list.append(road_dist)
                ed_list.append(dist_id_dict[sm_type][id_to_try][1])
                if not keep_output_paths:
                    arcpy.management.Delete(out_path)
                output_writer.writerow(
                    [id_to_try,
                     dist_id_dict[sm_type][id_to_try][0],
                     dist_id_dict[sm_type][id_to_try][1],
                     road_dist]
                )
            except arcpy.ExecuteError as e:
                arcpy.AddWarning(f"{sm_type}:{id_to_try},{dist_id_dict[sm_type][id_to_try][0]} failed: {str(e)}")
                if remaining_ids:
                    id_to_try = random.choice(remaining_ids)
                    remaining_ids.remove(id_to_try)
                    arcpy.AddWarning(f"Attempting new ID: {id_to_try}, {dist_id_dict[sm_type][id_to_try][0]}")
                    road_dist = None
                else:
                    arcpy.AddWarning("No more IDs to try, skipping this distance calculation")
                    road_dist = 1
        if id_to_try != rand_id:
            arcpy.AddMessage(f"New ID ({id_to_try}) successful")

    print(f"{sm_type} road distance completed")

#close csv file and delete temporary layers, feature classes, and solvers
output_file.close()
arcpy.management.Delete("harvest_site_layer")
arcpy.management.Delete("sawmill_layer")
arcpy.management.Delete("hs_points")
for name in arcpy.ListDatasets("*Solver*"):
    arcpy.management.Delete(name)

#optional code if it is desired to reuse previously calculated data
# input_file = open(os.path.join(output_dir, "distances.csv"), "r", newline="\n")
# input_reader = csv.reader(input_file)
# for row in input_reader:
#     ed_list.append(float(row[2]))
#     rd_list.append(float(row[3]))
# input_file.close()

#convert lists to arrays
arcpy.AddMessage("Starting OLS regression")
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
print(model1.summary())
print()

X2 = sm.add_constant(df[['sl']])
model2 = sm.OLS(y, X2).fit()
print(model2.summary())
print()

X3 = df[['sl']]
model3 = sm.OLS(y, X3).fit()
print(model3.summary())
print()

b1 = model3.params['sl']
print(b1)
arcpy.AddMessage(f"Circuity Factor: {b1}")

#print output and write to text file
results_file = open(os.path.join(output_dir, "OLS_results.txt"), "w+")
results_file.write(str(model1.summary()) + "\n")
results_file.write(str(model2.summary()) + "\n")
results_file.write(str(model3.summary()) + "\n")
results_file.write(f"Circuity factor: {b1}")
results_file.close()
