########################################################################################################################
# test_distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Tests the calculate_road_distance function in distance_calculator.py
########################################################################################################################

import unittest
import arcpy, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import distance_calculator

class TestDistanceCalculator(unittest.TestCase):
    def test_calculate_distances_from_exit_1(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_test"
        arcpy.env.overwriteOutput = True

        roads_raster = "roads_raster.tif"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_path_1.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 1878"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 0"
        )

        dist = distance_calculator.calculate_road_distance(
            "exit_points_layer", roads_raster, "sawmill_layer", output_path
        )
        print("Test 1 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 6.1 miles
        self.assertTrue(6.0 < dist < 6.2)

    def test_calculate_distances_from_exit_2(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_test"
        arcpy.env.overwriteOutput = True

        roads_raster = "roads_raster.tif"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_path_2.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 0"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 3"
        )

        dist = distance_calculator.calculate_road_distance(
            "exit_points_layer", roads_raster, "sawmill_layer", output_path
        )
        print("Test 2 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 13.6
        self.assertTrue(13.5 < dist < 13.7)

    def test_calculate_distances_from_exit_3(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_test"
        arcpy.env.overwriteOutput = True

        roads_raster = "roads_raster.tif"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_path_3.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 3295"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 21"
        )

        dist = distance_calculator.calculate_road_distance(
            "exit_points_layer", roads_raster, "sawmill_layer", output_path
        )
        print("Test 3 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        # actual road distance: 19.5 miles
        self.assertTrue(19.4 < dist < 19.6)

    def test_calculate_distances_from_exit_4(self):
        arcpy.env.workspace = "F:/timber_project/scratch/MS_test"
        arcpy.env.overwriteOutput = True

        roads_raster = "roads_raster.tif"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"
        output_path = "F:/timber_project/outputs/MS_test/test_path_4.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 	3600"
        )
        arcpy.management.MakeFeatureLayer(sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByAttribute(
            "sawmill_layer", "NEW_SELECTION", "FID = 10"
        )

        dist = distance_calculator.calculate_road_distance(
            "exit_points_layer", roads_raster, "sawmill_layer", output_path
        )
        print("Test 4 result: " + str(dist))
        arcpy.management.Delete("exit_points_layer")
        arcpy.management.Delete("sawmill_layer")
        #actual road distance: 339 miles
        self.assertTrue(334 < dist < 344)

    if __name__ == '__main__':
        unittest.main()