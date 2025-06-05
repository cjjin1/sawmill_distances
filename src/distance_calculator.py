########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates distance from a point on a public road to the nearest sawmill
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
    arcpy.conversion.RasterToPolyline(cost_path, output_path, simplify="SIMPLIFY")
    distance = _calculate_distance_for_shp(output_path)
    return distance

def calculate_road_distance_nd(starting_point, network_dataset, sawmill, output_path):
    """Finds the distance from a starting point to a sawmill destination using network analyst"""
    arcpy.CheckOutExtension("Network")
    route_layer_name = "sawmill_route"
    result = arcpy.na.MakeRouteLayer(
        network_dataset,
        route_layer_name,
        "Length",
    )
    route_layer = result.getOutput(0)
    sub_layers = arcpy.na.GetNAClassNames(route_layer)
    stops_layer_name = sub_layers["Stops"]

    arcpy.na.AddLocations(
        in_network_analysis_layer=route_layer,
        sub_layer=stops_layer_name,
        in_table=starting_point,
        append="CLEAR",
    )

    arcpy.na.AddLocations(
        in_network_analysis_layer=route_layer,
        sub_layer=stops_layer_name,
        in_table=sawmill,
        append="APPEND",
    )

    arcpy.na.Solve(route_layer, terminate_on_solve_error="TERMINATE")
    arcpy.management.CopyFeatures(route_layer.listLayers(sub_layers["Routes"])[0], output_path)
    distance = _calculate_distance_for_shp(output_path)
    arcpy.CheckInExtension("Network")
    return distance

def _calculate_distance_for_shp(shapefile_path):
    """Calculates distance for a given polyline shapefile"""
    arcpy.management.AddField(shapefile_path, "distance", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(
        shapefile_path, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
    )
    distance = 0
    sc = arcpy.da.SearchCursor(shapefile_path, ["distance"])
    for row in sc:
        distance += row[0]
    del row, sc
    return distance

def euclidean_distance_haversine(point_1, point_2, radius = 3958.7610477):
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
    return radius * c

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