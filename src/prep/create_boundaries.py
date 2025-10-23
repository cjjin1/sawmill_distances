########################################################################################################################
# create_boundaries.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Creates a boundary shapefile for osm_roads_planet.py to use. This shapefile is a 125-mile buffer around
#          all park boundaries within the designated physiographic region. The output shapefile will go into the
#          directory the physiographic boundary shapefile is in. All other intermediate files will be deleted.
# Usage: <park boundaries (ranger_districts.shp)> <physiographic shapefile/fc> <output name>
#        Important note: the output name can only be the basename + extension (no extension if in File GDB), although a
#        full file path is a valid output name.
########################################################################################################################

import sys,os,arcpy

arcpy.env.overwriteOutput = True

#get inputs
park = sys.argv[1]
physio = sys.argv[2]
output = sys.argv[3]

#set workspace to physio's directory
arcpy.env.workspace = os.path.dirname(physio)

#clip the ranger districts by the physiographic region
arcpy.analysis.Clip(park, physio, "temp_park_bd")

#buffer the temp park boundary by 125 miles
arcpy.analysis.Buffer(
    "temp_park_bd",
    output,
    buffer_distance_or_field="125 Miles",
    dissolve_option="ALL"
    )

#delete temp files
arcpy.management.Delete("temp_park_bd")