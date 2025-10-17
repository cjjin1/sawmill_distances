import sys,os,arcpy

from temp_prep import DataPrep

arcpy.env.overwriteOutput = True

park = sys.argv[1]
physio = sys.argv[2]
sr = sys.argv[3]
region_name = None
if len(sys.argv) == 5:
    region_name = sys.argv[4]

arcpy.env.workspace = os.path.dirname(physio)

data_prepper = DataPrep(
    park_boundaries=park,
    physio_boundary=physio,
    spat_ref=sr,
)

if region_name:
    data_prepper.create_boundary_fcs(
        new_physio=f"proj_physio_{region_name}.shp",
        new_park_boundaries=f"park_boundaries_{region_name}.shp",
        new_sm_boundaries=f"sm_boundaries_{region_name}.shp"
    )
else:
    data_prepper.create_boundary_fcs()
