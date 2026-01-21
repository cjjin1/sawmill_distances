########################################################################################################################
# create_isochrones.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Creates an isochrone polygon given a point and a network dataset. Allows for multiple cutoff inputs.
########################################################################################################################

import arcpy, os, sys

class Isochrone:
    """Calculates the isochrone for a given point"""

    def __init__(self, network_ds, point, output_path, travel_mode, cutoffs):
        self.network_ds = network_ds
        self.point = point
        self.output_path = output_path
        self.travel_mode = travel_mode
        if self.travel_mode == "Length":
            self.cutoffs = [int(cutoff) for cutoff in cutoffs.split(";")]
        if self.travel_mode == "Time":
            self.cutoffs = [float(cutoff) / 60 for cutoff in cutoffs.split(";")]

    def calculate_isochrone(self):
        isochrone_layer_name = "sawmill_isochrone"
        result = arcpy.na.MakeServiceAreaAnalysisLayer(
            self.network_ds,
            layer_name=isochrone_layer_name,
            travel_mode=self.travel_mode,
            cutoffs=self.cutoffs
        )
        isochrone_layer = result.getOutput(0)
        try:
            solver = arcpy.na.GetSolverProperties(isochrone_layer)
            solver.restrictions = ["Oneway"]
        except arcpy.ExecuteError:
            print("No oneway restriction implemented, solution will not include oneway functionality")
        sub_layers = arcpy.na.GetNAClassNames(isochrone_layer)
        facilities_layer_name = sub_layers["Facilities"]

        arcpy.na.AddLocations(
            in_network_analysis_layer=isochrone_layer,
            sub_layer=facilities_layer_name,
            in_table=self.point,
            append="CLEAR",
            search_tolerance="20000 Feet"
        )

        try:
            arcpy.na.Solve(isochrone_layer, ignore_invalids="SKIP")
            if int(arcpy.management.GetCount(sub_layers["SAPolygons"])[0]) == 0:
                raise arcpy.ExecuteError("Solve resulted in a failure")
        except arcpy.ExecuteError as e:
            arcpy.management.Delete(isochrone_layer)
            raise arcpy.ExecuteError(e)
        arcpy.management.CopyFeatures(sub_layers["SAPolygons"], self.output_path)
        arcpy.management.Delete(isochrone_layer_name)
        arcpy.management.Delete(isochrone_layer)
        del result, isochrone_layer

        return self.output_path

    def set_symbology(self):
        """Update the output isochrone polygon to have graduated colors"""
        proj_file = arcpy.mp.ArcGISProject("CURRENT")
        m = proj_file.activeMap

        m.addDataFromPath(self.output_path)

        layer = m.listLayers(os.path.splitext(os.path.basename(self.output_path))[0])[0]
        sym = layer.symbology
        sym.updateRenderer("GraduatedColorsRenderer")

        renderer = sym.renderer
        renderer.classification = "FromBreak"
        renderer.breakCount = int(arcpy.management.GetCount(self.output_path)[0])
        renderer.classificationMethod = "NaturalBreaks"

        ramps = proj_file.listColorRamps("Oranges (Continuous)")
        renderer.colorRamp = ramps[0]

        layer.symbology = sym

def main():
    network_dataset = sys.argv[1]
    point = sys.argv[2]
    output_path = sys.argv[3]
    travel_mode = sys.argv[4]
    cutoffs = sys.argv[5]

    isochrone = Isochrone(network_dataset, point, output_path, travel_mode, cutoffs)
    isochrone.calculate_isochrone()
    isochrone.set_symbology()

if __name__ == "__main__":
    main()