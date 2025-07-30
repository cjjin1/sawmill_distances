########################################################################################################################
# calculate_straight_line_distances.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates the straight line distances from each harvest site to every sawmill of each type
########################################################################################################################

import sys, arcpy, os, random
import distance_calculator as dc

sawmills = sys.argv[1]
harvest_sites = sys.argv[2]
output_dir = sys.argv[3]
try:
    subset_size = int(sys.argv[4])
    if subset_size < 1:
        arcpy.AddWarning("Invalid subset size, harvest site feature class will not be subset.")
except ValueError:
    arcpy.AddWarning("Invalid subset size, harvest site feature class will not be subset.")
    subset_size = 0
try:
    proj = arcpy.mp.ArcGISProject("CURRENT")
    workspace = proj.defaultGeodatabase
except OSError:
    workspace = sys.argv[5]

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

if subset_size > 0:
    sc = arcpy.da.SearchCursor(harvest_sites, ["OBJECTID"])
    id_list = []
    for row in sc:
        id_list.append(row[0])
    del row, sc

    rand_id_list = random.sample(id_list, subset_size)
    where_clause = f"OBJECTID IN ({','.join(map(str, rand_id_list))})"
    arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
    arcpy.management.SelectLayerByAttribute(
        "harvest_site_layer",
        "NEW_SELECTION",
        where_clause,
    )
    arcpy.management.CopyFeatures("harvest_site_layer", "harvest_site_subset")
    harvest_sites = "harvest_site_subset"

#create list for sawmill types
sm_types = [
    "Lumber/Solid Wood", "Pellet", "Chip", "Pulp/Paper", "Composite Panel/Engineered Wood Product", "Plywood/Veneer"
]

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
if output_dir:
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
else:
    output_dir = workspace + "/../" + "straight_line_distances"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

dc.calculate_sl_distances(harvest_sites, sawmills, sm_types, dist_id_dict, output_dir)
arcpy.AddMessage(f"Straight Line Distance CSV can be found in: {os.path.abspath(output_dir)}")
