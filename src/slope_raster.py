########################################################################################################################
# slope_raster.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Creates a feature class containing all areas that contain areas where roads cannot be built
# Usage: <Workspace> <stream feature dataset> <streams directory> <roadless area> <roads dataset> <DEM raster>
#        <[optional] Boundary Shapefile>
########################################################################################################################

import arcpy, sys, os
arcpy.CheckOutExtension("Spatial")
from arcpy.sa import *

def strip_z_and_project(stream_input, streams_dir_input, stream_dataset_output, spatial_ref):
    """Removes the z value from stream data to allow for projection to 2899"""
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
        os.path.join(stream_dataset_output, os.path.splitext(os.path.basename(stream_input))[0]),
        spatial_ref
    )
    arcpy.management.Delete(shapefile_temp)

def stream_setup(ws, str_ds, str_dir, spat_ref, bd=None):
    """Projects, clips (if boundary is provided, and buffers streams to create off limit areas pertaining to streams"""
    # get list of feature classes in stream_dir
    arcpy.env.workspace = str_dir
    streams_list = arcpy.ListFeatureClasses("*", "Line")

    # project every stream to 2899
    for stream in streams_list:
        strip_z_and_project(stream, str_dir, str_ds, spat_ref)

    # merge the stream feature classes, clip if boundary is provided
    arcpy.env.workspace = str_ds
    streams_list = arcpy.ListFeatureClasses("*", "Line")
    if bd:
        merge_list = []
        for stream in streams_list:
            if "_bounded" in stream:
                arcpy.management.Delete(stream)
            else:
                arcpy.analysis.Clip(stream, bd, stream + "_bounded")
                merge_list.append(stream + "_bounded")
        arcpy.management.Merge(merge_list, os.path.join(workspace, "streams"))
        del merge_list
    else:
        arcpy.management.Merge(streams_list, os.path.join(workspace, "streams"))

    # create a buffer of the streams
    arcpy.env.workspace = ws
    arcpy.analysis.Buffer("streams", "streams_buffer", "100 Feet")
    return "streams_buffer"

def roadless_area_setup(ws, rl_a, spat_ref, bd=None):
    """Project and clip (if boundary is provided) roadless areas"""
    arcpy.env.workspace = ws
    new_polygon = os.path.splitext(os.path.basename(rl_a))[0]

    # project roadless areas to 2899
    arcpy.management.Project(rl_a, new_polygon, spat_ref)

    # clip if boundary is provided
    if boundary:
        arcpy.management.Clip(new_polygon, bd, new_polygon + "_bounded")
        return os.path.join(ws, new_polygon + "_bounded")

    return os.path.join(ws, new_polygon)

def create_off_limit_areas(ws, merge_list, roads):
    """Merge polygons of off limit areas into one polygon feature class"""
    arcpy.env.workspace = ws

    # merge roadless areas with streams buffer
    arcpy.management.Merge(merge_list, "off_limit_temp")

    # create a buffer of the roads and clip the streams buffer by the roads buffer
    arcpy.analysis.Buffer(roads, roads + "_buffer", "50 Feet")
    if arcpy.Exists("off_limit_areas"):
        arcpy.management.Delete("off_limit_areas")
    arcpy.analysis.Erase("off_limit_temp", roads + "_buffer", "off_limit_areas")
    return "off_limit_areas"

def create_slope_raster(ws, elev_data, ofa, spat_ref, bd=None):
    """Create the slope raster for use in least cost path analysis"""
    arcpy.env.workspace = ws
    elev_proj = "dem_proj"
    if not arcpy.Exists(elev_proj):
        arcpy.management.ProjectRaster(elev_data, elev_proj, spat_ref)

    if bd:
        bd_raster = "boundary_raster"
        arcpy.conversion.PolygonToRaster(
            bd,
            "OBJECTID",
            bd_raster,
            "CELL_CENTER",
            cellsize=elev_proj
        )
        boundary_raster = Raster(bd_raster)
        elev_raster = Raster(elev_proj)
        elev_bounded = Con(boundary_raster & elev_raster, elev_raster)
        elev_bounded.save("dem_bounded")
        elev_proj = "dem_bounded"

    off_limits = "off_limit_raster"
    arcpy.conversion.PolygonToRaster(
        ofa,
        "OBJECTID",
        off_limits,
        "CELL_CENTER",
        cellsize=elev_proj
    )

    slope_raster = Slope(elev_proj, "DEGREE")
    ofa_raster = Raster(off_limits)
    slope_mask = Con(IsNull(ofa_raster) & slope_raster, slope_raster)
    slope_mask.save("slope_raster")

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
    boundary = os.path.join(workspace, "bv_boundary")

#add in roadless area dataset when available
m_list = [stream_setup(workspace, stream_dataset, streams_dir, SR, boundary)]
off_limit_areas = create_off_limit_areas(workspace, m_list, road_data)
create_slope_raster(workspace, dem, "off_limit_areas", boundary, SR)
