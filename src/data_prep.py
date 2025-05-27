########################################################################################################################
# data_prep.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Prepares data for distance calculations. Filters exit points for NFS roads that connect to public roads.
#          Projects all data to WGS1984. Snaps sawmills and exit points to roads dataset. Makes a raster from roads
#          dataset.
# Usage: <Workspace> <Public Roads Shapefile> <NFS Roads Shapefile> <sawmill shapefile> <[optional] Boundary Shapefile>
########################################################################################################################

import arcpy, sys, os

#read in scratch directory
scratch_dir = sys.argv[1] + "/"
arcpy.env.workspace = scratch_dir
arcpy.env.overwriteOutput = True

#read in shapefiles for public roads, NFS roads, sawmills, and state boundary
roads_shp = sys.argv[2]
NFS_roads = sys.argv[3]
sawmills = sys.argv[4]

#Project all feature classes to WGS 1984 (can be changed)
SR = arcpy.SpatialReference(4326)
if not arcpy.Exists(os.path.basename(roads_shp)):
    arcpy.Project_management(roads_shp, os.path.basename(roads_shp), SR)
if not arcpy.Exists(os.path.basename(NFS_roads)):
    arcpy.Project_management(NFS_roads, os.path.basename(NFS_roads), SR)
if not arcpy.Exists(os.path.basename(sawmills)):
    arcpy.Project_management(sawmills, os.path.basename(sawmills), SR)
sawmills = scratch_dir + os.path.basename(sawmills)
roads_shp = scratch_dir + os.path.basename(roads_shp)
NFS_roads = scratch_dir + os.path.basename(NFS_roads)

#if a boundary shapefile is included
if len(sys.argv) == 6:
    boundary_shp = sys.argv[5]
    if not arcpy.Exists(os.path.basename(boundary_shp)):
        arcpy.Project_management(boundary_shp, os.path.basename(boundary_shp), SR)
    boundary_shp = scratch_dir + os.path.basename(boundary_shp)
    #Clip the NFS roads  to the state
    arcpy.analysis.Clip(NFS_roads, boundary_shp, "NFS_MS")
    NFS_roads = scratch_dir + "NFS_MS.shp"

#Create a feature class to contain the end point of each polyline in the NFS_roads shapefile
NFS_points = os.path.basename(NFS_roads).split(".")[0] + "_points.shp"
arcpy.management.FeatureVerticesToPoints(NFS_roads, NFS_points, "BOTH_ENDS")

#Select and export points within 150 feet of a public road
exit_points = "NFS_exit_points.shp"
arcpy.management.MakeFeatureLayer(NFS_points, "temp_layer")
result = arcpy.management.SelectLayerByLocation(
    "temp_layer","WITHIN_A_DISTANCE",roads_shp,"150 feet","NEW_SELECTION"
)
arcpy.management.CopyFeatures("temp_layer", exit_points)

#Create the closest points from the NFS roads to the roads dataset
adjusted_exit_points = "NFS_adjusted_exit_points.shp"
arcpy.analysis.Near(exit_points, roads_shp, location="LOCATION")
arcpy.management.XYTableToPoint(exit_points, adjusted_exit_points, "NEAR_X", "NEAR_Y")

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
    cellsize=0.0005
)