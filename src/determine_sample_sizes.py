########################################################################################################################
# determine_sample_sizes.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Use Neyman or Proportional Allocation to find optimal sample sizes for each sawmill type
########################################################################################################################

import sys, arcpy, csv, os
import distance_calculator as dc
import datetime
import numpy as np

allocation_type = sys.argv[1]
output_dir = sys.argv[2]
sawmills = sys.argv[3]
if allocation_type == "Neyman":
    sl_dist_csv = sys.argv[5]
    network_dataset = sys.argv[6]
    harvest_sites = sys.argv[7]
    pairs_per_type = int(sys.argv[8])
    keep_output_paths = sys.argv[9]
    calculate_road_distances = sys.argv[10]
    if "#" in sys.argv[5:9]:
        raise arcpy.ExecuteError("Straight Line Distance CSV File, " +
                                 "Network Dataset, Harvest Site Data, and Pairs Per Type are all required parameters")
    if keep_output_paths.lower() == "true":
        keep_output_paths = True
    else:
        keep_output_paths = False
    if calculate_road_distances.lower() == "true":
        calculate_road_distances = True
    else:
        calculate_road_distances = False
    try:
        proj = arcpy.mp.ArcGISProject("CURRENT")
        workspace = proj.defaultGeodatabase
    except OSError:
        workspace = sys.argv[11]

    # set workspace
    arcpy.env.workspace = workspace
    arcpy.env.overwriteOutput = True

    # Setup output directory
    if output_dir != "#":
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    else:
        if not calculate_road_distances:
            raise arcpy.ExecuteError("Must provide directory that contains road distance files if using previously " +
                                     "calculated road distance data")
        output_dir = workspace + "/../" + f"outputs/neyman_allocation_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    # creating results file
    csv_out = os.path.join(output_dir, "sample_sizes.csv")
    out_file = open(csv_out, "w+", newline="\n")
    out_writer = csv.writer(out_file)
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

    # Z-score and margin of error values
    z = 1.96
    E = 0.1

    # read in straight line distances
    dc.read_sl_distance_csv(sl_dist_csv, dist_id_dict)
    # calculate road distances if need be
    if calculate_road_distances:
        out_dir_abs = os.path.abspath(output_dir)
        dc.calculate_road_distances(
            dist_id_dict, pairs_per_type, out_dir_abs, harvest_sites, sawmills, network_dataset, keep_output_paths
        )
        arcpy.AddMessage(f"Road Distance csv files can be found in: {os.path.abspath(output_dir)}")
        arcpy.management.Delete("hs_points")
    else:
        arcpy.AddMessage(f"Reading existing road distance csv files: {os.path.abspath(output_dir)}")

    # dictionary to store multipliers
    rd_dict = {
        "Lumber/Solid Wood": [],
        "Pellet": [],
        "Chip": [],
        "Pulp/Paper": [],
        "Composite Panel/Engineered Wood Product": [],
        "Plywood/Veneer": []
    }

    # for each sawmill type, read the corresponding road distance csv file
    # calculate standard deviation of the multipliers (road distance / straight line distance)
    # calculate sample size
    # write output to csv file
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
            rd_dict[sm_type].append(multiplier)
        rd_in.close()

        std_dev = np.std(rd_dict[sm_type])
        n = (z ** 2 * float(std_dev) ** 2) / E ** 2
        n = round(n)
        arcpy.AddMessage(f"Sample size for {sm_type}: {n}")
        out_writer.writerow([sm_type, n])
    out_file.close()
    arcpy.AddMessage(f"Sample size csv file can be found in {os.path.abspath(output_dir)}")
elif allocation_type == "Proportional":
    total_sample_size = sys.argv[4]
    try:
        proj = arcpy.mp.ArcGISProject("CURRENT")
        workspace = proj.defaultGeodatabase
    except OSError:
        workspace = sys.argv[5]

    # set workspace
    arcpy.env.workspace = workspace
    arcpy.env.overwriteOutput = True

    # Setup output directory
    if output_dir != "#":
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    else:
        output_dir = (workspace + "/../"
                      + f"outputs/proportional_allocation_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    # creating results file
    csv_out = os.path.join(output_dir, "sample_sizes.csv")
    out_file = open(csv_out, "w+", newline="\n")
    out_writer = csv.writer(out_file)

    count_dict = {}
    total_count = 0
    sc = arcpy.da.SearchCursor(sawmills, ["Mill_Type"])
    for row in sc:
        if count_dict.get(row[0]):
            count_dict[row[0]] += 1
        else:
            count_dict[row[0]] = 1
        total_count += 1
    del row, sc
    for sm_type in count_dict:
        n = (count_dict[sm_type] / total_count) * int(total_sample_size)
        n = round(n)
        arcpy.AddMessage(f"Sample size for {sm_type}: {n}")
        out_writer.writerow([sm_type, n])
    out_file.close()
    arcpy.AddMessage(f"Sample size csv file can be found in {os.path.abspath(output_dir)}")
else:
    raise arcpy.ExecuteError("Invalid allocation type")
