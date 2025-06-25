########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates distance from a harvest site to a sawmill
########################################################################################################################

import arcpy, os
from arcpy.sa import *

def calculate_distance(harvest_site, roads, network_dataset, sawmills, slope, output_path):
    """Finds the total road distance from a harvest site to a sawmill destination.
       Harvest site input must be a singular point.
       If multiple sawmills are inputted, then the nearest sawmill will be the destination.
       Returns both total road distance and Euclidean distance, in that order"""
    centroid_fc = "harvest_site_centroid"
    arcpy.management.FeatureToPoint(harvest_site, centroid_fc)

    lc_path = "least_cost_path"
    roads_raster = os.path.basename(roads) + "_raster"
    if not arcpy.Exists(roads_raster):
        arcpy.conversion.PolylineToRaster(
            roads, "OBJECTID", roads_raster, cellsize=slope
        )
    calculate_least_cost_path(centroid_fc, roads_raster, slope, lc_path)
    lcp_points = "lcp_points"
    arcpy.management.GeneratePointsAlongLines(
        lc_path, lcp_points, Point_Placement="PERCENTAGE", Percentage=100, Include_End_Points="END_POINTS"
    )
    arcpy.analysis.Near(lcp_points, roads, search_radius="60 Feet", location="LOCATION", distance_unit="Miles")
    near_dist_min = 100
    near_x_min = 0
    near_y_min = 0
    spat_ref = None
    sc = arcpy.da.SearchCursor(lcp_points, ["SHAPE@", "NEAR_DIST", "NEAR_X", "NEAR_Y"])
    for shape, near_dist, near_x, near_y in sc:
        if near_dist != -1 and near_dist < near_dist_min:
            near_dist_min = near_dist
            near_x_min = near_x
            near_y_min = near_y
            spat_ref = shape.spatialReference
    if not spat_ref:
        raise arcpy.ExecuteError("No nearby roads to harvest site")
    starting_point = arcpy.PointGeometry(arcpy.Point(near_x_min, near_y_min), spat_ref)

    temp_path = "network_path"
    if int(arcpy.management.GetCount(sawmills)[0]) == 1:
        calculate_road_distance_nd(starting_point, network_dataset, sawmills, temp_path)
        euclidean_distance = euclidean_distance_near(centroid_fc, sawmills)
    elif int(arcpy.management.GetCount(sawmills)[0]) > 1:
        calculate_closest_road_distance_nd(starting_point, network_dataset, sawmills, temp_path)
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_destination")
        arcpy.management.SelectLayerByLocation(
            "sawmill_destination", "WITHIN_A_DISTANCE", temp_path, search_distance="100 feet"
        )
        euclidean_distance = euclidean_distance_near(centroid_fc, "sawmill_destination")
        arcpy.management.Delete("sawmill_destination")
    else:
        raise arcpy.ExecuteError("No valid sawmill input")

    arcpy.edit.Snap(
        in_features=lc_path,
        snap_environment=[[temp_path, "END", "100 Feet"]]
    )
    arcpy.management.Merge([temp_path, lc_path], output_path)
    road_distance = calculate_distance_for_fc(output_path)

    # arcpy.management.Delete(temp_path)
    # arcpy.management.Delete("least_cost_path")
    arcpy.management.Delete(centroid_fc)
    arcpy.management.Delete(starting_point)
    for name in arcpy.ListDatasets("*Solver*"):
        arcpy.management.Delete(name)
    for name in arcpy.ListRasters("*Cost*"):
        arcpy.management.Delete(name)
    return road_distance, euclidean_distance

def calculate_least_cost_path(starting_point, dest, cost_raster, output_path):
    """Takes in a starting point, roads raster, and a sawmill destination
       Finds the distance from the starting point to the sawmill destination
       Returns a feature class containing a path and distance
       Can accommodate multiple destinations if destination is unknown, will find
       the closest destination out of the entire sawmill feature class"""
    cost = CostDistance(starting_point, cost_raster)
    backlink = CostBackLink(starting_point, cost_raster)
    cost_path = CostPath(
        dest,
        cost,
        backlink,
        "BEST_SINGLE"
    )
    arcpy.conversion.RasterToPolyline(cost_path, output_path)
    arcpy.management.Delete(cost_path)
    arcpy.management.Delete(cost)
    arcpy.management.Delete(backlink)

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
        search_tolerance="100 feet"
    )

    arcpy.na.Solve(route_layer, terminate_on_solve_error="TERMINATE")
    arcpy.management.CopyFeatures(sub_layers["Routes"], output_path)
    arcpy.management.Delete(route_layer_name)
    arcpy.CheckInExtension("Network")

def calculate_closest_road_distance_nd(starting_point, network_dataset, sawmills, output_path):
    """Finds the distance from a starting point to the nearest sawmill destination using network analyst"""
    arcpy.CheckOutExtension("Network")
    cf_layer_name = "closest_sawmill"
    arcpy.na.MakeClosestFacilityAnalysisLayer(
        network_dataset,
        cf_layer_name,
        travel_mode = "Driving Distance"
    )

    sub_layers = arcpy.na.GetNAClassNames(cf_layer_name)
    facilities = sub_layers["Facilities"]
    incidents = sub_layers["Incidents"]

    arcpy.na.AddLocations(cf_layer_name, facilities, sawmills, search_tolerance="100 feet")
    arcpy.na.AddLocations(cf_layer_name, incidents, starting_point)

    arcpy.na.Solve(cf_layer_name)
    arcpy.management.CopyFeatures(sub_layers["CFRoutes"], output_path)
    arcpy.management.Delete(cf_layer_name)
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
        distance += row[0]
    del row, sc
    return distance

def euclidean_distance_near(point_1, point_2):
    """Calculates the Euclidean distance between two points using near tool"""
    arcpy.analysis.Near(point_1, point_2, distance_unit = "Miles", method="GEODESIC")
    distance = 0
    sc = arcpy.da.SearchCursor(point_1, ["NEAR_DIST"])
    for row in sc:
        distance = row[0]
        break
    del row, sc
    if int(arcpy.management.GetCount(point_1)[0]) > 1 or int(arcpy.management.GetCount(point_2)[0]) > 1:
        raise arcpy.ExecuteError("Euclidean distance: one or both point feature classes contain more than one point")
    return distance