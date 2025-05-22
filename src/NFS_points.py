########################################################################################################################
# NFS_points.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Create points that can be used to calculate distance from NFS roads to sawmills.
# Usage: <Workspace> <public Roads Shapefile> <NFS Roads Shapefile> <Sawmills>
########################################################################################################################

import arcpy, sys, os

#read in scratch directory
scratch_dir = sys.argv[1] + "/"
arcpy.env.workspace = scratch_dir
arcpy.env.overwriteOutput = True

#read in shapefiles for public roads, NFS roads, sawmills, and state boundary
roads_shp = sys.argv[2]
NFS_roads = sys.argv[3]
sawmills_shp = sys.argv[4]
boundary_shp = sys.argv[5]

#Project all feature classes to WGS 1984 (can be changed)
SR = arcpy.SpatialReference(4326)
if not arcpy.Exists(os.path.basename(roads_shp)):
    arcpy.Project_management(roads_shp, os.path.basename(roads_shp), SR)
if not arcpy.Exists(os.path.basename(NFS_roads)):
    arcpy.Project_management(NFS_roads, os.path.basename(NFS_roads), SR)
if not arcpy.Exists(os.path.basename(sawmills_shp)):
    arcpy.Project_management(sawmills_shp, os.path.basename(sawmills_shp), SR)
if not arcpy.Exists(os.path.basename(boundary_shp)):
    arcpy.Project_management(boundary_shp, os.path.basename(boundary_shp), SR)
roads_shp = scratch_dir + os.path.basename(roads_shp)
NFS_roads = scratch_dir + os.path.basename(NFS_roads)
sawmills_shp = scratch_dir + os.path.basename(sawmills_shp)
boundary_shp = scratch_dir + os.path.basename(boundary_shp)

#Clip the NFS roads  to the state
arcpy.analysis.Clip(NFS_roads, boundary_shp, "NFS_MS")
NFS_roads = scratch_dir + "NFS_MS"

#Create a feature class to contain the end point of each polyline in the NFS_roads shapefile
NFS_points = os.path.basename(NFS_roads).split(".")[0] + "_points.shp"
arcpy.management.FeatureVerticesToPoints(NFS_roads, NFS_points, "BOTH_ENDS")

