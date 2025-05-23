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
    """"Takes in a starting point, roads raster, and multiple sawmill destinations
        Finds the distances to each sawmill destination
        Returns a feature class containing paths and distances"""
    road_cost = CostDistance(starting_point, roads)
    road_backlink = CostBackLink(starting_point, roads)
    cost_path = CostPath(
        sawmills,
        road_cost,
        road_backlink,
        "EACH_CELL"
    )
    paths_shp = "paths.shp"
    arcpy.conversion.RasterToPolyline(cost_path, paths_shp)
    arcpy.management.AddField(paths_shp, "distance", "double")
    arcpy.management.CalculateGeometryAttributes(
        paths_shp, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
    )

#read in scratch directory
scratch_dir = sys.argv[1] + "/"
arcpy.env.workspace = scratch_dir
arcpy.env.overwriteOutput = True

#read in shapefiles for roads, exit points, and sawmills
roads_shp = sys.argv[2]
exit_points = sys.argv[3]
sawmills = sys.argv[4]

#Project all feature classes to WGS 1984 (can be changed)
SR = arcpy.SpatialReference(4326)
if not arcpy.Exists(os.path.basename(roads_shp)):
    arcpy.Project_management(roads_shp, os.path.basename(roads_shp), SR)
if not arcpy.Exists(os.path.basename(sawmills)):
    arcpy.Project_management(sawmills, os.path.basename(sawmills), SR)
roads_shp = scratch_dir + os.path.basename(roads_shp)
sawmills = scratch_dir + os.path.basename(sawmills)

#Snap the sawmills to the nearest point on a road
adjusted_sawmills = "sawmills_adjusted.shp"
arcpy.analysis.Near(sawmills, roads_shp, location="LOCATION")
arcpy.management.XYTableToPoint(sawmills, adjusted_sawmills, "NEAR_X", "NEAR_Y")

#Add a distance field to the roads shapefile
arcpy.management.AddField(roads_shp, "distance", "double")
arcpy.management.CalculateGeometryAttributes(
    roads_shp, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
)

#convert road shapefile to raster
roads_raster = "roads_raster.tif"
arcpy.conversion.PolylineToRaster(
    in_features=roads_shp,
    value_field="distance",
    out_rasterdataset=roads_raster,
    cell_assignment="MAXIMUM_LENGTH",
    priority_field="DISTANCE",
    cellsize=10
)