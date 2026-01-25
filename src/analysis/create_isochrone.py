########################################################################################################################
# create_isochrones.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Creates an isochrone polygon given a point and a network dataset. Allows for multiple cutoff inputs.
########################################################################################################################

import arcpy, os, sys

class Isochrone:
    """Calculates the isochrone for a given point"""

    def __init__(self, network_ds, lat, lon, output_dir, travel_mode, output_convex_hull, cutoffs):
        self.network_ds = network_ds
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        arcpy.env.workspace = self.output_dir
        arcpy.env.overwriteOutput = True
        self.lat = lat
        self.lon = lon
        self.point = f"point_{lat:.3f}_{lon:.3f}".replace(".", "_") + ".shp"

        point_geom = arcpy.PointGeometry(arcpy.Point(lon, lat), arcpy.SpatialReference(4326))
        arcpy.management.CreateFeatureclass(
            self.output_dir,
            self.point,
            geometry_type="POINT",
            spatial_reference=arcpy.SpatialReference(4326)
        )
        with arcpy.da.InsertCursor(self.point, ["SHAPE@"]) as ic:
            ic.insertRow([point_geom])

        output_isochrone = f"isochrone_{lat:.3f}_{lon:.3f}".replace(".", "_") + ".shp"
        self.output_path = os.path.join(output_dir, output_isochrone)
        self.travel_mode = travel_mode
        if self.travel_mode == "Length":
            self.cutoffs = [int(cutoff) for cutoff in cutoffs.split(";")]
        if self.travel_mode == "Time":
            self.cutoffs = [float(cutoff) / 60 for cutoff in cutoffs.split(";")]

        self.output_convex_hull = False
        if output_convex_hull.lower() == "true":
            self.output_convex_hull = True

    def calculate_isochrone(self):
        isochrone_layer_name = "sawmill_isochrone"
        result = arcpy.na.MakeServiceAreaAnalysisLayer(
            self.network_ds,
            layer_name=isochrone_layer_name,
            travel_mode=self.travel_mode,
            cutoffs=self.cutoffs,
            geometry_at_cutoffs="DISKS"
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

    def convex_hull(self):
        """Creates new feature class from isochrones with convex hull"""
        arcpy.management.MinimumBoundingGeometry(
            self.output_path,
            os.path.join(self.output_dir, "convex_hull_" + os.path.basename(self.output_path)),
            geometry_type="CONVEX_HULL",
        )
        self.output_path = os.path.join(self.output_dir, "convex_hull_" + os.path.basename(self.output_path))

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

    def fc_to_geojson(self):
        """Split the output fc into individual geojson files"""
        desc = arcpy.Describe(self.output_path)
        oid_field = desc.OIDFieldName

        temp_layer = "temp_layer"
        arcpy.management.MakeFeatureLayer(self.output_path, temp_layer)

        with arcpy.da.SearchCursor(temp_layer, [oid_field, "ToBreak"]) as sc:
            for row in sc:
                arcpy.management.SelectLayerByAttribute(
                    temp_layer,
                    "NEW_SELECTION",
                    f"{oid_field} = {row[0]}"
                )
                to_break = float(row[1])
                if self.travel_mode == "Time":
                    to_break = int(to_break * 60)
                json_out = f"isochrone_{self.lat:.3f}_{self.lon:.3f}_{to_break}".replace(".", "_") + ".json"
                if self.output_convex_hull:
                    json_out = "convex_hull_" + json_out
                arcpy.conversion.FeaturesToJSON(
                    temp_layer,
                    out_json_file=os.path.join(self.output_dir, json_out)
                )
        arcpy.management.Delete(temp_layer)

    def process(self):
        self.calculate_isochrone()
        if self.output_convex_hull:
            self.convex_hull()
        self.set_symbology()
        self.fc_to_geojson()

def main():
    network_dataset = sys.argv[1]
    lat = float(sys.argv[2])
    lon = float(sys.argv[3])
    output_dir = sys.argv[4]
    travel_mode = sys.argv[5]
    output_convex_hull = sys.argv[6]
    cutoffs = sys.argv[7]

    isochrone = Isochrone(network_dataset, lat, lon, output_dir, travel_mode, output_convex_hull, cutoffs)
    isochrone.process()

if __name__ == "__main__":
    main()