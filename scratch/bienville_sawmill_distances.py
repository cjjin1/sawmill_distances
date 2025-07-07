########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates distance from a harvest sites in Bienville Forest to the nearest sawmill
########################################################################################################################

import arcpy, random
import distance_calculator

arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
arcpy.env.overwriteOutput = True

network_dataset = "Transportation/streets_nd"
roads_dataset = "Transportation/all_roads_fixed"
sawmills = "sawmills_bounded"
harvest_sites = "harvest_sites_bienville_alt"
slope_raster = "slope_raster"
ofa = "off_limit_areas"

random.seed(20)
id_list = random.sample(range(1, 703), 100)
# id_list = id_list[:50]
# id_list_2 = [320, 184, 232] #623,320,232,460,184,11,470
result_dict = {}
output_path = "test_path"

# arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
# arcpy.management.SelectLayerByAttribute(
#     "harvest_site_layer", "NEW_SELECTION", f"OBJECTID = {320}"
# )
# dist, euclidean_dist = distance_calculator.calculate_distance(
#     "harvest_site_layer",
#     roads_dataset,
#     network_dataset,
#     sawmills,
#     slope_raster,
#     ofa,
#     output_path
# )

for fid in id_list:
    arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
    arcpy.management.SelectLayerByAttribute(
        "harvest_site_layer", "NEW_SELECTION", f"OBJECTID = {fid}"
    )
    try:
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            roads_dataset,
            network_dataset,
            sawmills,
            slope_raster,
            ofa,
            output_path
        )
        result_dict[id] = [dist, euclidean_dist]
        print(f"Harvest site {fid}: {dist}, {euclidean_dist}")
    except arcpy.ExecuteError:
        print(f"Harvest site {fid} could not find a path to a sawmill")
    arcpy.management.Delete("harvest_site_layer")
arcpy.management.Delete("temp_path")