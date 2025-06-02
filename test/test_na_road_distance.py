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
    def test_calculate_distances_from_exit_1(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_test"
        arcpy.env.overwriteOutput = True

        network_dataset = "MS_test.gdb/Transportation/ms_streets_nd"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_nd_path_1.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 1878"
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
        self.assertTrue(6.0 < dist < 6.2)