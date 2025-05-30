########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates distance from a point on a public road to the nearest sawmill
# Usage: <Workspace> <Public Roads Shapefile> <NFS exit points> <sawmills>
########################################################################################################################

import arcpy, sys, os, math
from arcpy.sa import *

def calculate_road_distance(starting_point, roads, sawmill, output_path):
    """Takes in a starting point, roads raster, and a sawmill destination
       Finds the distance from the starting point to the sawmill destination
       Returns a feature class containing a path and distance
       Can accommodate multiple destinations if destination is unknown, will find
       the closest destination out of the entire sawmill feature class"""
    road_cost = CostDistance(starting_point, roads)
    road_backlink = CostBackLink(starting_point, roads)
    cost_path = CostPath(
        sawmill,
        road_cost,
        road_backlink,
        "BEST_SINGLE"
    )
    path_shp = output_path
    arcpy.conversion.RasterToPolyline(cost_path, path_shp, simplify="SIMPLIFY")
    arcpy.management.AddField(path_shp, "distance", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(
        path_shp, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
    )
    distance = 0
    sc = arcpy.da.SearchCursor(path_shp, ["distance"])
    for row in sc:
        distance += row[0]
    del row, sc
    return distance

def euclidean_distance_haversine(point_1, point_2):
    """Calculates the Euclidean distance between two points using Haversine formula"""
    point_1_x, point_1_y, point_2_x, point_2_y = 0, 0 ,0 ,0
    sc = arcpy.da.SearchCursor(point_1, ["SHAPE@XY"])
    for row in sc:
        point_1_x, point_1_y = row[0]
        break
    del row, sc

    sc = arcpy.da.SearchCursor(point_2, ["SHAPE@XY"])
    for row in sc:
        point_2_x, point_2_y = row[0]
        break
    del row, sc

    phi1 = math.radians(point_1_y)
    phi2 = math.radians(point_2_y)
    delta_phi = math.radians(point_2_y - point_1_y)
    delta_lambda = math.radians(point_2_x - point_1_x)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.pow(math.sin(delta_lambda / 2), 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    r = 3958.76104
    return r * c

def euclidean_distance_near(point_1, point_2):
    """Calculates the Euclidean distance between two points using near tool, converts meters into miles"""
    arcpy.analysis.Near(point_1, point_2, method="GEODESIC")
    distance = 6.213711922 * 10**-4
    sc = arcpy.da.SearchCursor(point_1, ["NEAR_DIST"])
    for row in sc:
        distance *= row[0]
        break
    del row, sc
    return distance