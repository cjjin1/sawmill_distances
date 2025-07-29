########################################################################################################################
# circuity_factor_modular.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Finds the road circuity factor from between road distance and straight-line distance from harvest sites to
#          sawmills. Made into multiple methods for modularity purposes.
########################################################################################################################

import sys, arcpy, csv, os, random
import distance_calculator
import statsmodels.api as sm
import numpy as np
import pandas as pd

def calculate_sl_distances(hv_sites, sawmill_data, sm_ts, di_dict, op_dir):
    """Calculates straight line distance from every harvest site to every sawmill for every sawmill type"""
    csv_sl_out = os.path.join(op_dir, "sl_distances.csv")
    sl_out = open(csv_sl_out, "w+", newline="\n")
    sl_writer = csv.writer(sl_out)

    # calculate the distance for every harvest site to every type of sawmill
    arcpy.AddMessage("Starting Straight Line Distance Calculations")
    sc = arcpy.da.SearchCursor(hv_sites, ["OBJECTID"])
    arcpy.management.MakeFeatureLayer(hv_sites, "harvest_site_layer")
    for row in sc:
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", f"OBJECTID = {row[0]}"
        )
        arcpy.analysis.Near(
            sawmills, "harvest_site_layer", "120 Miles", method="PLANAR", distance_unit="Miles"
        )
        arcpy.management.MakeFeatureLayer(sawmill_data, "sawmill_layer")
        for sm_t in sm_ts:
            # sort by mill type and ensure distance is valid
            arcpy.management.SelectLayerByAttribute(
                "sawmill_layer",
                "NEW_SELECTION",
                f"Mill_Type = '{sm_t}' AND NEAR_DIST >= 0"
            )
            # get lowest straight line distance and id of nearest sawmill
            sc2 = arcpy.da.SearchCursor(
                "sawmill_layer",
                ["OBJECTID", "NEAR_DIST", "Mill_Type"],
                sql_clause=(None, "ORDER BY NEAR_DIST ASC")
            )
            for n_fid, n_dist, m_type in sc2:
                di_dict[sm_t][row[0]] = (n_fid, n_dist)
                sl_writer.writerow([sm_t, row[0], n_fid, n_dist])
                break
            del sc2

        print(f"{row[0]} distances completed")
        arcpy.management.Delete("sawmill_layer")
    arcpy.management.Delete("harvest_site_layer")
    sl_out.close()

def read_sl_distance_csv(sl_csv, di_dict):
    """Reads in from straight line distance csv file"""
    sl_in = open(sl_csv, "r", newline="\n")
    sl_reader = csv.reader(sl_in)
    for row in sl_reader:
        di_dict[row[0]][row[1]] = (row[2], row[3])
    sl_in.close()

def calculate_road_distance_all(di_dict, ppt, op_dir, hs_sites, sm_data, nw_ds):
    """Calculates circuity factor with every sawmill type"""
    # output file for distance results so the full script doesn't have to run every time
    output_file = open(os.path.join(op_dir, "distances.csv"), "w+", newline="\n")
    output_writer = csv.writer(output_file)

    # select m number of random ids from each of the type's lists
    # calculate the road distance for each of the ids and sawmill id pairs
    # add to rd_list and ed_list, as well as write out to a csv file
    arcpy.AddMessage("Starting Road Distance Calculations")
    arcpy.management.MakeFeatureLayer(hs_sites, "harvest_site_layer")
    arcpy.management.MakeFeatureLayer(sm_data, "sawmill_layer")
    for sm_type in di_dict:
        oid_list = list(dist_id_dict[sm_type].keys())
        rand_id_list = random.sample(oid_list, ppt)
        remaining_ids = list(set(oid_list) - set(rand_id_list))
        for rand_id in rand_id_list:
            road_dist = None
            id_to_try = rand_id
            while not road_dist:
                try:
                    arcpy.management.SelectLayerByAttribute(
                        "harvest_site_layer",
                        "NEW_SELECTION",
                        f"OBJECTID = {id_to_try}"
                    )
                    arcpy.management.SelectLayerByAttribute(
                        "sawmill_layer",
                        "NEW_SELECTION",
                        f"OBJECTID = {dist_id_dict[sm_type][id_to_try][0]}"
                    )
                    out_path = os.path.join(output_dir, f"path_{sm_type[:3]}_{id_to_try}.shp")
                    road_dist = distance_calculator.calculate_route_distance(
                        "harvest_site_layer", nw_ds, "sawmill_layer", out_path
                    )
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

    # close csv file and delete temporary layers, feature classes, and solvers
    output_file.close()
    arcpy.management.Delete("harvest_site_layer")
    arcpy.management.Delete("sawmill_layer")
    for name in arcpy.ListDatasets("*Solver*"):
        arcpy.management.Delete(name)

def calculate_road_distance_individual(di_dict, ppt, op_dir, hv_sites, sm_data, nw_ds):
    """Calculates circuity factor for each sawmill type"""
    # select m number of random ids from each of the type's lists
    # calculate the road distance for each of the ids and sawmill id pairs
    # add to rd_list and ed_list, as well as write out to a csv file
    arcpy.AddMessage("Starting Road Distance Calculations")
    arcpy.management.MakeFeatureLayer(hv_sites, "harvest_site_layer")
    arcpy.management.MakeFeatureLayer(sm_data, "sawmill_layer")
    for sm_type in di_dict:

        # output file for distance results so the full script doesn't have to run every time
        csv_out = os.path.join(op_dir, f"{sm_type[:3]}_distance.csv")
        output_file = open(csv_out, "w+", newline="\n")
        output_writer = csv.writer(output_file)

        oid_list = list(dist_id_dict[sm_type].keys())
        rand_id_list = random.sample(oid_list, ppt)
        remaining_ids = list(set(oid_list) - set(rand_id_list))
        for rand_id in rand_id_list:
            road_dist = None
            id_to_try = rand_id
            while not road_dist:
                try:
                    arcpy.management.SelectLayerByAttribute(
                        "harvest_site_layer",
                        "NEW_SELECTION",
                        f"OBJECTID = {id_to_try}"
                    )
                    arcpy.management.SelectLayerByAttribute(
                        "sawmill_layer",
                        "NEW_SELECTION",
                        f"OBJECTID = {dist_id_dict[sm_type][id_to_try][0]}"
                    )
                    out_path = os.path.join(output_dir, f"path_{sm_type[:3]}_{id_to_try}.shp")
                    road_dist = distance_calculator.calculate_route_distance(
                        "harvest_site_layer", nw_ds, "sawmill_layer", out_path
                    )
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

        output_file.close()
    # delete temporary layers, feature classes, and solvers
    arcpy.management.Delete("harvest_site_layer")
    arcpy.management.Delete("sawmill_layer")
    for name in arcpy.ListDatasets("*Solver*"):
        arcpy.management.Delete(name)

def calculate_circuity_factor_from_csv(rd_csv, output_name):
    """Reads in road distance csv created by the road distance calculation functions"""
    rd_list = []
    ed_list = []

    rd_in = open(rd_csv, "r", newline="\n")
    rd_reader = csv.reader(rd_in)
    for row in rd_reader:
        ed_list.append(float(row[2]))
        rd_list.append(float(row[3]))
    rd_in.close()

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
    print(f"Circuity Factor for {output_name}: {b1}")

    results_file = open(os.path.join(output_dir, output_name), "w+")
    results_file.write(str(model1.summary()) + "\n")
    results_file.write(str(model2.summary()) + "\n")
    results_file.write(str(model3.summary()) + "\n")
    results_file.write(f"Circuity factor: {b1}")
    results_file.close()


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

calculate_sl_distances(harvest_sites, sawmills, sm_types, dist_id_dict, output_dir)
read_sl_distance_csv(os.path.join(output_dir, "sl_distances.csv"), dist_id_dict)
calculate_road_distance_individual(
    dist_id_dict,
    pairs_per_type,
    output_dir,
    harvest_sites,
    sawmills,
    network_dataset
)
calculate_road_distance_all(
    dist_id_dict,
    int(pairs_per_type / 6),
    output_dir,
    harvest_sites,
    sawmills,
    network_dataset
)
arcpy.management.Delete("hs_points")
result_output = os.path.join(output_dir, "distances.csv")
calculate_circuity_factor_from_csv(result_output, "circuity_factor_result_all.txt")
for sm_type in sm_types:
    result_output = os.path.join(output_dir, f"{sm_type[:3]}_distance.csv")
    calculate_circuity_factor_from_csv(result_output, f"circuity_factor_{sm_type[:3]}.txt")