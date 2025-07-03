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
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        self.network_dataset = "Transportation/streets_nd"
        self.roads_dataset = "Transportation/all_roads_fixed"
        self.sawmills = "sawmills_bounded"
        self.harvest_sites = "harvest_sites_bounded"
        self.slope_raster = "slope_raster"
        self.ofa = "off_limit_areas"

    def test_calculate_road_distance_nd_1(self):
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_1.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 444"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "OBJECTID = 48"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            "sawmill_layer",
            self.slope_raster,
            self.ofa,
            output_path
        )
        print(f"Test 1 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        self.assertTrue(56 <= dist <= 57)
        self.assertTrue(43.8 <= euclidean_dist <= 44)

    def test_calculate_road_distance_nd_2(self):
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_2.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 3576"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "OBJECTID = 3"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            "sawmill_layer",
            self.slope_raster,
            self.ofa,
            output_path
        )
        print(f"Test 2 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        self.assertTrue(5.0 <= dist <= 5.5)
        self.assertTrue(1.1 <= euclidean_dist <= 1.2)

    def test_calculate_road_distance_nd_3(self):
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_3.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 868"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "OBJECTID = 79"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            "sawmill_layer",
            self.slope_raster,
            self.ofa,
            output_path
        )
        print(f"Test 3 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        self.assertTrue(164 <= dist <= 165)
        self.assertTrue(150.2 <= euclidean_dist <= 150.4)

    def test_calculate_road_distance_nd_4(self):
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_4.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 5305"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "OBJECTID = 63"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            "sawmill_layer",
            self.slope_raster,
            self.ofa,
            output_path
        )
        print(f"Test 4 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f} ")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(10.5 <= dist <= 11)
        self.assertTrue(8.3 <= euclidean_dist <= 8.6)

    def test_calculate_road_distance_nd_closest_chip(self):
        output_path = "E:/timber_project/outputs/BV_test/test_chip.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 5305"
        )
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            self.sawmills,
            self.slope_raster,
            self.ofa,
            output_path,
            "chip"
        )
        print(f"Closest chip sawmill result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(40.5 <= dist <= 41)
        self.assertTrue(34 <= euclidean_dist <= 34.5)

    def test_calculate_road_distance_nd_closest_lumber(self):
        output_path = "E:/timber_project/outputs/BV_test/test_lumber.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 5305"
        )
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            self.sawmills,
            self.slope_raster,
            self.ofa,
            output_path,
            "lumber"
        )
        print(f"Closest lumber sawmill result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(10.5 <= dist <= 11)
        self.assertTrue(8.3 <= euclidean_dist <= 8.6)

    def test_calculate_road_distance_nd_closest_mass_timber(self):
        output_path = "E:/timber_project/outputs/BV_test/test_mass_timber.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 5305"
        )
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            self.sawmills,
            self.slope_raster,
            self.ofa,
            output_path,
            "mass timber"
        )
        print(f"Closest mass timber sawmill result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(72.5 <= dist <= 73)
        self.assertTrue(57.2 <= euclidean_dist <= 57.6)

    def test_calculate_road_distance_nd_closest_OSB(self):
        output_path = "E:/timber_project/outputs/BV_test/test_OSB.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 5305"
        )
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            self.sawmills,
            self.slope_raster,
            self.ofa,
            output_path,
            "OSB"
        )
        print(f"Closest OSB sawmill result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(172 <= dist <= 173)
        self.assertTrue(157 <= euclidean_dist <= 158)

    def test_calculate_road_distance_nd_closest_panel(self):
        output_path = "E:/timber_project/outputs/BV_test/test_panel.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 5305"
        )
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            self.sawmills,
            self.slope_raster,
            self.ofa,
            output_path,
            "panel"
        )
        print(f"Closest panel sawmill result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(59 <= dist <= 60)
        self.assertTrue(49 <= euclidean_dist <= 50)

    def test_calculate_road_distance_nd_closest_pellet(self):
        output_path = "E:/timber_project/outputs/BV_test/test_pellet.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 5305"
        )
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            self.sawmills,
            self.slope_raster,
            self.ofa,
            output_path,
            "pellet"
        )
        print(f"Closest pellet sawmill result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(63 <= dist <= 64)
        self.assertTrue(51 <= euclidean_dist <= 52)

    def test_calculate_road_distance_nd_closest_plywoood_veneer(self):
        output_path = "E:/timber_project/outputs/BV_test/test_plywoood_veneer.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 5305"
        )
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            self.sawmills,
            self.slope_raster,
            self.ofa,
            output_path,
            "plywood/veneer"
        )
        print(f"Closest plywood/veneer sawmill result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(39 <= dist <= 40)
        self.assertTrue(32 <= euclidean_dist <= 32.5)

    def test_calculate_road_distance_nd_closest_pulp_paper(self):
        output_path = "E:/timber_project/outputs/BV_test/test_pulp_paper.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 5305"
        )
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            self.sawmills,
            self.slope_raster,
            self.ofa,
            output_path,
            "pulp/paper"
        )
        print(f"Closest pulp/paper sawmill result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(65.5 <= dist <= 66.5)
        self.assertTrue(55.5 <= euclidean_dist <= 56.5)

    def test_oneway_1(self):
        output_path = "E:/timber_project/outputs/BV_test/test_oneway_closest.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 395"
        )
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            self.sawmills,
            self.slope_raster,
            self.ofa,
            output_path
        )
        arcpy.management.Delete("harvest_site_layer")
        print(f"Oneway test result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(8.5 <= dist <= 9)

    def test_oneway_2(self):
        output_path = "E:/timber_project/outputs/BV_test/test_oneway_set.shp"

        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 395"
        )
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "OBJECTID = 63"
        )
        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer",
            self.roads_dataset,
            self.network_dataset,
            "sawmill_layer",
            self.slope_raster,
            self.ofa,
            output_path
        )
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        print(f"Oneway test result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}")
        self.assertTrue(arcpy.Exists(output_path))
        self.assertTrue(8.5 <= dist <= 9)

    if __name__ == '__main__':
        unittest.main()