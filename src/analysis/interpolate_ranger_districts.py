########################################################################################################################
# interpolate_range_districts.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Creates a distance to sawmill cost surface raster dataset for ranger districts using interpolation.
########################################################################################################################

import os, arcpy, sys
from arcpy.sa import *

METERS_TO_MILES = 0.0006213712

class MakeODCostMatrix:

    def __init__(self, network_ds, ranger_district, sawmills, workspace, output_path):
        """Initializes the MakeODCostMatrix object with variables"""
        self.network_ds = network_ds
        self.ranger_district = ranger_district
        self.sawmills = sawmills
        self.workspace = workspace
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = self.workspace
        self.origins = None
        self.results_dict = None
        self.output_path = output_path

    def create_fishnet(self):
        """Creates a grid of points across a ranger district with 100 meters between each point."""
        arcpy.management.MakeFeatureLayer(self.ranger_district, "district_layer")
        sel_district_fc = os.path.join(self.workspace, f"district_layer_buffered")
        arcpy.analysis.Buffer("district_layer", sel_district_fc, "2000 Feet")
        # arcpy.management.CopyFeatures("district_layer", sel_district_fc)
        arcpy.management.Delete("district_layer")

        district_desc = arcpy.Describe(sel_district_fc)
        extent = district_desc.extent
        origin = f"{extent.XMin} {extent.YMin}"
        corner = f"{extent.XMax} {extent.YMax}"
        y_axis = f"{extent.XMin} {extent.YMax}"

        r_district_fishnet = os.path.join(self.workspace, f"district_layer_fishnet")
        fishnet_label = r_district_fishnet + "_label"
        arcpy.management.CreateFishnet(
            r_district_fishnet,
            origin,
            y_axis,
            "100 Meters",
            "100 Meters",
            0,
            0,
            corner_coord=corner,
            labels="LABELS",
            template=sel_district_fc,
            geometry_type="POLYGON"
        )

        fishnet_points = os.path.join(self.workspace, f"district_points")
        arcpy.management.MakeFeatureLayer(fishnet_label, "points_layer")
        arcpy.management.SelectLayerByLocation(
            "points_layer",
            "INTERSECT",
            sel_district_fc
        )
        arcpy.management.CopyFeatures("points_layer", fishnet_points)
        arcpy.management.Delete("points_layer")
        self.origins = fishnet_points

    def solve_od_cost_matrix(self):
        """Creates and solves the OD Cost Matrix. Creates a dictionary of results"""
        arcpy.CheckOutExtension("Network")
        result = arcpy.na.MakeODCostMatrixLayer(
            in_network_dataset=self.network_ds,
            out_network_analysis_layer="r_district_ODCM",
            impedance_attribute="Time",
            default_cutoff=10,
            default_number_destinations_to_find=1,
            accumulate_attribute_name=["Length", "Time"]
        )
        lines_layer = result.getOutput(0)
        arcpy.na.AddLocations(
            in_network_analysis_layer="r_district_ODCM",
            sub_layer="Origins",
            in_table=self.origins,
            append="CLEAR",
            search_tolerance="20 Miles"
        )
        arcpy.na.AddLocations(
            in_network_analysis_layer="r_district_ODCM",
            sub_layer="Destinations",
            in_table=self.sawmills,
            append="APPEND",
            search_tolerance="20 Miles"
        )
        try:
            arcpy.na.Solve(lines_layer, ignore_invalids="SKIP")
        except arcpy.ExecuteError as e:
            arcpy.management.Delete(lines_layer)
            arcpy.management.Delete("r_district_ODCM")
            raise arcpy.ExecuteError(e)

        sub_layers = arcpy.na.GetNAClassNames(lines_layer)
        lines = sub_layers["ODLines"]
        origins = sub_layers["Origins"]

        # {id: length}
        lengths_dict = {}

        with arcpy.da.SearchCursor(lines, ["OriginID", "Total_Length"]) as sc:
            for row in sc:
                lengths_dict[row[0]] = row[1]

        with arcpy.da.SearchCursor(origins, ["ObjectID", "DistanceToNetworkInMeters"]) as sc:
            for row in sc:
                if row[0] in lengths_dict:
                    lengths_dict[row[0]] += row[1] * METERS_TO_MILES

        feature_datasets = arcpy.ListDatasets("ODCostMatrixSolver*", "Feature")
        for dataset in feature_datasets:
            arcpy.management.Delete(dataset)
        arcpy.management.Delete("r_district_ODCM")
        arcpy.CheckOutExtension("Network")

        self.results_dict = lengths_dict

    def attach_results_to_fc(self):
        """Creates a new field for the distance result and updates each relevant entry with the associated distance."""
        fields_list = arcpy.ListFields(self.origins, "rd_dist_to_sawmill")
        if len(fields_list) == 0:
            arcpy.management.AddField(self.origins, "rd_dist_to_sawmill", "DOUBLE")

        with arcpy.da.UpdateCursor(self.origins, ["OBJECTID", "rd_dist_to_sawmill"]) as uc:
            for row in uc:
                oid = int(row[0])
                if oid in self.results_dict:
                    row[1] = self.results_dict[oid]
                    uc.updateRow(row)

    def remove_points_without_results(self):
        """Removes all points without results by checking if the results field is null."""
        arcpy.management.MakeFeatureLayer(self.origins, "results_layer")
        arcpy.management.SelectLayerByAttribute(
            "results_layer",
            "NEW_SELECTION",
            f"rd_dist_to_sawmill IS NOT NULL"
        )
        arcpy.management.CopyFeatures("results_layer", self.output_path)

    def process(self):
        self.create_fishnet()
        self.solve_od_cost_matrix()
        self.attach_results_to_fc()
        self.remove_points_without_results()
        return self.output_path

def interpolate_ranger_district(points_fc, clip_polygon):
    """Uses Kriging to interpolate distance to sawmill cost surface using points. Clips the result to a polygon."""
    krig_out = Kriging(
        points_fc,
        "rd_dist_to_sawmill",
        KrigingModelUniversal("QUADRATICDRIFT"),
        100,
        RadiusVariable(12)
    )
    mask_rast = ExtractByMask(krig_out, clip_polygon)
    arcpy.management.Delete(krig_out)
    del krig_out
    return mask_rast

def project_districts(r_district, workspace):
    """Project the ranger districts input file to the workspace."""
    arcpy.management.Project(r_district, os.path.join(workspace, "ranger_districts"), arcpy.SpatialReference(102004))
    return os.path.join(workspace, "ranger_districts")

def main():
    network_dataset = sys.argv[1]
    ranger_districts = sys.argv[2]
    sawmills = sys.argv[3]
    projection = sys.argv[4]
    if projection.lower() == "false":
        projection = False
    else:
        projection = True
    working_gdb = sys.argv[5]

    if projection:
        ranger_districts = project_districts(ranger_districts, working_gdb)

    arcpy.env.workspace = working_gdb
    arcpy.env.overwriteOutput = True

    desc = arcpy.Describe(ranger_districts)
    oid_field = desc.OIDFieldName
    r_district_id_list = []
    with arcpy.da.SearchCursor(ranger_districts, [oid_field]) as sc:
        for row in sc:
            r_district_id_list.append(row[0])

    raster_list = []
    for oid in r_district_id_list:
        arcpy.management.MakeFeatureLayer(ranger_districts, f"district_layer_{oid}")
        arcpy.management.SelectLayerByAttribute(
            f"district_layer_{oid}",
            "NEW_SELECTION",
            f"{oid_field} = {oid}"
        )
        od_cost_matrix = MakeODCostMatrix(
            network_dataset,
            f"district_layer_{oid}",
            sawmills,
            working_gdb,
            f"r_district_{oid}_points"
        )
        od_cost_matrix.process()

        interpolated_rast = interpolate_ranger_district(
            points_fc=os.path.join(working_gdb, f"r_district_{oid}_points"),
            clip_polygon=TEST_R_DISTRICT
        )
        raster_list.append(interpolated_rast)
        arcpy.management.Delete(f"district_layer_{oid}")
        arcpy.management.Delete(f"r_district_{oid}_points")
        arcpy.management.Delete("district_layer_buffered")
        arcpy.management.Delete("district_layer_fishnet")
        arcpy.management.Delete("district_layer_fishnet_label")
        arcpy.management.Delete("district_points")
    arcpy.management.MosaicToNewRaster(
        raster_list,
        working_gdb,
        "interpolated_rast_mosaic",
        cellsize=100,
        number_of_bands=1
    )

if __name__ == "__main__":
    main()