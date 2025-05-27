########################################################################################################################
# test_distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Tests the calculate_distances_from_exit function in distance_calculator.py
########################################################################################################################

import unittest
import arcpy, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import distance_calculator

class TestDistanceCalculator(unittest.TestCase):
    def test_calculate_distances_from_exit_1(self):
        arcpy.env.workspace = "F:/timber_project/scratch/"
        arcpy.env.overwriteOutput = True

        roads_raster = "roads_raster.tif"
        sawmills = "sawmills_adjusted.shp"
        exit_points = "NFS_adjusted_exit_points.shp"

        arcpy.management.MakeFeatureLayer(exit_points, "exit_points_layer")
        arcpy.management.SelectLayerByAttribute(
            "exit_points_layer", "NEW_SELECTION", "FID = 1878"
        )
        dist = distance_calculator.calculate_distance_from_exit("exit_points_layer", roads_raster, sawmills)
        self.assertTrue(arcpy.Exists("paths.shp"))
        self.assertTrue(6.0 < dist < 6.2)

    if __name__ == '__main__':
        unittest.main()