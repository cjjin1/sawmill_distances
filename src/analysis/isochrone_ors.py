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
travel_mode = sys.argv[4]
ranges = sys.argv[5].split(";")
if travel_mode.lower() == "time":
    ranges = [int(r) * 60 for r in ranges]
elif travel_mode.lower() == "length":
    ranges = [int(r) * 1609.34 for r in ranges]
    travel_mode = "distance"

arcpy.env.workspace = output_dir
arcpy.env.overwriteOutput = True

api_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6Ijg0NTA4MjdhOTBjMjRhYmFiNTg1N2VhYTM2NjNiMWQzIiwiaCI6Im11cm11cjY0In0="

client = openrouteservice.Client(key=api_key)

location = [lat, lon]

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
    output_shp = f"isochrone_{lat:.3f}_{lon:.3f}_{int(r / 1609.34)}miles.shp".replace(".", "_") + ".shp"
    if travel_mode.lower() == "time":
        output_path = os.path.join(
            output_dir,
            f"isochrone_{lat:.3f}_{lon:.3f}_{int(r / 60)}minutes.geojson".replace(".", "_")
        ) + ".geojson"
        output_shp = f"isochrone_{lat:.3f}_{lon:.3f}_{int(r / 60)}minutes.shp".replace(".", "_") + ".shp"

    with open(output_path, "w+") as f:
        json.dump(iso, f)

    print(output_shp)
    arcpy.conversion.JSONToFeatures(output_path, output_shp, geometry_type="POLYGON")