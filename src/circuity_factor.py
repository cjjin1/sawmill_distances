########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Finds the road circuity factor from between road distance and straightline distance from harvest sites to
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
pairs_per_bucket = int(sys.argv[6])
keep_output_paths = sys.argv[7]
if keep_output_paths.lower() == "true":
    keep_output_paths = True
else:
    keep_output_paths = False
sawmill_bucket = None
if len(sys.argv) == 9 and sys.argv[8] != "#":
    sawmill_bucket = sys.argv[8]

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


#create dictionary for sawmill type buckets
sm_type_buckets = {
    "lumber":["lumber"],
    "pellet":["pellet"],
    "chip":["chip"],
    "pulp/paper":["pulp/paper"],
    "plywood/veneer":["plywood/veneer", "panel"],
    "composite board":["OSB", "mass timber", "EWP"]
}

#if a specific bucket is selected, then all other buckets are removed from the dictionary
if sawmill_bucket:
    sawmill_bucket_list = sm_type_buckets[sawmill_bucket]
    sm_type_buckets = {
        sawmill_bucket: sawmill_bucket_list
    }

#dict to store straight line distance and ids
dist_id_dict = {
    "lumber": {},
    "pellet": {},
    "chip": {},
    "pulp/paper":{},
    "plywood/veneer": {},
    "composite board": {}
}

# #output file for distance results so the full script doesn't have to run every time
output_file = open(os.path.join(output_dir, "distances.csv"), "w+", newline="\n")
output_writer = csv.writer(output_file)

#calculate the distance for every harvest site to every type of sawmill
sc = arcpy.da.SearchCursor(harvest_sites, ["OBJECTID"])
arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
for row in sc:
    arcpy.management.SelectLayerByAttribute(
        "harvest_site_layer", "NEW_SELECTION", f"OBJECTID = {row[0]}"
    )
    arcpy.analysis.Near(
        sawmills,
        "harvest_site_layer", "120 Miles", method="GEODESIC", distance_unit = "Miles"
    )
    arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
    for sm_bucket in sm_type_buckets:
        #sort by mill type and ensure distance is valid
        mill_types = sm_type_buckets[sm_bucket]
        conditions = [f"Mill_Type = '{t}'" for t in mill_types]
        where_clause = "(" + " OR ".join(conditions) + ") AND NEAR_DIST > 0"
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            where_clause
        )
        #get lowest straight line distance and id of nearest sawmill
        sc2 = arcpy.da.SearchCursor(
            "sawmill_layer", ["OBJECTID", "NEAR_DIST", "Mill_Type"], sql_clause=(None, "ORDER BY NEAR_DIST ASC")
        )
        for n_fid, n_dist, m_type in sc2:
            dist_id_dict[sm_bucket][row[0]] = (n_fid, n_dist)
            break
        del sc2

    print(f"{row[0]} distances completed")
    arcpy.management.Delete("sawmill_layer")
arcpy.management.Delete("harvest_site_layer")

#lists to store road and Euclidean distance
rd_list = []
ed_list = []

#select m number of random ids from each of the bucket's lists
#calculate the road distance for each of the ids and sawmill id pairs
#add to rd_list and ed_list, as well as write out to a csv file
arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
for sm_bucket in dist_id_dict:
    oid_list = list(dist_id_dict[sm_bucket].keys())
    rand_id_list = random.sample(oid_list, pairs_per_bucket)
    for rand_id in rand_id_list:
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", f"OBJECTID = {rand_id}"
        )
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            f"OBJECTID = {dist_id_dict[sm_bucket][rand_id][0]}"
        )
        out_path = os.path.join(output_dir, f"path_{sm_bucket[:3]}_{rand_id}.shp")
        distance_calculator.calculate_road_distance_nd(
            "harvest_site_layer", network_dataset, "sawmill_layer", out_path
        )
        try:
            road_dist = distance_calculator.calculate_distance_for_fc(out_path)
        except arcpy.ExecuteError:
            print(f"{sm_bucket}:{rand_id},{dist_id_dict[sm_bucket][rand_id][0]} failed")
            road_dist = "n/a"
        rd_list.append(road_dist)
        ed_list.append(dist_id_dict[sm_bucket][rand_id][1])
        if not keep_output_paths:
            arcpy.management.Delete(out_path)
        output_writer.writerow(
            [rand_id,
             dist_id_dict[sm_bucket][rand_id][0],
             dist_id_dict[sm_bucket][rand_id][1],
             road_dist]
        )
    print(f"{sm_bucket} road distance completed")

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

#convert lists to arrays
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

#print output and write to text file
results_file = open(os.path.join(output_dir, "OLS_results.txt"), "w+")
results_file.write(str(model1.summary()) + "\n")
results_file.write(str(model2.summary()) + "\n")
results_file.write(str(model3.summary()) + "\n")
results_file.write(f"Circuity factor: {b1}")
results_file.close()
