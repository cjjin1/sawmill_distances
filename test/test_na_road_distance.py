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
    def test_calculate_road_distance_nd_1(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "BV_ND.gdb/Transportation/streets_nd"
        roads_dataset = "BV_ND.gdb/Transportation/all_roads"
        sawmills = "sawmills_adjusted.shp"
        harvest_sites = "TimberHarvestBienville.shp"
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_1.shp"
        closest_output_path = "E:/timber_project/outputs/BV_test/test_closest_nd_path_1.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "FID = 62"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 0"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, "sawmill_layer", output_path
        )
        closest_dist, euclidean_closest_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, closest_output_path
        )
        print(f"Test 2 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}  " +
              f"Test 2 closest result: {closest_dist:.4f}, Euclidean: {euclidean_closest_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 9.4 miles
        self.assertEquals(dist, closest_dist)
        self.assertEquals(euclidean_dist, euclidean_closest_dist)
        self.assertTrue(9.1 <= dist <= 9.5)
        self.assertTrue(9.1 <= closest_dist <= 9.5)

    def test_calculate_road_distance_nd_2(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "BV_ND.gdb/Transportation/streets_nd"
        roads_dataset = "BV_ND.gdb/Transportation/all_roads"
        sawmills = "sawmills_adjusted.shp"
        harvest_sites = "TimberHarvestBienville.shp"
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_2.shp"
        closest_output_path = "E:/timber_project/outputs/BV_test/test_closest_nd_path_2.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "FID = 78"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 0"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, "sawmill_layer", output_path
        )
        closest_dist, euclidean_closest_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, closest_output_path
        )
        print(f"Test 2 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}  " +
              f"Test 2 closest result: {closest_dist:.4f}, Euclidean: {euclidean_closest_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 4.8
        self.assertTrue(5.0 <= dist <= 5.4)
        self.assertTrue(5.0 <= closest_dist <= 5.4)
        self.assertEquals(dist, closest_dist)
        self.assertEquals(euclidean_dist, euclidean_closest_dist)

    def test_calculate_road_distance_nd_3(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "BV_ND.gdb/Transportation/streets_nd"
        roads_dataset = "BV_ND.gdb/Transportation/all_roads"
        sawmills = "sawmills_adjusted.shp"
        harvest_sites = "TimberHarvestBienville.shp"
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_3.shp"
        closest_output_path = "E:/timber_project/outputs/BV_test/test_closest_nd_path_3.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "FID = 101"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 24"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, "sawmill_layer", output_path
        )
        closest_dist, euclidean_closest_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, closest_output_path
        )
        print(f"Test 2 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}  " +
              f"Test 2 closest result: {closest_dist:.4f}, Euclidean: {euclidean_closest_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 17.95
        self.assertTrue(17.4 <= dist <= 18.1)
        self.assertTrue(17.4 <= closest_dist <= 18.1)
        self.assertEquals(dist, closest_dist)
        self.assertEquals(euclidean_dist, euclidean_closest_dist)

    def test_calculate_road_distance_nd_4(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "BV_ND.gdb/Transportation/streets_nd"
        roads_dataset = "BV_ND.gdb/Transportation/all_roads"
        sawmills = "sawmills_adjusted.shp"
        harvest_sites = "TimberHarvestBienville.shp"
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_4.shp"
        closest_output_path = "E:/timber_project/outputs/BV_test/test_closest_nd_path_4.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "FID = 69"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 24"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, "sawmill_layer", output_path
        )
        closest_dist, euclidean_closest_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, closest_output_path
        )
        print(f"Test 2 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}  " +
              f"Test 2 closest result: {closest_dist:.4f}, Euclidean: {euclidean_closest_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 23.6
        self.assertTrue(23.3 <= dist <= 23.6)
        self.assertTrue(23.3 <= closest_dist <= 23.6)
        self.assertEquals(dist, closest_dist)
        self.assertEquals(euclidean_dist, euclidean_closest_dist)

    def test_concerns(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "BV_ND.gdb/Transportation/streets_nd"
        roads_dataset = "BV_ND.gdb/Transportation/all_roads"
        sawmills = "sawmills_adjusted.shp"
        harvest_sites = "TimberHarvestBienville.shp"
        output_path_1 = "E:/timber_project/outputs/BV_test/test_concerns_1.shp"
        output_path_2 = "E:/timber_project/outputs/BV_test/test_concerns_2.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "FID = 100"
        )
        distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset,sawmills, output_path_1
        )
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "FID = 74"
        )
        distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset,sawmills, output_path_2
        )
        self.assertTrue(arcpy.Exists(output_path_1) and arcpy.Exists(output_path_2))

    if __name__ == '__main__':
        unittest.main()