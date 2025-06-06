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
        arcpy.env.workspace = "F:/timber_project/scratch/MS_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "MS_OSM_ND.gdb/Transportation/streets_nd"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_nd_path_1.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 1190"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 0"
        )

        dist = distance_calculator.calculate_road_distance_nd(
            "exit_points_layer", network_dataset, "sawmill_layer", output_path
        )
        print("Test 1 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 6.1 miles
        self.assertTrue(dist <= 6.3)

    def test_calculate_road_distance_nd_2(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "MS_OSM_ND.gdb/Transportation/streets_nd"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_nd_path_2.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 0"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 3"
        )

        dist = distance_calculator.calculate_road_distance_nd(
            "exit_points_layer", network_dataset, "sawmill_layer", output_path
        )
        print("Test 2 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 13.6
        self.assertTrue(dist <= 13.8)

    def test_calculate_road_distance_nd_3(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "MS_OSM_ND.gdb/Transportation/streets_nd"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_nd_path_3.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 2119"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 21"
        )

        dist = distance_calculator.calculate_road_distance_nd(
            "exit_points_layer", network_dataset, "sawmill_layer", output_path
        )
        print("Test 3 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 19.5 miles
        self.assertTrue(dist <= 19.7)

    def test_calculate_road_distance_nd_4(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "MS_OSM_ND.gdb/Transportation/streets_nd"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_nd_path_4.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 2325"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 10"
        )

        dist = distance_calculator.calculate_road_distance_nd(
            "exit_points_layer", network_dataset, "sawmill_layer", output_path
        )
        print("Test 4 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        #actual road distance: 339 miles
        self.assertTrue(dist <= 340)

    def test_calculate_road_distance_nd_5(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "MS_OSM_ND.gdb/Transportation/streets_nd"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_nd_path_5.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 3297"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 20"
        )

        dist = distance_calculator.calculate_road_distance_nd(
            "exit_points_layer", network_dataset, "sawmill_layer", output_path
        )
        print("Test 5 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 153 miles
        self.assertTrue(dist <= 154)

    def test_calculate_road_distance_nd_6(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "MS_OSM_ND.gdb/Transportation/streets_nd"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_nd_path_6.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 737"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 11"
        )

        dist = distance_calculator.calculate_road_distance_nd(
            "exit_points_layer", network_dataset, "sawmill_layer", output_path
        )
        print("Test 6 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 45.0 miles
        self.assertTrue(dist <= 45.2)

    def test_calculate_road_distance_nd_7(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "MS_OSM_ND.gdb/Transportation/streets_nd"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_nd_path_7.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 609"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 	36"
        )

        dist = distance_calculator.calculate_road_distance_nd(
            "exit_points_layer", network_dataset, "sawmill_layer", output_path
        )
        print("Test 7 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 30.5 miles
        self.assertTrue(dist <= 30.7)

    def test_calculate_road_distance_nd_8(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_OSM_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "MS_OSM_ND.gdb/Transportation/streets_nd"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_nd_path_8.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 450"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 2"
        )

        dist = distance_calculator.calculate_road_distance_nd(
            "exit_points_layer", network_dataset, "sawmill_layer", output_path
        )
        print("Test 8 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 71.4 miles
        self.assertTrue(dist <= 71.6)

    if __name__ == '__main__':
        unittest.main()