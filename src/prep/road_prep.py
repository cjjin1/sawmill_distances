########################################################################################################################
# data_prep.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Shortened version of data_prep.py, only imports the OSM road output and prepares it for network dataset
#          creation.
#
# Usage: <workspace (file gdb)> <OSM road data>
#
# IMPORTANT: The workspace must be a non-existent File GDB within an existing directory. This is because the
#            Data Interoperability tool 'Quick Import' creates a new File GDB and cannot import into an existing
#            File GDB. The created File GDB will serve as the workspace for this script and where all the resulting
#            feature classes will be placed.
########################################################################################################################

import sys, arcpy, os

class DataPrep:
    def __init__(self, workspace=None, total_roads=None):
        self.workspace = workspace
        self.total_roads = total_roads
        self.transport_dataset = "Transportation"
        self.complete_roads = None

    def create_new_file_gdb(self):
        """Uses the quick import tool from Data Interoperability to create a new File GDB with roads data"""
        if not arcpy.Exists(os.path.join(self.workspace, os.path.basename(self.total_roads))):
            if not os.path.isdir(os.path.dirname(self.workspace)):
                raise arcpy.ExecuteError(f"{self.workspace} is not placed in an existing directory.")
            arcpy.CheckOutExtension("DataInteroperability")
            arcpy.gp.QuickImport_interop(os.path.dirname(self.total_roads), self.workspace)
            arcpy.CheckInExtension("DataInteroperability")
        else:
            raise arcpy.ExecuteError(f"{self.workspace} already exists. Please provide a name for a new file GDB.")
        self.total_roads = os.path.join(self.workspace, os.path.basename(self.total_roads))

        if not arcpy.Exists(os.path.join(self.workspace, self.transport_dataset)):
            arcpy.management.CreateFeatureDataset(self.workspace, self.transport_dataset, 4326)

    def create_road_fc(self, keep_temp=False):
        """Cleans and merges the roads feature classes, then creates a network dataset out of the result"""
        # deletes network dataset if it already exists
        if arcpy.Exists(os.path.join(self.workspace, self.transport_dataset, "streets_nd")):
            arcpy.management.Delete(os.path.join(self.workspace, self.transport_dataset, "streets_nd"))
            arcpy.management.Delete(os.path.join(self.workspace, self.transport_dataset, "streets_nd_Junctions"))

        # set workspace to transportation feature dataset
        arcpy.env.workspace = os.path.join(self.workspace, self.transport_dataset)
        self.complete_roads = "nd_" + os.path.basename(self.total_roads)
        arcpy.management.FeatureToLine(self.total_roads, self.complete_roads)
        arcpy.management.RepairGeometry(self.complete_roads)

        # add and calculate distance field
        arcpy.management.AddField(self.complete_roads, "distance", "DOUBLE")
        arcpy.management.CalculateGeometryAttributes(
            self.complete_roads, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
        )

        # add and calculate travel time field
        arcpy.management.AddField(self.complete_roads, "travel_time", "DOUBLE")
        fields = ["distance", "maxspeed", "travel_time"]
        with arcpy.da.UpdateCursor(self.complete_roads, fields) as uc:
            for row in uc:
                row[2] = float(row[0]) / float(row[1])
                uc.updateRow(row)

        if not keep_temp:
            arcpy.management.Delete(self.total_roads)

    def process(self):
        """Starts and runs the process of preparing data"""
        arcpy.AddMessage("Beginning Data Preparation")
        arcpy.AddMessage("Importing Road Data and Creating File GDB")
        self.create_new_file_gdb()

        arcpy.env.workspace = self.workspace
        arcpy.env.overwriteOutput = True

        arcpy.AddMessage("Combining All Road Feature Classes")
        self.create_road_fc(keep_temp=True)

        arcpy.AddMessage("Creating Network Dataset")
        arcpy.na.CreateNetworkDataset(
            os.path.join(self.workspace, self.transport_dataset),
            "streets_nd",
            self.complete_roads,
            "NO_ELEVATION"
        )

def main():
    """Main function to run data preparation script"""
    workspace = sys.argv[1]
    total_roads = sys.argv[2]

    data_prepper = DataPrep(workspace=workspace, total_roads=total_roads)

    data_prepper.process()
    print("Finished preparing data")

if __name__ == "__main__":
    main()
