########################################################################################################################
# isochrone_ors.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Creates an isochrone polygon given a point and a network dataset. Allows for multiple cutoff inputs.
#          Uses openrouteservice
########################################################################################################################

import openrouteservice
import json
import arcpy, sys, os

lat = float(sys.argv[1])
lon = float(sys.argv[2])
output_dir = sys.argv[3]
travel_mode = sys.argv[4].lower()
ranges = sys.argv[5].split(";")
output_shp_files = sys.argv[6]
if travel_mode == "time":
    ranges = [int(r) * 60 for r in ranges]
else:
    ranges = [int(r) * 1609.34 for r in ranges]
    travel_mode = "distance"
if output_shp_files.lower() == "true":
    output_shp_files = True
else:
    output_shp_files = False

arcpy.env.workspace = output_dir
arcpy.env.overwriteOutput = True

api_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6Ijg0NTA4MjdhOTBjMjRhYmFiNTg1N2VhYTM2NjNiMWQzIiwiaCI6Im11cm11cjY0In0="

client = openrouteservice.Client(key=api_key)

location = [lon, lat]

for r in ranges:
    iso = client.isochrones(
        locations=[location],
        profile="driving-hgv",
        range=[r],
        range_type=travel_mode
    )

    output_path = os.path.join(
        output_dir,
        f"isochrone_{lat:.3f}_{lon:.3f}_{int(r / 1609.34)}miles".replace(".", "_")
    ) + ".geojson"
    output_shp = f"isochrone_{lat:.3f}_{lon:.3f}_{int(r / 1609.34)}miles".replace(".", "_") + ".shp"
    if travel_mode.lower() == "time":
        output_path = os.path.join(
            output_dir,
            f"isochrone_{lat:.3f}_{lon:.3f}_{int(r / 60)}minutes".replace(".", "_")
        ) + ".geojson"
        output_shp = f"isochrone_{lat:.3f}_{lon:.3f}_{int(r / 60)}minutes".replace(".", "_") + ".shp"

    with open(output_path, "w+") as f:
        json.dump(iso, f)

    if output_shp_files:
        arcpy.conversion.JSONToFeatures(output_path, output_shp, geometry_type="POLYGON")

        try:
            proj_file = arcpy.mp.ArcGISProject("CURRENT")
            m = proj_file.activeMap

            m.addDataFromPath(os.path.join(output_dir, output_shp))
        except OSError:
            pass