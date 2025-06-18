########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates distance from a harvest site to a sawmill
########################################################################################################################

import arcpy

def calculate_distance(harvest_site, roads, network_dataset, sawmills, output_path):
    """Finds the total road distance from a harvest site to a sawmill destination.
       Harvest site input must be a singular point.
       If multiple sawmills are inputted, then the nearest sawmill will be the destination.
       Returns both total road distance and Euclidean distance, in that order"""
    centroid_fc = "harvest_site_centroid.shp"
    arcpy.management.FeatureToPoint(harvest_site, centroid_fc)

    sr = arcpy.Describe(harvest_site).spatialReference
    arcpy.CreateFeatureclass_management(
        arcpy.env.workspace, "nearest_point", "POINT", spatial_reference=sr
    )
    arcpy.analysis.Near(centroid_fc, roads, location = "LOCATION", distance_unit = "Miles")
    nearest_point = None
    near_line = None
    near_distance = 0
    i = 0
    sc = arcpy.da.SearchCursor(centroid_fc, ["SHAPE@", "NEAR_DIST", "NEAR_X", "NEAR_Y"])
    ic = arcpy.da.InsertCursor("nearest_point", ["SHAPE@"])
    for shape, near_dist, near_x, near_y in sc:
        if i != 0:
            raise arcpy.ExecuteError("Harvest site feature class includes more than one point")
        nearest_point = arcpy.PointGeometry(arcpy.Point(near_x, near_y), shape.spatialReference)
        near_line = arcpy.Polyline(arcpy.Array([shape.firstPoint, arcpy.Point(near_x, near_y)]), sr)
        near_distance = near_dist
        i += 1
    ic.insertRow([nearest_point])
    del near_x, near_y, shape, near_dist, sc, ic

    if int(arcpy.management.GetCount(sawmills)[0]) == 1:
        road_distance = calculate_road_distance_nd(nearest_point, network_dataset, sawmills, output_path)
        euclidean_distance = euclidean_distance_near(centroid_fc, sawmills)
    elif int(arcpy.management.GetCount(sawmills)[0]) > 1:
        road_distance = calculate_closest_road_distance_nd(nearest_point, network_dataset, sawmills, output_path)
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_destination")
        arcpy.management.SelectLayerByLocation(
            "sawmill_destination", "WITHIN_A_DISTANCE", output_path, search_distance="100 feet"
        )
        euclidean_distance = euclidean_distance_near(centroid_fc, "sawmill_destination")
        arcpy.management.Delete("sawmill_destination")
    else:
        raise arcpy.ExecuteError("No valid sawmill input")
    ic = arcpy.da.InsertCursor(output_path, ["SHAPE@", "Shape_Leng"])
    ic.insertRow([near_line, near_distance * 5280])
    del ic

    arcpy.management.Delete(centroid_fc)
    arcpy.management.Delete("nearest_point")
    return road_distance + near_distance, euclidean_distance

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
    distance = calculate_distance_for_shp(output_path)
    arcpy.CheckInExtension("Network")
    return distance

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
    distance = calculate_distance_for_shp(output_path)
    arcpy.CheckInExtension("Network")
    return distance

def calculate_distance_for_shp(shapefile_path):
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