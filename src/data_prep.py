########################################################################################################################
# data_prep.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Prepares data for distance calculations. Filters exit points for NFS roads that connect to public roads.
#          Projects all data to WGS1984. Snaps sawmills and exit points to roads dataset. Makes a raster from roads
#          dataset.
# Usage: <Workspace> <Feature Dataset> <Public Roads Shapefile> <NFS Roads Shapefile> <sawmill shapefile>
#        <[optional] Boundary Shapefile>
########################################################################################################################

import arcpy, sys, os

#read in scratch directory
scratch_dir = sys.argv[1] + "/"
transportation_dataset = sys.argv[2] + "/"
arcpy.env.workspace = scratch_dir
arcpy.env.overwriteOutput = True

#read in shapefiles for public roads, NFS roads, sawmills, and state boundary
roads = sys.argv[3]
NFS_roads = sys.argv[4]
sawmills = sys.argv[5]

#Project all feature classes to WGS 1984 (can be changed)
SR = arcpy.SpatialReference(4326)
if not arcpy.Exists(os.path.basename(roads)):
    arcpy.Project_management(roads, transportation_dataset + os.path.basename(roads), SR)
if not arcpy.Exists(os.path.basename(NFS_roads)):
    arcpy.Project_management(NFS_roads, os.path.basename(NFS_roads), SR)
if not arcpy.Exists(os.path.basename(sawmills)):
    arcpy.Project_management(sawmills, os.path.basename(sawmills), SR)
sawmills = scratch_dir + os.path.basename(sawmills)
roads = transportation_dataset + os.path.basename(roads)
NFS_roads = scratch_dir + os.path.basename(NFS_roads)

#if a boundary shapefile is included
if len(sys.argv) == 7:
    boundary_shp = sys.argv[6]
    if not arcpy.Exists(os.path.basename(boundary_shp)):
        arcpy.Project_management(boundary_shp, os.path.basename(boundary_shp), SR)
    boundary_shp = scratch_dir + os.path.basename(boundary_shp)
    #Clip the NFS roads  to the state
    arcpy.analysis.Clip(NFS_roads, boundary_shp, "NFS_bounded.shp")
    NFS_roads = scratch_dir + "NFS_bounded.shp"
    #keep only the sawmills within Mississippi
    arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
    arcpy.management.SelectLayerByLocation(
        "sawmill_layer", "WITHIN", boundary_shp, selection_type="NEW_SELECTION"
    )
    arcpy.management.CopyFeatures("sawmill_layer", "sawmills_bounded.shp")
    sawmills = scratch_dir + "sawmills_bounded.shp"
    arcpy.management.Delete("sawmill_layer")

#Create a feature class to contain the end point of each polyline in the NFS_roads shapefile
NFS_points = os.path.basename(NFS_roads).split(".")[0] + "_points.shp"
arcpy.management.FeatureVerticesToPoints(NFS_roads, NFS_points, "BOTH_ENDS")

#Select and export points within 150 feet of a public road
exit_points = "NFS_exit_points.shp"
arcpy.management.MakeFeatureLayer(NFS_points, "temp_layer")
result = arcpy.management.SelectLayerByLocation(
    "temp_layer","WITHIN_A_DISTANCE",roads, "150 feet", "NEW_SELECTION"
)
arcpy.management.CopyFeatures("temp_layer", exit_points)
arcpy.management.Delete("temp_layer")

#Create the closest points from the NFS roads to the roads dataset
adjusted_exit_points = "NFS_adjusted_exit_points.shp"
arcpy.analysis.Near(exit_points, roads, location="LOCATION")
arcpy.management.XYTableToPoint(exit_points, adjusted_exit_points, "NEAR_X", "NEAR_Y")

#Snap the sawmills to the nearest point on a road
adjusted_sawmills = "sawmills_adjusted.shp"
arcpy.analysis.Near(sawmills, roads, location="LOCATION")
arcpy.management.XYTableToPoint(sawmills, adjusted_sawmills, "NEAR_X", "NEAR_Y")

#Add a distance field to the roads shapefile
arcpy.management.AddField(roads, "distance", "DOUBLE")
arcpy.management.CalculateGeometryAttributes(
    roads, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
)

#Create and build the network dataset using roads dataset
arcpy.na.CreateNetworkDataset(
    transportation_dataset,
    "streets_nd",
    [os.path.basename(roads)],
    "NO_ELEVATION"
)

#convert road shapefile to raster
#Uncomment if needed for Cost Distance tool
# roads_raster = "roads_raster.tif"
# arcpy.conversion.PolylineToRaster(
#     in_features=roads_shp,
#     value_field="distance",
#     out_rasterdataset=roads_raster,
#     cell_assignment="MAXIMUM_LENGTH",
#     priority_field="DISTANCE",
#     cellsize=0.0004
# )