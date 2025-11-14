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
import matplotlib.pyplot as plt

def calculate_route_distance(harvest_site, network_ds, sawmill, output_path, travel_mode):
    """Finds the route from harvest site to sawmill then calculates distance"""
    calculate_road_distance_nd(harvest_site, network_ds, sawmill, output_path, travel_mode)
    road_dist = calculate_distance_for_fc(output_path)
    arcpy.analysis.Near(harvest_site, output_path, search_radius="3 Miles", distance_unit="Miles")
    sc = arcpy.da.SearchCursor(harvest_site, ["NEAR_DIST"])
    for row in sc:
        road_dist += row[0]
        break
    del sc, row
    return road_dist

def calculate_road_distance_nd(starting_point, network_dataset, sawmill, output_path, travel_mode):
    """Finds the road distance from a starting point to a sawmill destination using network analyst"""
    arcpy.CheckOutExtension("Network")
    route_layer_name = "sawmill_route"
    result = arcpy.na.MakeRouteAnalysisLayer(
        network_dataset,
        layer_name=route_layer_name,
        travel_mode=travel_mode
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

def calculate_circuity_factor_from_csv(rd_csv, output_name, op_dir, sawmill_type, pdf_file):
    """Reads in road distance csv created by the road distance calculation functions. Returns coefficent
       for each regression."""
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

    generate_histogram(road_distance, "Road Distance", sawmill_type, 40, pdf_file)
    generate_histogram(euclidean_distance, "Euclidean Distance", sawmill_type, 40, pdf_file)
    generate_overlaid_histogram(
        [road_distance, euclidean_distance],
        ["Road Distance", "Euclidean Distance"],
        sawmill_type,
        60,
        pdf_file
    )

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

    b1 = model1.params['sl']
    b2 = model2.params['sl']
    b3 = model3.params['sl']
    arcpy.AddMessage(f"Circuity Factor for {output_name}: {b3}")

    results_file = open(os.path.join(op_dir, output_name), "w+")
    results_file.write(str(model1.summary()) + "\n")
    results_file.write(str(model2.summary()) + "\n")
    results_file.write(str(model3.summary()) + "\n")
    results_file.write(f"Circuity factor: {b3}")
    results_file.close()

    return b1, b2, b3

def generate_histogram(arr, value_name, sm_type, bin_num, pdf):
    """Generates a histogram based off an array for a sawmill type. Outputs to a pdf file."""
    plt.hist(arr, bins=bin_num, edgecolor="black", linewidth=1.2)
    plt.xlim(0, 120)
    plt.xlabel(value_name + " (Miles)")
    plt.ylabel("Frequency")
    plt.title(f"Histogram of {value_name} for {sm_type}")
    pdf.savefig()
    plt.close()

def generate_overlaid_histogram(arr_list, value_list, sm_type, bin_num, pdf):
    """Generates an overlaid histogram based off two arrays (of both road and eucldiean distance for a sawmill type.
       Outputs to a pdf file."""
    plt.hist(arr_list, label=value_list, bins=bin_num, edgecolor="black", linewidth=0.5, color=["blue", "red"])
    plt.xlim(0, 120)
    plt.xlabel("Distance (Miles)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.title(f"Histogram of Road and Euclidean Distances for {sm_type}")
    pdf.savefig()
    plt.close()