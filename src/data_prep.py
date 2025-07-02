########################################################################################################################
# data_prep.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Prepares data for distance calculations. Filters exit points for NFS roads that connect to public roads.
#          Projects all data to WGS1984. Snaps sawmills and exit points to roads dataset. Makes a raster from roads
#          dataset.
# Usage: <Workspace> <Feature Dataset> <Roads Dataset> <NFS Roads Shapefile> <sawmill shapefile> <harvest sites>
#        <[optional] Boundary Shapefile>
########################################################################################################################

import arcpy, sys, os

#read in scratch directory
scratch_dir = sys.argv[1]
transportation_dataset = sys.argv[2]
arcpy.env.workspace = scratch_dir
arcpy.env.overwriteOutput = True

#read in shapefiles for public roads, NFS roads, sawmills, and state boundary
roads = sys.argv[3]
NFS_roads = sys.argv[4]
sawmills = sys.argv[5]
harvest_sites = sys.argv[6]

#Project all feature classes to NAD 1983 StatePlane Mississippi East (can be changed)
SR = arcpy.SpatialReference(2899)
if not arcpy.Exists(os.path.join(transportation_dataset, os.path.basename(roads))):
    arcpy.Project_management(roads, os.path.join(transportation_dataset, os.path.basename(roads)), SR)
if not arcpy.Exists(os.path.splitext(os.path.basename(NFS_roads))[0]):
    arcpy.Project_management(NFS_roads, os.path.splitext(os.path.basename(NFS_roads))[0], SR)
if not arcpy.Exists(os.path.splitext(os.path.basename(sawmills))[0]):
    arcpy.Project_management(sawmills, os.path.splitext(os.path.basename(sawmills))[0], SR)
if not arcpy.Exists(os.path.splitext(os.path.basename(harvest_sites))[0]):
    arcpy.Project_management(harvest_sites, os.path.splitext(os.path.basename(harvest_sites))[0], SR)
roads = os.path.join(transportation_dataset, os.path.basename(roads))
sawmills = os.path.splitext(os.path.basename(sawmills))[0]
NFS_roads = os.path.splitext(os.path.basename(NFS_roads))[0]
harvest_sites = os.path.splitext(os.path.basename(harvest_sites))[0]

#if a boundary shapefile is included
if len(sys.argv) == 8:
    boundary_shp = sys.argv[7]
    if not arcpy.Exists(os.path.basename(boundary_shp).split(".")[0]):
        arcpy.Project_management(boundary_shp, os.path.basename(boundary_shp).split(".")[0], SR)
    boundary_shp = os.path.basename(boundary_shp).split(".")[0]
    #Clip the NFS roads  to the state
    arcpy.analysis.Clip(NFS_roads, boundary_shp, "NFS_bounded")
    NFS_roads = "NFS_bounded"
    #keep only the sawmills within Mississippi
    arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
    arcpy.management.SelectLayerByLocation(
        "sawmill_layer", "WITHIN", boundary_shp, selection_type="NEW_SELECTION"
    )
    arcpy.management.CopyFeatures("sawmill_layer", "sawmills_bounded")
    sawmills = "sawmills_bounded"
    arcpy.management.Delete("sawmill_layer")
    #extract the timber harvest feature class inside the boundary
    arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_layer")
    arcpy.management.SelectLayerByLocation(
        "harvest_layer", "WITHIN", boundary_shp, selection_type="NEW_SELECTION"
    )
    arcpy.management.CopyFeatures("harvest_layer", "harvest_sites_bounded")
    arcpy.management.Delete("harvest_layer")

#remove closed and announced sawmills from sawmill fc
uc = arcpy.da.UpdateCursor(sawmills, ["Status"])
for row in uc:
    if row[0] == "Closed" or row[0] == "Announced":
        uc.deleteRow()
del row, uc

#generate points along each NFS road
points = "NFS_points"
arcpy.management.GeneratePointsAlongLines(
    NFS_roads, points, "PERCENTAGE", Percentage = 4, Include_End_Points = "END_POINTS"
)

#use Near on points to check for proximity to public roads
#add a field to indicate if a point is near or not
arcpy.analysis.Near(points, roads, search_radius="170 Feet")
arcpy.management.AddField(points, "IS_NEAR", "SHORT")
arcpy.management.CalculateField(
    points, "IS_NEAR", "0 if !NEAR_DIST! == -1 else 1", "PYTHON3"
)

#mark every NFS road as a duplicate if more than 20 points is near a public road (> 80%)
dup_dict = {}
arcpy.management.AddField(NFS_roads, "DUPLICATE", "SHORT")
sc = arcpy.da.SearchCursor(points, ["ORIG_FID", "IS_NEAR"])
uc = arcpy.da.UpdateCursor(NFS_roads, ["OBJECTID","DUPLICATE"])
for row in sc:
    if not dup_dict.get(row[0]):
        dup_dict[row[0]] = row[1]
    else:
        dup_dict[row[0]] += row[1]
del row, sc

for row in uc:
    if dup_dict[row[0]] > 20:
        row[1] = 1
    else:
        row[1] = 0
    uc.updateRow(row)
del row, uc

#export all NFS roads that are not flagged as duplicates
arcpy.conversion.ExportFeatures(NFS_roads, "NFS_cleaned", "DUPLICATE = 0")
NFS_roads = "NFS_cleaned"

#get points to snap the NFS roads to
end_points = "end_points"
arcpy.management.GeneratePointsAlongLines(
    NFS_roads, end_points, Point_Placement="PERCENTAGE", Percentage=100, Include_End_Points="END_POINTS"
)
arcpy.analysis.Near(end_points, roads, search_radius="100 Feet", location="LOCATION", distance_unit="Miles")
arcpy.CreateFeatureclass_management(
    arcpy.env.workspace, "road_points", "POINT", spatial_reference=SR
)
sc = arcpy.da.SearchCursor(end_points, ["SHAPE@", "NEAR_X", "NEAR_Y"])
ic = arcpy.da.InsertCursor("road_points", ["SHAPE@"])
for shape, near_x, near_y in sc:
    road_point = arcpy.PointGeometry(arcpy.Point(near_x, near_y), SR)
    if near_x != -1 and near_y != -1:
        ic.insertRow([road_point])
del sc, ic, shape, near_x, near_y

#remove NFS_roads that won't snap to any public road
remove_count = 1
while remove_count > 0:
    remove_count = 0
    arcpy.management.MakeFeatureLayer(end_points, "end_points_neg")
    arcpy.management.SelectLayerByAttribute(
        "end_points_neg", "NEW_SELECTION", "NEAR_DIST = -1"
    )
    arcpy.analysis.SpatialJoin(
        target_features=end_points,
        join_features=NFS_roads,
        out_feature_class="spatial_join_output",
        join_operation="JOIN_ONE_TO_ONE",
        join_type="KEEP_ALL",
        match_option="INTERSECT",
        field_mapping="",
        search_radius=None,
        distance_field_name=""
    )
    arcpy.management.MakeFeatureLayer("spatial_join_output", "joined_lyr")
    arcpy.management.SelectLayerByAttribute(
        "joined_lyr", "NEW_SELECTION", '"Join_Count" >= 2'
    )

    orig_fid_dict = {}
    sc = arcpy.da.SearchCursor("end_points_neg", ["ORIG_FID"])
    for row in sc:
        if orig_fid_dict.get(row[0]):
            orig_fid_dict[row[0]] += 1
        else:
            orig_fid_dict[row[0]] = 1
    del row, sc

    sc = arcpy.da.SearchCursor("joined_lyr", ["ORIG_FID"])
    for row in sc:
        if orig_fid_dict.get(row[0]) and orig_fid_dict[row[0]] == 2:
            orig_fid_dict[row[0]] -= 1
    del row, sc

    uc = arcpy.da.UpdateCursor(NFS_roads, ["OBJECTID"])
    for row in uc:
        if orig_fid_dict.get(row[0]) and orig_fid_dict[row[0]] == 2:
            uc.deleteRow()
            remove_count += 1
    del row, uc
    arcpy.management.Delete("joined_lyr")
    arcpy.management.Delete("spatial_join_output")
    arcpy.management.Delete("end_points_neg")

#snap the cleaned NFS roads to the points on the public roads
arcpy.edit.Snap(NFS_roads, [["road_points", "VERTEX", "100 Feet"]])

#merge the two roads datasets
output_roads = os.path.join(transportation_dataset, "all_roads")
if arcpy.Exists(os.path.join(transportation_dataset, "streets_nd")):
    arcpy.management.Delete(os.path.join(transportation_dataset, "streets_nd"))
    arcpy.management.Delete(os.path.join(transportation_dataset, "streets_nd_Junctions"))
arcpy.management.Merge([roads, NFS_roads], output_roads)

#integreate the roads dataset then convert to line so that each line ends at an intersection
arcpy.management.Integrate(output_roads, cluster_tolerance="0.5 Feet")
arcpy.management.FeatureToLine(output_roads, os.path.join(transportation_dataset, "all_roads_fixed"))
output_roads = os.path.join(transportation_dataset, "all_roads_fixed")

#Add a distance field to the roads shapefile
arcpy.management.AddField(output_roads, "distance", "DOUBLE")
arcpy.management.CalculateGeometryAttributes(
    output_roads, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
)

#Create and build the network dataset using roads dataset
arcpy.na.CreateNetworkDataset(
    transportation_dataset,
    "streets_nd",
    [os.path.basename(output_roads)],
    "NO_ELEVATION"
)
arcpy.na.BuildNetwork(os.path.join(transportation_dataset, "streets_nd"))