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
        self.harvest_sites = "harvest_sites_bounded"
        self.slope_raster = "slope_raster"
        self.ofa = "off_limit_areas"
        self.harvest_points = "harvest_site_points"

    def test_calculate_road_distance_chip(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_1.shp"
        sawmill_type = "chip"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 444"
        )

        euclidean_dist, dist = distance_calculator.calculate_road_dist_only(
            "harvest_site_layer",
            self.network_dataset,
            self.sawmills,
            output_path,
            sawmill_type
        )
        print(f"Test {sawmill_type} result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(37 <= dist <= 38)
        self.assertTrue(31 <= euclidean_dist <= 32)

    def test_calculate_road_distance_lumber(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_1.shp"
        sawmill_type = "lumber"

        arcpy.management.MakeFeatureLayer(self.harvest_points, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 444"
        )

        euclidean_dist, dist = distance_calculator.calculate_road_dist_only(
            "harvest_site_layer",
            self.network_dataset,
            self.sawmills,
            output_path,
            sawmill_type
        )
        print(f"Test {sawmill_type} result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(10 <= dist <= 10.6)
        self.assertTrue(7.4 <= euclidean_dist <= 7.8)

    def test_calculate_road_distance_mass_timber(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_1.shp"
        sawmill_type = "mass timber"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 444"
        )

        euclidean_dist, dist = distance_calculator.calculate_road_dist_only(
            "harvest_site_layer",
            self.network_dataset,
            self.sawmills,
            output_path,
            sawmill_type
        )
        print(f"Test {sawmill_type} result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(69 <= dist <= 70)
        self.assertTrue(55.3 <= euclidean_dist <= 56.3)

    def test_calculate_road_distance_OSB(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_1.shp"
        sawmill_type = "OSB"

        arcpy.management.MakeFeatureLayer(self.harvest_points, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 444"
        )
        with self.assertRaises(arcpy.ExecuteError) as e:
            distance_calculator.calculate_road_dist_only(
                "harvest_site_layer",
                self.network_dataset,
                self.sawmills,
                output_path,
                sawmill_type
            )
        arcpy.management.Delete("harvest_site_layer")
        print(f"Test {sawmill_type} successfully results in an error: {e.exception}")

    def test_calculate_road_distance_panel(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_1.shp"
        sawmill_type = "panel"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 444"
        )

        euclidean_dist, dist = distance_calculator.calculate_road_dist_only(
            "harvest_site_layer",
            self.network_dataset,
            self.sawmills,
            output_path,
            sawmill_type
        )
        print(f"Test {sawmill_type} result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(56 <= dist <= 57)
        self.assertTrue(46.5 <= euclidean_dist <= 47.5)

    def test_calculate_road_distance_pellet(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_1.shp"
        sawmill_type = "pellet"

        arcpy.management.MakeFeatureLayer(self.harvest_points, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 444"
        )

        euclidean_dist, dist = distance_calculator.calculate_road_dist_only(
            "harvest_site_layer",
            self.network_dataset,
            self.sawmills,
            output_path,
            sawmill_type
        )
        print(f"Test {sawmill_type} result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(60.5 <= dist <= 61.5)
        self.assertTrue(49.5 <= euclidean_dist <= 50.5)

    def test_calculate_road_distance_plywoood_veneer(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_1.shp"
        sawmill_type = "plywood/veneer"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 444"
        )

        euclidean_dist, dist = distance_calculator.calculate_road_dist_only(
            "harvest_site_layer",
            self.network_dataset,
            self.sawmills,
            output_path,
            sawmill_type
        )
        print(f"Test {sawmill_type} result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(35.5 <= dist <= 36.5)
        self.assertTrue(29 <= euclidean_dist <= 30)

    def test_calculate_road_distance_pulp_paper(self):
        output_path = "C:/timber_project/outputs/BV_test/test_nd_path_1.shp"
        sawmill_type = "pulp/paper"

        arcpy.management.MakeFeatureLayer(self.harvest_points, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 444"
        )

        euclidean_dist, dist = distance_calculator.calculate_road_dist_only(
            "harvest_site_layer",
            self.network_dataset,
            self.sawmills,
            output_path,
            sawmill_type
        )
        print(f"Test {sawmill_type} result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(66 <= dist <= 67)
        self.assertTrue(53.8 <= euclidean_dist <= 54)

    if __name__ == '__main__':
        unittest.main()