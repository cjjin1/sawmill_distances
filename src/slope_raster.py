########################################################################################################################
# slope_raster.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Creates a feature class containing all areas that contain areas where roads cannot be built
# Usage: <Workspace> <stream feature dataset> <streams directory> <roadless area> <roads dataset> <DEM raster>
#        <[optional] Boundary Shapefile>
########################################################################################################################

import arcpy, sys, os

def strip_z_and_project(stream_input, streams_dir_input, stream_dataset_input, spat_ref):
    shapefile_temp = os.path.join(streams_dir_input, "stream_temp.shp")
    sr = arcpy.Describe(stream_input).spatialReference
    geom_type = arcpy.Describe(stream_input).shapeType

    temp_features = []
    sc = arcpy.da.SearchCursor(stream_input, ["SHAPE@"])
    for row in sc:
        parts = []
        for part in row[0]:
            new_part = arcpy.Array([arcpy.Point(p.X, p.Y) for p in part])
            parts.append(new_part)
        new_geom = arcpy.Polyline(arcpy.Array(parts), sr)
        temp_features.append([new_geom])
    del row, sc

    arcpy.management.CreateFeatureclass(
        streams_dir_input,
        "stream_temp.shp",
        geometry_type=geom_type,
        spatial_reference=sr
    )

    ic = arcpy.da.InsertCursor(shapefile_temp, ["SHAPE@"])
    for row in temp_features:
        ic.insertRow(row)
    del row, ic

    arcpy.management.Project(
        shapefile_temp,
        os.path.join(stream_dataset_input, os.path.splitext(os.path.basename(stream_input))[0]),
        spat_ref
    )
    arcpy.management.Delete(shapefile_temp)

def stream_setup(ws, str_ds, str_dir, bd):
    # get list of feature classes in stream_dir
    arcpy.env.workspace = str_dir
    streams_list = arcpy.ListFeatureClasses("*", "Line")

    # project every stream to 2899
    for stream in streams_list:
        strip_z_and_project(stream, str_dir, str_ds, SR)

    # merge the stream feature classes, clip if boundary is provided
    arcpy.env.workspace = str_ds
    streams_list = arcpy.ListFeatureClasses("*", "Line")
    if bd and len(streams_list) > 1:
        merge_list = []
        for stream in streams_list:
            if "_bounded" in stream:
                arcpy.management.Delete(stream)
            else:
                arcpy.analysis.Clip(stream, bd, stream + "_bounded")
                merge_list.append(stream + "_bounded")
        arcpy.management.Merge(merge_list, os.path.join(workspace, "streams"))
        del merge_list
    elif bd and len(streams_list) == 1:
        arcpy.management.Clip(streams_list[0], bd, os.path.join(workspace, "streams"))
    else:
        arcpy.management.Merge(streams_list, os.path.join(workspace, "streams"))

    # create a buffer of the streams
    arcpy.env.workspace = ws
    arcpy.analysis.Buffer("streams", "streams_buffer", "50 Feet")
    return "streams_buffer"

def roadless_area_setup(ws, rl_a, bd):
    arcpy.env.workspace = ws

    # project roadless areas to 2899
    arcpy.management.Project(rl_a, "roadless_area", SR)

    # clip if boundary is provided
    if boundary:
        arcpy.management.Clip(rl_a, bd, rl_a + "_bounded")

    return rl_a + "_bounded"

def create_off_limit_areas(ws, merge_list, roads):
    arcpy.env.workspace = ws

    # merge roadless areas with streams buffer
    arcpy.management.Merge(merge_list, "off_limit_temp")

    # create a buffer of the roads and clip the streams buffer by the roads buffer
    arcpy.analysis.Buffer(roads, roads + "_buffer", "50 Feet")
    if arcpy.Exists("off_limit_areas"):
        arcpy.management.Delete("off_limit_areas")
    arcpy.analysis.Erase("off_limit_temp", roads + "_buffer", "off_limit_areas")
    return "off_limit_areas"

def create_slope_raster(ws, elev_data, ofa):
    arcpy.env.workspace = ws

#read in inputs
workspace = sys.argv[1]
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True
stream_dataset = sys.argv[2]
streams_dir = sys.argv[3]
roadless_area = sys.argv[4]
road_data = sys.argv[5]
dem = sys.argv[6]
boundary = None
SR = arcpy.SpatialReference(2899)
if len(sys.argv) == 8:
    boundary = sys.argv[7]
    if not arcpy.Exists("bv_boundary"):
        arcpy.management.Project(boundary, "bv_boundary", SR)
    boundary = "bv_boundary"

#m_list = [stream_setup(workspace, stream_dataset, streams_dir, boundary)]
#off_limit_areas = create_off_limit_areas(m_list, road_data)
