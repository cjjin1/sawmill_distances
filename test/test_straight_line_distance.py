################################################################################class TestDistanceCalculator(unittest.TestCase):########################################
# test_straight_line_distance.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Tests the calculate_straight_line_distance function in distance_calculator.py
########################################################################################################################

import unittest
import arcpy, sys, os

from distance_calculator import *

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import distance_calculator

class TestStraightLineDistance(unittest.TestCase):
    def test_euclidean_distance_haversine_1(self):
        arcpy.env.workspace = "F:/timber_project/scratch/"
        arcpy.env.overwriteOutput = True

        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 1878"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 0"
        )

        dist = euclidean_distance_haversine("exit_points_layer", "sawmill_layer", 3955.7439)
        print("Test 1 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        self.assertTrue(4.92 < dist < 4.94)

    def test_euclidean_distance_haversine_2(self):
        arcpy.env.workspace = "F:/timber_project/scratch/"
        arcpy.env.overwriteOutput = True

        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 3600"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 10"
        )

        dist = euclidean_distance_haversine("exit_points_layer", "sawmill_layer", 3955.7439)
        print("Test 2 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        self.assertTrue(276 < dist < 277)

    def test_euclidean_distance_near_1(self):
        arcpy.env.workspace = "F:/timber_project/scratch/"
        arcpy.env.overwriteOutput = True

        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 1878"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 0"
        )

        point_1 = "F:/timber_project/outputs/test_point_1_near1.shp"
        point_2 = "F:/timber_project/outputs/test_point_2_near1.shp"
        arcpy.CopyFeatures_management("exit_points_layer", point_1)
        arcpy.CopyFeatures_management("sawmill_layer", point_2)

        dist = distance_calculator.euclidean_distance_near(point_1, point_2)
        print("Test 3 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        self.assertTrue(4.92 < dist < 4.93)

    def test_euclidean_distance_near_2(self):
        arcpy.env.workspace = "F:/timber_project/scratch/"
        arcpy.env.overwriteOutput = True

        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 3600"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 10"
        )

        point_1 = "F:/timber_project/outputs/test_point_1_near2.shp"
        point_2 = "F:/timber_project/outputs/test_point_2_near2.shp"
        arcpy.CopyFeatures_management("exit_points_layer", point_1)
        arcpy.CopyFeatures_management("sawmill_layer", point_2)

        dist = distance_calculator.euclidean_distance_near(point_1, point_2)
        print("Test 4 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        self.assertTrue(276.2 < dist < 276.3)
