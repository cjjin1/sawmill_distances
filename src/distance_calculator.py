########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates distance from a harvest site to a sawmill, also contains functions for compiling results of
#          distance calculations into csv files
########################################################################################################################

import arcpy, csv, os, random, time, gc
import statsmodels.api as sm
import numpy as np
import pandas as pd
import datetime

def calculate_route_distance(harvest_site, network_ds, sawmill, output_path):
    """Finds the route from harvest site to sawmill then calculates distance"""
    calculate_road_distance_nd(harvest_site, network_ds, sawmill, output_path)
    road_dist = calculate_distance_for_fc(output_path)
    arcpy.analysis.Near(harvest_site, output_path, search_radius="3 Miles", distance_unit="Miles")
    sc = arcpy.da.SearchCursor(harvest_site, ["NEAR_DIST"])
    for row in sc:
        road_dist += row[0]
        break
    del sc, row
    return road_dist

def calculate_road_distance_nd(starting_point, network_dataset, sawmill, output_path):
    """Finds the road distance from a starting point to a sawmill destination using network analyst"""
    arcpy.CheckOutExtension("Network")
    route_layer_name = "sawmill_route"
    result = arcpy.na.MakeRouteLayer(
        network_dataset,
        route_layer_name,
        "Length",
    )
    route_layer = result.getOutput(0)
    try:
        solver = arcpy.na.GetSolverProperties(route_layer)
        solver.restrictions = ["Oneway"]
    except arcpy.ExecuteError:
        print("No oneway restriction implemented, solution will not include oneway functionality")
    sub_layers = arcpy.na.GetNAClassNames(route_layer)
    stops_layer_name = sub_layers["Stops"]

    arcpy.na.AddLocations(
        in_network_analysis_layer=route_layer,
        sub_layer=stops_layer_name,
        in_table=starting_point,
        append="CLEAR",
        search_tolerance="20000 Feet"
    )

    arcpy.na.AddLocations(
        in_network_analysis_layer=route_layer,
        sub_layer=stops_layer_name,
        in_table=sawmill,
        append="APPEND",
        search_tolerance="20000 Feet"
    )
    try:
        arcpy.na.Solve(route_layer, ignore_invalids="SKIP")
        if int(arcpy.management.GetCount(sub_layers["Routes"])[0]) == 0:
            raise arcpy.ExecuteError("Solve resulted in a failure")
    except arcpy.ExecuteError as e:
        arcpy.management.Delete(route_layer_name)
        raise arcpy.ExecuteError(e)
    arcpy.management.CopyFeatures(sub_layers["Routes"], output_path)
    arcpy.management.Delete(route_layer_name)
    arcpy.management.Delete(route_layer)
    arcpy.CheckInExtension("Network")

def calculate_distance_for_fc(fc_path):
    """Calculates distance for a given polyline shapefile"""
    arcpy.management.AddField(fc_path, "distance", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(
        fc_path, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
    )
    distance = 0
    sc = arcpy.da.SearchCursor(fc_path, ["distance"])
    for row in sc:
        try:
            distance += row[0]
        except TypeError:
            continue
    del row, sc
    return distance

def euclidean_distance(hs_point, points, mill_type):
    """Calculates the Euclidean distance between two points using near tool"""
    arcpy.management.MakeFeatureLayer(points, "point_layer")
    arcpy.management.SelectLayerByAttribute(
        "point_layer", "NEW_SELECTION", f"Mill_Type = '{mill_type}'"
    )
    arcpy.analysis.Near(
        hs_point, "point_layer","120 Miles" ,distance_unit = "Miles", method="PLANAR"
    )
    near_fid = 0
    distance = 0
    sc = arcpy.da.SearchCursor(hs_point, ["NEAR_FID","NEAR_DIST"])
    for row in sc:
        near_fid = row[0]
        distance = row[1]
        break
    del row, sc
    arcpy.management.Delete("point_layer")
    if near_fid == -1 or distance == -1:
        raise arcpy.ExecuteError("Euclidean distance: no harvest site within 120 miles of site")
    return near_fid, distance

def calculate_sl_distances(hv_sites, sawmill_data, sm_ts, op_dir):
    """Calculates straight line distance from every harvest site to every sawmill for every sawmill type"""
    csv_sl_out = os.path.join(op_dir, f"sl_distances_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv")
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
            sawmill_data,
            "harvest_site_layer",
            "120 Miles",
            method="PLANAR",
            distance_unit="Miles"
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

def calculate_road_distances(di_dict, ppt, op_dir, hv_sites, sm_data, nw_ds, kop):
    """Calculates circuity factor for each sawmill type, can accommodate different sample sizes per sawmill type"""
    # select m number of random ids from each of the type's lists
    # calculate the road distance for each of the ids and sawmill id pairs
    # add to rd_list and ed_list, as well as write out to a csv file
    arcpy.AddMessage("Starting Road Distance Calculations")
    for sm_type in di_dict:

        # output file for distance results so the full script doesn't have to run every time
        csv_out = os.path.join(op_dir, f"{sm_type[:3]}_distance.csv")
        output_file = open(csv_out, "w+", newline="\n")
        output_writer = csv.writer(output_file)

        oid_list = list(di_dict[sm_type].keys())
        sample_size = ppt
        if isinstance(ppt, dict):
            sample_size = int(ppt[sm_type])
        rand_id_list = random.sample(oid_list, sample_size)
        remaining_ids = list(set(oid_list) - set(rand_id_list))
        count = 1
        for rand_id in rand_id_list:
            road_dist = None
            id_to_try = rand_id
            while not road_dist:
                try:
                    time.sleep(0.5)
                    gc.collect()
                    arcpy.management.MakeFeatureLayer(hv_sites, f"harvest_site_{id_to_try}")
                    arcpy.management.MakeFeatureLayer(sm_data, f"sawmill_layer_{id_to_try}")
                    arcpy.management.SelectLayerByAttribute(
                        f"harvest_site_{id_to_try}",
                        "NEW_SELECTION",
                        f"OBJECTID = {id_to_try}"
                    )
                    arcpy.management.SelectLayerByAttribute(
                        f"sawmill_layer_{id_to_try}",
                        "NEW_SELECTION",
                        f"OBJECTID = {di_dict[sm_type][id_to_try][0]}"
                    )
                    out_path = os.path.join(arcpy.env.workspace, f"path_{sm_type[:3]}_{id_to_try}")
                    road_dist = calculate_route_distance(
                        f"harvest_site_{id_to_try}", nw_ds, f"sawmill_layer_{id_to_try}", out_path
                    )
                    time.sleep(0.25)
                    gc.collect()
                    if not kop:
                        arcpy.management.Delete(out_path)
                    if road_dist == 0:
                        raise arcpy.ExecuteError("Solve resulted in failure")
                    output_writer.writerow(
                        [id_to_try,
                         di_dict[sm_type][id_to_try][0],
                         di_dict[sm_type][id_to_try][1],
                         road_dist]
                    )
                except arcpy.ExecuteError as e:
                    arcpy.AddWarning(f"{sm_type}:{id_to_try},{di_dict[sm_type][id_to_try][0]} failed: {str(e)}")
                    if remaining_ids:
                        id_to_try = random.choice(remaining_ids)
                        remaining_ids.remove(id_to_try)
                        arcpy.AddWarning(f"Attempting new ID: {id_to_try}, {di_dict[sm_type][id_to_try][0]}")
                        road_dist = None
                    else:
                        arcpy.AddWarning("No more IDs to try, skipping this distance calculation")
                        break
                finally:
                    # delete temporary layers, feature classes, and solvers
                    arcpy.management.Delete(f"harvest_site_{id_to_try}")
                    arcpy.management.Delete(f"sawmill_layer_{id_to_try}")
                    for name in arcpy.ListDatasets("*Solver*"):
                        arcpy.management.Delete(name)
                    time.sleep(0.25)
                    gc.collect()
                    arcpy.management.ClearWorkspaceCache()
            if id_to_try != rand_id:
                arcpy.AddMessage(f"New ID ({id_to_try}) successful")
            arcpy.AddMessage(f"Site {count}: Harvest Site {id_to_try} calculated.")
            count += 1

        output_file.close()

def calculate_circuity_factor_from_csv(rd_csv, output_name, op_dir):
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
    arcpy.AddMessage(f"Circuity Factor for {output_name}: {b1}")

    results_file = open(os.path.join(op_dir, output_name), "w+")
    results_file.write(str(model1.summary()) + "\n")
    results_file.write(str(model2.summary()) + "\n")
    results_file.write(str(model3.summary()) + "\n")
    results_file.write(f"Circuity factor: {b1}")
    results_file.close()