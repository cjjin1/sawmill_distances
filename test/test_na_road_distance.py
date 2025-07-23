########################################################################################################################
# test_distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Tests the calculate_road_distance_nd function in distance_calculator.py
########################################################################################################################

import unittest
import arcpy, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import distance_calculator

class TestDistanceCalculator(unittest.TestCase):
    def setUp(self):
        arcpy.env.workspace = "C:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        self.network_dataset = "Transportation/streets_nd"
        self.roads_dataset = "Transportation/all_roads_fixed"
        self.sawmills = "sawmills_bounded"
        self.harvest_sites = "harvest_site_points"
        self.slope_raster = "slope_raster"
        self.ofa = "off_limit_areas"
        self.harvest_points = "harvest_site_points"

    def test_calculate_road_distance_chip(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_chip.shp"
        sawmill_type = "chip"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 68"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 85"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(37 <= dist <= 38)

    def test_calculate_road_distance_lumber(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_lumber.shp"
        sawmill_type = "lumber"

        arcpy.management.MakeFeatureLayer(self.harvest_points, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 68"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 3"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(10 <= dist <= 10.6)

    def test_calculate_road_distance_mass_timber(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_mass_timber.shp"
        sawmill_type = "mass timber"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 68"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 105"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(69 <= dist <= 70)

    def test_calculate_road_distance_OSB(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_OSB.shp"
        sawmill_type = "OSB"

        arcpy.management.MakeFeatureLayer(self.harvest_points, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 68"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 79"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
        )
        arcpy.management.Delete("harvest_site_layer")
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(173 <= dist <= 174)

    def test_calculate_road_distance_panel(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_panel.shp"
        sawmill_type = "panel"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 68"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 81"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(56 <= dist <= 57)

    def test_calculate_road_distance_pellet(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_pellet.shp"
        sawmill_type = "pellet"

        arcpy.management.MakeFeatureLayer(self.harvest_points, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 68"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 100"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(61 <= dist <= 62)

    def test_calculate_road_distance_plywoood_veneer(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_plywood_veneer.shp"
        sawmill_type = "plywood/veneer"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 68"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 65"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(36 <= dist <= 37)

    def test_calculate_road_distance_pulp_paper(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_pulp_paper.shp"
        sawmill_type = "pulp/paper"

        arcpy.management.MakeFeatureLayer(self.harvest_points, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 68"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer",
            "NEW_SELECTION",
            "OBJECTID = 75"
        )

        dist = distance_calculator.calculate_route_distance(
            "harvest_site_layer",
            self.network_dataset,
            "sawmill_layer",
            output_path,
        )
        print(f"Test {sawmill_type} result: {dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(66 <= dist <= 67)

    if __name__ == '__main__':
        unittest.main()