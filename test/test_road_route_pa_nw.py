########################################################################################################################
# test_distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Tests the calculate_road_distance_nd function in distance_calculator.py with specifically time cost
########################################################################################################################

import unittest
import arcpy, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "analysis")))
import distance_calculator

class TestDistanceCalculator(unittest.TestCase):
    def setUp(self):
        arcpy.env.workspace = "C:/timber_project/scratch/pa_nw/pa_nw.gdb"
        arcpy.env.overwriteOutput = True

        self.network_dataset = "Transportation/streets_nd"
        self.sawmills = "sawmills"
        self.harvest_sites = "hs_points"

    def test_calculate_road_distance_1(self):
        output_path = "C:/timber_project/outputs/pa_nw_test/test_path_1.shp"
        sawmill_type = "pulp/paper"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 209"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 57"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
            "TimeCost"
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))

    def test_calculate_road_distance_2(self):
        output_path = "C:/timber_project/outputs/pa_nw_test/test_path_2.shp"
        sawmill_type = "pulp/paper"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 158"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 111"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
            "TimeCost"
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))

    def test_calculate_road_distance_3(self):
        output_path = "C:/timber_project/outputs/pa_nw_test/test_path_3.shp"
        sawmill_type = "pulp/paper"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 108"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 126"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
            "TimeCost"
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))

    def test_calculate_road_distance_4(self):
        output_path = "C:/timber_project/outputs/pa_nw_test/test_path_4.shp"
        sawmill_type = "pulp/paper"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 402"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 97"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
            "TimeCost"
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))

    def test_calculate_road_distance_5(self):
        output_path = "C:/timber_project/outputs/pa_nw_test/test_path_5.shp"
        sawmill_type = "pulp/paper"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 165"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 109"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
            "TimeCost"
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))