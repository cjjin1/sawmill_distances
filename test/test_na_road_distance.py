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
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        network_dataset = "Transportation/streets_nd"
        roads_dataset = "Transportation/all_roads"
        sawmills = "sawmills_bounded"
        harvest_sites = "harvest_sites_bounded"
        slope_raster = "slope_raster"
        ofa = "off_limit_areas"
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_1.shp"
        closest_output_path = "E:/timber_project/outputs/BV_test/test_closest_nd_path_1.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 283"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "OBJECTID = 1"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, "sawmill_layer", slope_raster, ofa, output_path
        )
        closest_dist, euclidean_closest_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, closest_output_path
        )
        print(f"Test 1 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}  " +
              f"Test 1 closest result: {closest_dist:.4f}, Euclidean: {euclidean_closest_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 9.4 miles
        # original tested distance: 9.2127
        # with slope: 9.2894
        self.assertEquals(dist, closest_dist)
        self.assertEquals(euclidean_dist, euclidean_closest_dist)
        self.assertTrue(9.1 <= dist <= 9.5)
        self.assertTrue(9.1 <= closest_dist <= 9.5)

    def test_calculate_road_distance_nd_2(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        network_dataset = "Transportation/streets_nd"
        roads_dataset = "Transportation/all_roads"
        sawmills = "sawmills_bounded"
        harvest_sites = "harvest_sites_bounded"
        slope_raster = "slope_raster"
        ofa = "off_limit_areas"
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_2.shp"
        closest_output_path = "E:/timber_project/outputs/BV_test/test_closest_nd_path_2.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 1252"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "OBJECTID = 1"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, "sawmill_layer", slope_raster, ofa, output_path
        )
        closest_dist, euclidean_closest_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, closest_output_path
        )
        print(f"Test 2 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}  " +
              f"Test 2 closest result: {closest_dist:.4f}, Euclidean: {euclidean_closest_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 4.8
        # original tested distance: 4.7566
        # with slope: 4.7479
        self.assertTrue(4.6 <= dist <= 5.0)
        self.assertTrue(4.6 <= closest_dist <= 5.0)
        self.assertEquals(dist, closest_dist)
        self.assertEquals(euclidean_dist, euclidean_closest_dist)

    def test_calculate_road_distance_nd_3(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        network_dataset = "Transportation/streets_nd"
        roads_dataset = "Transportation/all_roads"
        sawmills = "sawmills_bounded"
        harvest_sites = "TimberHarvestBienville"
        slope_raster = "slope_raster"
        ofa = "off_limit_areas"
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_3.shp"
        closest_output_path = "E:/timber_project/outputs/BV_test/test_closest_nd_path_3.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 102"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "OBJECTID = 25"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, "sawmill_layer", slope_raster, ofa, output_path
        )
        closest_dist, euclidean_closest_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, closest_output_path
        )
        print(f"Test 3 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}  " +
              f"Test 3 closest result: {closest_dist:.4f}, Euclidean: {euclidean_closest_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 17.95
        # original tested distance: 18.0467
        # with slope: 18.0748
        self.assertTrue(17.4 <= dist <= 18.1)
        self.assertTrue(17.4 <= closest_dist <= 18.1)
        self.assertEquals(dist, closest_dist)
        self.assertEquals(euclidean_dist, euclidean_closest_dist)

    def test_calculate_road_distance_nd_4(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        network_dataset = "Transportation/streets_nd"
        roads_dataset = "Transportation/all_roads"
        sawmills = "sawmills_bounded"
        harvest_sites = "harvest_sites_bounded"
        slope_raster = "slope_raster"
        ofa = "off_limit_areas"
        output_path = "E:/timber_project/outputs/BV_test/test_nd_path_4.shp"
        closest_output_path = "E:/timber_project/outputs/BV_test/test_closest_nd_path_4.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 435"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "OBJECTID = 25"
        )

        dist, euclidean_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, "sawmill_layer", slope_raster, ofa, output_path
        )
        closest_dist, euclidean_closest_dist = distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, closest_output_path
        )
        print(f"Test 4 result: {dist:.4f}, Euclidean: {euclidean_dist:.4f}  " +
              f"Test 4 closest result: {closest_dist:.4f}, Euclidean: {euclidean_closest_dist:.4f}")
        arcpy.management.Delete("harvest_site_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 23.6
        # original tested distance: 23.5254
        # with slope: 23.5535
        self.assertTrue(23.3 <= dist <= 23.6)
        self.assertTrue(23.3 <= closest_dist <= 23.6)
        self.assertEquals(dist, closest_dist)
        self.assertEquals(euclidean_dist, euclidean_closest_dist)

    def test_concerns(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        network_dataset = "Transportation/streets_nd"
        roads_dataset = "Transportation/all_roads"
        sawmills = "sawmills_bounded"
        harvest_sites = "TimberHarvestBienville"
        slope_raster = "slope_raster"
        ofa = "off_limit_areas"
        output_path_1 = "E:/timber_project/outputs/BV_test/test_concerns_1.shp"
        output_path_2 = "E:/timber_project/outputs/BV_test/test_concerns_2.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 101"
        )
        distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, output_path_1
        )
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 75"
        )
        distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, output_path_2
        )
        self.assertTrue(arcpy.Exists(output_path_1) and arcpy.Exists(output_path_2))

    def test_off_limit_overlap_1(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        network_dataset = "Transportation/streets_nd"
        roads_dataset = "Transportation/all_roads"
        sawmills = "sawmills_bounded"
        harvest_sites = "harvest_sites_bounded"
        slope_raster = "slope_raster"
        ofa = "off_limit_areas"
        output_path_1 = "E:/timber_project/outputs/BV_test/test_overlap_1.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 1003"
        )
        distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, output_path_1
        )
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path_1))

    def test_off_limit_overlap_2(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        network_dataset = "Transportation/streets_nd"
        roads_dataset = "Transportation/all_roads"
        sawmills = "sawmills_bounded"
        harvest_sites = "harvest_sites_bounded"
        slope_raster = "slope_raster"
        ofa = "off_limit_areas"
        output_path_2 = "E:/timber_project/outputs/BV_test/test_overlap_2.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 1343"
        )
        distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, output_path_2
        )
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path_2))

    def test_off_limit_overlap_3(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        network_dataset = "Transportation/streets_nd"
        roads_dataset = "Transportation/all_roads"
        sawmills = "sawmills_bounded"
        harvest_sites = "harvest_sites_bounded"
        slope_raster = "slope_raster"
        ofa = "off_limit_areas"
        output_path_3 = "E:/timber_project/outputs/BV_test/test_overlap_3.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 556"
        )
        distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, output_path_3
        )
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path_3))

    def test_off_limit_overlap_4(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        network_dataset = "Transportation/streets_nd"
        roads_dataset = "Transportation/all_roads"
        sawmills = "sawmills_bounded"
        harvest_sites = "harvest_sites_bounded"
        slope_raster = "slope_raster"
        ofa = "off_limit_areas"
        output_path_4 = "E:/timber_project/outputs/BV_test/test_overlap_4.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 207"
        )
        distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, output_path_4
        )
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path_4))

    def test_off_limit_overlap_5(self):
        arcpy.env.workspace = "E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb"
        arcpy.env.overwriteOutput = True

        network_dataset = "Transportation/streets_nd"
        roads_dataset = "Transportation/all_roads"
        sawmills = "sawmills_bounded"
        harvest_sites = "harvest_sites_bounded"
        slope_raster = "slope_raster"
        ofa = "off_limit_areas"
        output_path_5 = "E:/timber_project/outputs/BV_test/test_overlap_5.shp"

        arcpy.management.MakeFeatureLayer(harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer", "NEW_SELECTION", "OBJECTID = 344"
        )
        distance_calculator.calculate_distance(
            "harvest_site_layer", roads_dataset, network_dataset, sawmills, slope_raster, ofa, output_path_5
        )
        arcpy.management.Delete("harvest_site_layer")
        self.assertTrue(arcpy.Exists(output_path_5))

    if __name__ == '__main__':
        unittest.main()