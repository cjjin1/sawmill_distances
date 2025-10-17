########################################################################################################################
# create_boundaries.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Creates a boundary shapefile for osm_roads_planet.py to use. This shapefile is a 125-mile buffer around
#          all park boundaries within the designated physiographic region. The output shapefile will go into the
#          directory the physiographic boundary shapefile is in. All other intermediate files will be deleted.
# Usage: <park boundaries (ranger_districts.shp)> <physiographic shapefile/fc> <spatial reference: epsg code>
#        <optional: region_name>
#        Important note: although region name is optional, if no region name is selected, the output files, including
#        intermediate files, will have default names. The output files may be overwritten if they already exist inside
#        the directory the physiographic region shapefile is in.
########################################################################################################################

import sys,os,arcpy

from temp_prep import DataPrep

arcpy.env.overwriteOutput = True

#get inputs
park = sys.argv[1]
physio = sys.argv[2]
sr = sys.argv[3]
region_name = None
if len(sys.argv) == 5:
    region_name = sys.argv[4]

#set workspace to physio's directory
arcpy.env.workspace = os.path.dirname(physio)

#construct DataPrep object
data_prepper = DataPrep(
    park_boundaries=park,
    physio_boundary=physio,
    spat_ref=sr,
)

#check if region name has been given
#call create_boundary_fcs()
#delete intermediate files
if region_name:
    data_prepper.create_boundary_fcs(
        new_physio=f"proj_physio_{region_name}.shp",
        new_park_boundaries=f"park_boundaries_{region_name}.shp",
        new_sm_boundaries=f"sm_boundaries_{region_name}.shp"
    )
    arcpy.management.Delete(f"park_boundaries_{region_name}.shp")
    arcpy.management.Delete(f"proj_physio_{region_name}.shp")
else:
    data_prepper.create_boundary_fcs(
        new_physio="proj_physio.shp",
        new_park_boundaries="park_boundaries.shp",
        new_sm_boundaries="sm_boundaries.shp"
    )
    arcpy.management.Delete("park_boundaries.shp")
    arcpy.management.Delete("proj_physio.shp")
