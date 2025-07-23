########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates distance from a harvest site to a sawmill
########################################################################################################################

import arcpy, os
from arcpy.sa import *

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
    except:
        raise arcpy.ExecuteError()
    arcpy.management.CopyFeatures(sub_layers["Routes"], output_path)
    arcpy.management.Delete(route_layer_name)
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

########################################################################################################################
# def calculate_distance(harvest_site, roads, network_ds, sawmills, slope, off_limit_areas, output_path, sm_type=None):
#     """Finds the total road distance from a harvest site to a sawmill destination.
#        Harvest site input must be a singular point.
#        If multiple sawmills are inputted, then the nearest sawmill will be the destination.
#        Returns both total road distance and Euclidean distance, in that order"""
#     temp_site = "harvest_site_erased"
#     centroid_fc = "harvest_site_centroid"
#     arcpy.analysis.Erase(harvest_site, off_limit_areas, temp_site)
#     arcpy.management.FeatureToPoint(temp_site, centroid_fc, "INSIDE")
#
#     sr = arcpy.Describe(harvest_site).spatialReference
#     arcpy.CreateFeatureclass_management(
#         arcpy.env.workspace, "nearest_point", "POINT", spatial_reference=sr
#     )
#     arcpy.analysis.Near(centroid_fc, roads, location="LOCATION", distance_unit="Feet")
#     dist_to_road = -1
#     sc = arcpy.da.SearchCursor(centroid_fc, ["NEAR_DIST"])
#     for row in sc:
#         dist_to_road = row[0]
#     del row, sc
#     if dist_to_road == -1:
#         raise arcpy.ExecuteError("Invalid harvest site input")
#
#     if int(arcpy.management.GetCount(centroid_fc)[0]) != 1:
#         raise arcpy.ExecuteError("Invalid harvest site input")
#
#     lc_path = "least_cost_path"
#     path_distance = 0
#     if dist_to_road < 100:
#         arcpy.management.CreateFeatureclass(
#             arcpy.env.workspace, lc_path, "POLYLINE", spatial_reference=sr
#         )
#         sc = arcpy.da.SearchCursor(centroid_fc, ["SHAPE@", "NEAR_DIST", "NEAR_X", "NEAR_Y"])
#         ic = arcpy.da.InsertCursor("nearest_point", ["SHAPE@"])
#         near_line = None
#         for shape, near_dist, near_x, near_y in sc:
#             starting_point = arcpy.PointGeometry(arcpy.Point(near_x, near_y), shape.spatialReference)
#             path_distance = near_dist
#             ic.insertRow([starting_point])
#             arcpy.management.Delete(starting_point)
#             near_line = arcpy.Polyline(arcpy.Array([shape.firstPoint, arcpy.Point(near_x, near_y)]), sr)
#         del shape, near_x, near_y, sc, ic
#         ic2 = arcpy.da.InsertCursor("least_cost_path", ["SHAPE@"])
#         ic2.insertRow([near_line])
#         del ic2
#         arcpy.management.Delete(near_line)
#     else:
#         roads_raster = os.path.basename(roads) + "_raster"
#         if not arcpy.Exists(roads_raster):
#             arcpy.conversion.PolylineToRaster(
#                 roads, "OBJECTID", roads_raster, cellsize=slope
#             )
#         calculate_least_cost_path(centroid_fc, roads_raster, slope, lc_path)
#         lcp_points = "lcp_points"
#         arcpy.management.GeneratePointsAlongLines(
#             lc_path, lcp_points, Point_Placement="PERCENTAGE", Percentage=100, Include_End_Points="END_POINTS"
#         )
#         arcpy.analysis.Near(lcp_points, roads, search_radius="60 Feet", location="LOCATION", distance_unit="Miles")
#         near_dist_min = 100
#         near_x_min = 0
#         near_y_min = 0
#         spat_ref = None
#         sc = arcpy.da.SearchCursor(lcp_points, ["SHAPE@", "NEAR_DIST", "NEAR_X", "NEAR_Y"])
#         ic = arcpy.da.InsertCursor("nearest_point", ["SHAPE@"])
#         for shape, near_dist, near_x, near_y in sc:
#             if near_dist != -1 and near_dist < near_dist_min:
#                 near_dist_min = near_dist
#                 near_x_min = near_x
#                 near_y_min = near_y
#                 spat_ref = shape.spatialReference
#         if not spat_ref:
#             raise arcpy.ExecuteError("No nearby roads to harvest site")
#         starting_point = arcpy.PointGeometry(arcpy.Point(near_x_min, near_y_min), spat_ref)
#         ic.insertRow([starting_point])
#         del sc, ic, shape, near_dist, near_x, near_y
#         arcpy.management.Delete(lcp_points)
#         arcpy.management.Delete(starting_point)
#
#     temp_path = "network_path"
#     if int(arcpy.management.GetCount(sawmills)[0]) == 1:
#         calculate_road_distance_nd("nearest_point", network_ds, sawmills, temp_path)
#         euclidean_distance = euclidean_distance_near(centroid_fc, sawmills)
#     elif int(arcpy.management.GetCount(sawmills)[0]) > 1:
#         sm_input = sawmills
#         if sm_type:
#             arcpy.management.MakeFeatureLayer(sawmills, "sawmills_filtered")
#             arcpy.management.SelectLayerByAttribute(
#                 "sawmills_filtered", "NEW_SELECTION", f"Mill_Type='{sm_type}'"
#             )
#             sm_input = "sawmills_filtered"
#             if int(arcpy.management.GetCount(sm_input)[0]) == 0:
#                 raise arcpy.ExecuteError(f"No sawmills of type {sm_type} exit in the provided sawmills data")
#         calculate_closest_road_distance_nd("nearest_point", network_ds, sm_input, temp_path)
#         arcpy.management.GeneratePointsAlongLines(
#             temp_path,
#             "temp_path_points",
#             Point_Placement="PERCENTAGE",
#             Percentage=100,
#             Include_End_Points="END_POINTS"
#         )
#         arcpy.management.MakeFeatureLayer(sm_input, "sawmill_destination")
#         arcpy.management.SelectLayerByLocation(
#             "sawmill_destination",
#             "WITHIN_A_DISTANCE",
#             "temp_path_points",
#             search_distance="2000 feet"
#         )
#         euclidean_distance = euclidean_distance_near(centroid_fc, "sawmill_destination")
#         arcpy.management.Delete("sawmill_destination")
#         arcpy.management.Delete("temp_path_points")
#         arcpy.management.Delete("sawmills_filtered")
#     else:
#         raise arcpy.ExecuteError("No valid sawmill input")
#
#     arcpy.edit.Snap(
#         in_features=lc_path,
#         snap_environment=[[temp_path, "END", "100 Feet"]]
#     )
#     arcpy.management.Merge([temp_path, lc_path], output_path)
#     if path_distance > 0:
#         road_distance = calculate_distance_for_fc(temp_path)
#         road_distance += path_distance / 5280
#     else:
#         road_distance = calculate_distance_for_fc(output_path)
#
#     arcpy.management.Delete(temp_path)
#     arcpy.management.Delete("least_cost_path")
#     arcpy.management.Delete(centroid_fc)
#     arcpy.management.Delete("nearest_point")
#     arcpy.management.Delete(temp_site)
#     for name in arcpy.ListDatasets("*Solver*"):
#         arcpy.management.Delete(name)
#     for name in arcpy.ListRasters("*Cost*"):
#         arcpy.management.Delete(name)
#     return road_distance, euclidean_distance
#
# def calculate_least_cost_path(starting_point, dest, cost_raster, output_path):
#     """Takes in a starting point, roads raster, and a sawmill destination
#        Finds the distance from the starting point to the sawmill destination
#        Returns a feature class containing a path and distance
#        Can accommodate multiple destinations if destination is unknown, will find
#        the closest destination out of the entire sawmill feature class"""
#     cost = CostDistance(starting_point, cost_raster)
#     backlink = CostBackLink(starting_point, cost_raster)
#     cost_path = CostPath(
#         dest,
#         cost,
#         backlink,
#         "BEST_SINGLE"
#     )
#     arcpy.conversion.RasterToPolyline(cost_path, output_path)
#     arcpy.management.Delete(cost_path)
#     arcpy.management.Delete(cost)
#     arcpy.management.Delete(backlink)
########################################################################################################################