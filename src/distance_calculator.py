########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates distance from a point on a public road to the nearest sawmill
# Usage: <Workspace> <Public Roads Shapefile> <NFS exit points> <sawmills>
########################################################################################################################

import arcpy, sys, os
from arcpy.sa import *

def calculate_distances_from_exit(starting_point, roads, sawmills):
    """Takes in a starting point, roads raster, and multiple sawmill destinations
       Finds the distances to each sawmill destination
       Returns a feature class containing paths and distances"""
    road_cost = CostDistance(starting_point, roads)
    road_backlink = CostBackLink(starting_point, roads)
    cost_path = CostPath(
        sawmills,
        road_cost,
        road_backlink,
        "BEST_SINGLE"
    )
    paths_shp = "path.shp"
    arcpy.conversion.RasterToPolyline(cost_path, paths_shp, simplify="SIMPLIFY")
    arcpy.management.AddField(paths_shp, "distance", "double")
    arcpy.management.CalculateGeometryAttributes(
        paths_shp, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
    )
    distance = 0
    sc = arcpy.da.SearchCursor(paths_shp, ["distance"], "FID = 0")
    for row in sc:
        distance = row[0]
    del row, sc
    return distance
