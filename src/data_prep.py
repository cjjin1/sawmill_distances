########################################################################################################################
# data_prep.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Handles and cleans harvest site data and sawmill data. This includes project, clipping, and removing
#          unwanted features.
#          Also handles road data by projecting and merging road data properly.
# Usage: <workspace> <transportation dataset> <road data> <harvest site data> <sawmill data> <harvest site boundaries>
#        <total study area boundaries> <spatial reference code>
########################################################################################################################

import sys, arcpy, os

def project_roads(road_data, transport_ds, sr):
    """Simply projects roads data into new spatial reference"""
    #project input roads into the transportation datasest
    output_path = os.path.join(transport_ds, os.path.basename(road_data))
    if not arcpy.Exists(output_path):
        arcpy.management.Project(road_data, output_path, sr)

def clean_harvest_site_data(harvest_site_data, sr, boundary):
    """Projects and clips harvest site data. Also removes unwanted polygons that are too small."""
    #project harvest site data and boundary
    hs_proj = os.path.splitext(os.path.basename(harvest_site_data))[0]
    if not arcpy.Exists(hs_proj):
        arcpy.management.Project(harvest_site_data, hs_proj, sr)
    bound_proj = os.path.basename(boundary).split(".")[0]
    if not arcpy.Exists(os.path.basename(bound_proj)):
        arcpy.management.Project(boundary, bound_proj, sr)

    # extract the harvest site feature class inside the boundary
    arcpy.management.MakeFeatureLayer(hs_proj, "harvest_layer")
    arcpy.management.SelectLayerByLocation(
        "harvest_layer", "WITHIN", bound_proj, selection_type="NEW_SELECTION"
    )
    hs_bound = "harvest_sites_bounded"
    arcpy.management.CopyFeatures("harvest_layer", hs_bound)
    arcpy.management.Delete("harvest_layer")

    # remove all harvest sites under 60 square feet
    arcpy.management.AddField(hs_bound, "area", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(
        hs_bound, [["area", "AREA_GEODESIC"]], area_unit="SQUARE_FEET_US"
    )
    uc = arcpy.da.UpdateCursor(hs_bound, ["area"])
    for row in uc:
        if row[0] < 60:
            uc.deleteRow()
    del uc, row

def clean_sawmill_data(sawmill_data, sr, boundary):
    """Projects and clips sawmill data. Removes closed and announced sawmills."""
    #project sawmill data and boundary
    sm_proj = os.path.splitext(os.path.basename(sawmill_data))[0]
    if not arcpy.Exists(sm_proj):
        arcpy.management.Project(sawmill_data, sm_proj, sr)
    bound_proj = os.path.basename(boundary).split(".")[0]
    if not arcpy.Exists(os.path.basename(bound_proj)):
        arcpy.management.Project(boundary, bound_proj, sr)

    #extract sawmill feature class inside the boundary
    arcpy.management.MakeFeatureLayer(sawmill_data, "sawmill_layer")
    arcpy.management.SelectLayerByLocation(
        "sawmill_layer", "WITHIN", bound_proj, selection_type="NEW_SELECTION"
    )
    sm_bound = "sawmills_bounded"
    arcpy.management.CopyFeatures("sawmill_layer", sm_bound)
    arcpy.management.Delete("sawmill_layer")

    # remove closed and announced sawmills from sawmill fc
    uc = arcpy.da.UpdateCursor(sm_bound, ["Status"])
    for row in uc:
        if row[0] == "Closed":
            uc.deleteRow()
    del row, uc

def create_network_dataset(transport_ds, roads_data):
    """Cleans and merges the roads feature classes, then creates a network dataset out of the result"""
    #set workspace to transportation feature dataset
    arcpy.env.workspace = transport_ds

    #create list of feature classes to merge, erasing from the larger roads dataset to remove duplicate roads
    nfs_list = arcpy.ListFeatureClasses("*NFS*")
    merge_list = []
    erasing_fc = os.path.basename(roads_data)
    for i, rd_nfs in enumerate(nfs_list):
        arcpy.analysis.Erase(erasing_fc, rd_nfs, f"roads_erased_{i}")
        erasing_fc = f"roads_erased_{i}"
        merge_list.append(rd_nfs)
    merge_list.append(erasing_fc)

    #merge road feature classes
    merged_roads = "merged_roads"
    arcpy.management.Merge(merge_list, merged_roads)
    arcpy.management.RepairGeometry(merged_roads)

    #add and calculate distance field
    arcpy.management.AddField(merged_roads, "distance", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(
        merged_roads, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
    )

workspace = sys.argv[1]
transport_dataset = sys.argv[2]
roads = sys.argv[3]
harvest_sites = sys.argv[4]
sawmills = sys.argv[5]
hs_boundary = sys.argv[6]
sm_boundary = sys.argv[7]
spat_ref = sys.argv[8]

arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True

SR = arcpy.SpatialReference(int(spat_ref))
project_roads(roads, transport_dataset, SR)
clean_harvest_site_data(harvest_sites, SR, hs_boundary)
clean_sawmill_data(sawmills, SR, sm_boundary)
create_network_dataset(transport_dataset, roads)