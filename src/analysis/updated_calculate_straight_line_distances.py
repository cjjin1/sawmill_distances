########################################################################################################################
# calculate_straight_line_distances.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates the straight line distances from each harvest site to every sawmill of each type
########################################################################################################################

import sys, arcpy, os, random
import datetime
import csv

class StraightLineDistanceCalculator:

    def __init__(self, sawmills, harv_sites, out_csv, subset_size, workspace):
        """Initializes the attributes and sets workspace"""
        self.sawmills = sawmills
        self.harvest_sites = harv_sites
        self.id = "OBJECTID"
        if self.harvest_sites.endswith(".shp"):
            self.id = "FID"
        self.harvest_sites_subset = f"{harv_sites}_subset"
        self.out_csv = out_csv
        self.out_dir = os.path.dirname(out_csv)
        if self.out_csv == "#":
            self.out_dir = "#"
        self.subset_size = subset_size
        self.workspace = workspace
        self.sm_types = [
            "Lumber/Solid Wood",
            "Pellet",
            "Chip",
            "Pulp/Paper",
            "Composite Panel/Engineered Wood Product",
            "Plywood/Veneer"
        ]

        # set workspace
        arcpy.env.workspace = self.workspace
        arcpy.env.overwriteOutput = True

    def subset_sites(self):
        """Creates a random subset of sites"""
        sc = arcpy.da.SearchCursor(self.harvest_sites, ["OBJECTID"])
        id_list = []
        for row in sc:
            id_list.append(row[0])
        del row, sc

        rand_id_list = random.sample(id_list, self.subset_size)
        where_clause = f"{self.id} IN ({','.join(map(str, rand_id_list))})"
        arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
        arcpy.management.SelectLayerByAttribute(
            "harvest_site_layer",
            "NEW_SELECTION",
            where_clause,
        )
        arcpy.management.CopyFeatures("harvest_site_layer", self.harvest_sites_subset)
        self.harvest_sites = self.harvest_sites_subset

    def create_output_dir(self):
        """Sets up the output directory if it doesn't exist or if one was not given"""
        if self.out_dir != "#":
            if not os.path.exists(self.out_dir):
                os.makedirs(self.out_dir)
        else:
            output_dir = self.workspace + "/../" + "outputs/straight_line_distances"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

    def calculate_sl_distances(self):
        """Calculates straight line distance from every harvest site to every sawmill for every sawmill type"""
        if self.out_csv == "#":
            self.out_csv = os.path.join(
                self.out_dir, f"sl_distances_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            )
        sl_out = open(self.out_csv, "w+", newline="\n")
        sl_writer = csv.writer(sl_out)

        # calculate the distance for every harvest site to every type of sawmill
        arcpy.AddMessage("Starting Straight Line Distance Calculations")
        with arcpy.da.SearchCursor(self.harvest_sites, [f"{self.id}"]) as sc:
            arcpy.management.MakeFeatureLayer(self.harvest_sites, "harvest_site_layer")
            for row in sc:
                arcpy.management.SelectLayerByAttribute(
                    "harvest_site_layer", "NEW_SELECTION", f"{self.id} = {row[0]}"
                )
                arcpy.analysis.Near(
                    self.sawmills,
                    "harvest_site_layer",
                    "120 Miles",
                    method="PLANAR",
                    distance_unit="Miles"
                )
                arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
                for sm_t in self.sm_types:
                    # sort by mill type and ensure distance is valid
                    arcpy.management.SelectLayerByAttribute(
                        "sawmill_layer",
                        "NEW_SELECTION",
                        f"Mill_Type = '{sm_t}' AND NEAR_DIST >= 0"
                    )
                    # get lowest straight line distance and id of nearest sawmill
                    with arcpy.da.SearchCursor(
                        "sawmill_layer",
                        ["OBJECTID", "NEAR_DIST", "Mill_Type"],
                        sql_clause=(None, "ORDER BY NEAR_DIST ASC")
                    ) as sc2:
                        for n_fid, n_dist, m_type in sc2:
                            sl_writer.writerow([sm_t, row[0], n_fid, n_dist])
                            break

                print(f"{row[0]} distances completed")
                arcpy.management.Delete("sawmill_layer")
            arcpy.management.Delete("harvest_site_layer")
        sl_out.close()

    def process(self):
        """Runs the process for calculating straight line distances"""
        if self.subset_size > 0:
            self.subset_sites()
        self.create_output_dir()
        self.calculate_sl_distances()

def main():
    sawmills = sys.argv[1]
    harvest_sites = sys.argv[2]
    output_csv = sys.argv[3]
    try:
        subset_size = int(sys.argv[4])
        if subset_size < 1:
            arcpy.AddMessage("Invalid subset size, harvest site feature class will not be subset.")
            subset_size = 0
    except ValueError:
        arcpy.AddWarning("Invalid subset size, harvest site feature class will not be subset.")
        subset_size = 0
    try:
        proj = arcpy.mp.ArcGISProject("CURRENT")
        workspace = proj.defaultGeodatabase
    except OSError:
        workspace = sys.argv[5]

    calculator = StraightLineDistanceCalculator(sawmills, harvest_sites, output_csv, subset_size, workspace)
    calculator.process()
    arcpy.AddMessage(f"Straight Line Distance CSV can be found at: {os.path.abspath(output_csv)}")

if __name__ == "__main__":
    main()
