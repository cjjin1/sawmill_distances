########################################################################################################################
# distance_calculation.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculate distance between stands and the nearest sawmill
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

#Clip the NFS roads and road segments to the state
#Creeate a buffer around the state boundary to consider sawmills outside of the state, buffer distance can change
boundary_buffer = os.path.basename(boundary_shp).split(".")[0] + "_buffer.shp"
arcpy.analysis.Buffer(boundary_shp, boundary_buffer, "15 Miles")
arcpy.analysis.Clip(NFS_roads, boundary_buffer, "NFS_MS")
arcpy.analysis.Clip(roads_shp, boundary_buffer, "roads_MS")
NFS_roads = scratch_dir + "NFS_MS"
roads_shp = scratch_dir + "roads_MS"

#Create a feature class to contain the end point of each polyline in the NFS_roads shapefile
NFS_points = os.path.basename(NFS_roads).split(".")[0] + "_points.shp"
arcpy.management.CreateFeatureclass(scratch_dir, NFS_points, "POINT", spatial_reference=SR)

arcpy.AddField_management(NFS_points, "LineID", "LONG")
arcpy.AddField_management(NFS_points, "PointType", "TEXT")

sc = arcpy.da.SearchCursor(NFS_roads, ["SHAPE@", "OID@"])
ic = arcpy.da.InsertCursor(NFS_points, ["SHAPE@", "LineID", "PointType"])
for row in sc:
    line = row[0]
    oid = row[1]
    part = line.getPart(line.partCount - 1)
    start_point = part[0]
    end_point = part[-1]
    ic.insertRow([start_point, oid, "start"])
    ic.insertRow([end_point, oid, "end"])
del row, sc, ic

# TODO
# I need to find a way to filter out NFS roads that only connect to public roads and no other NFS roads.
# I can find all points that don't intersect with NFS roads and do intersect (within 50 feet, can change value)
# other roads.

#Select and export points within 50 feet of a public road
arcpy.management.SelectLayerByLocation(
    NFS_points,"WITHIN_A_DISTANCE",roads_shp,"50 feet","NEW_SELECTION")
temp_points = "temp_points.shp"
arcpy.management.CopyFeatures(NFS_points, temp_points)

#Join the selected points to the NFS roads
sj_result = "sj_result"
arcpy.analysis.SpatialJoin(
    target_features=temp_points,
    join_features=NFS_roads,
    out_feature_class=sj_result,
    join_operation="JOIN_ONE_TO_MANY",
    match_option="INTERSECT"
)

#Count how many NFS roads each point intersects
intersect_dict = {}
sc = arcpy.da.SearchCursor(sj_result, ["FID"])
for row in sc:
    if not intersect_dict.get(row[0]):
        intersect_dict[row[0]] = 0
    intersect_dict[row[0]] += 1
del row, sc

#create a new dictionary where only the points with one interesection are included
one_intersect_dict = {}
for fid in intersect_dict:
    if intersect_dict[fid] == 1:
        one_intersect_dict[fid] = intersect_dict[fid]

#create a new point feature class for exit points of NFS roads
NFS_exit_points = "NFS_exit_points.shp"
arcpy.management.CreateFeatureclass(scratch_dir, NFS_exit_points, "POINT", spatial_reference=SR)

#add points to exit point feature class that fulfill the criteria
arcpy.AddField_management(NFS_exit_points, "LineID", "LONG")
arcpy.AddField_management(NFS_exit_points, "PointType", "TEXT")

sc = arcpy.da.SearchCursor(temp_points, ["FID", "SHAPE@", "LineID", "PointType"])
ic = arcpy.da.InsertCursor(NFS_exit_points, ["SHAPE@", "LineID", "PointType"])
for row in sc:
    if one_intersect_dict.get(row[0]):
        ic.insertRow([row[1], row[2], row[3]])
del row, sc, ic
