########################################################################################################################
# roads_data_prep.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Combines OSM roads and NFS roads into a single roads feature class and puts it into a transportation dataset
#          to be used in a network dataset
# Usage: <Workspace> <Feature Dataset> <Roads data> <NFS Roads data> <Boundary input> <spatial reference>
#        <output name>
########################################################################################################################

import arcpy, sys, os

#read in scratch directory
workspace = sys.argv[1]
transport_dataset = sys.argv[2]
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True

#read in shapefiles for public roads, NFS roads, boundary, and spatial reference
roads = sys.argv[3]
NFS_roads = sys.argv[4]
boundary_shp = sys.argv[5]
spat_ref = sys.argv[6]
output_name = sys.argv[7]

#Project all feature classes
SR = arcpy.SpatialReference(int(spat_ref))
if not arcpy.Exists(os.path.basename(roads)):
    arcpy.management.Project(roads, os.path.basename(roads), SR)
if not arcpy.Exists(os.path.splitext(os.path.basename(NFS_roads))[0]):
    arcpy.management.Project(NFS_roads, os.path.splitext(os.path.basename(NFS_roads))[0], SR)
roads = os.path.basename(roads)
NFS_roads = os.path.splitext(os.path.basename(NFS_roads))[0]

#Project the boundary
if not arcpy.Exists(os.path.basename(boundary_shp).split(".")[0]):
    arcpy.Project_management(boundary_shp, os.path.basename(boundary_shp).split(".")[0], SR)
boundary_shp = os.path.basename(boundary_shp).split(".")[0]
# Clip the NFS roads to the boundary
arcpy.management.MakeFeatureLayer(NFS_roads, "NFS_roads")
arcpy.management.SelectLayerByLocation("NFS_roads", "INTERSECT", boundary_shp)
NFS_roads = "NFS_bounded"
arcpy.management.Project("NFS_roads", NFS_roads, SR)

#generate points along each NFS road
points = "NFS_points"
arcpy.management.GeneratePointsAlongLines(
    NFS_roads, points, "PERCENTAGE", Percentage = 4, Include_End_Points = "END_POINTS"
)

#use Near on points to check for proximity to public roads
#add a field to indicate if a point is near or not
#TODO test adding a ~20% 50 feet minimum
arcpy.analysis.Near(points, roads, search_radius="170 Feet")
arcpy.management.AddField(points, "IS_NEAR", "SHORT")
arcpy.management.CalculateField(
    points, "IS_NEAR", "0 if !NEAR_DIST! == -1 else 1", "PYTHON3"
)

arcpy.analysis.Near(points, roads, search_radius="50 Feet")
arcpy.management.AddField(points, "VERY_NEAR", "SHORT")
arcpy.management.CalculateField(
    points, "VERY_NEAR", "0 if !NEAR_DIST! == -1 else 1", "PYTHON3"
)

#mark every NFS road as a duplicate if more than 20 points is near a public road (> 80%)
near_dict = {}
very_near_dict = {}
arcpy.management.AddField(NFS_roads, "DUPLICATE", "SHORT")
sc = arcpy.da.SearchCursor(points, ["ORIG_FID", "IS_NEAR", "VERY_NEAR"])
uc = arcpy.da.UpdateCursor(NFS_roads, ["OBJECTID","DUPLICATE"])
for row in sc:
    if not near_dict.get(row[0]):
        near_dict[row[0]] = row[1]
    else:
        near_dict[row[0]] += row[1]
    if not very_near_dict.get(row[0]):
        very_near_dict[row[0]] = row[2]
    else:
        very_near_dict[row[0]] += row[2]
del row, sc

for row in uc:
    if near_dict[row[0]] > 20 and very_near_dict[row[0]] > 5:
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
output_roads = "all_roads"
arcpy.management.Merge([roads, NFS_roads], output_roads)

#integreate the roads dataset then convert to line so that each line ends at an intersection
arcpy.management.Integrate(output_roads, cluster_tolerance="0.5 Feet")
arcpy.management.FeatureToLine(output_roads, output_name)

#move output to transportation dataset
arcpy.conversion.FeatureClassToFeatureClass(output_name, transport_dataset, output_name)