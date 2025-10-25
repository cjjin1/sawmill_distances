########################################################################################################################
# data_prep.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Prepares all data necessary for circuity factor analysis in 5 major steps:
#          1. Creating new File GDB for workspace and feature dataset, importing road data (all done with Quick Import)
#          2. Creating boundary feature classes based off of the physiographic region boundary
#          3. Cleaning sawmill data (removing unwanted sawmills)
#          4. Cleaning harvest site data (removing unwanted harvest sites)
#          5. Merging the Forest Service roads with OSM roads.
#
#          It is recommended that all steps be done at the same time but steps 3-5 can be done separately.
#
# Usage: <workspace (file gdb)> <OSM road data> <FS road data> <sawmill data> <harvest site data> <ranger district fc>
#        <physiographic region boundary fc> <spatial reference: epsg code>
#
# IMPORTANT: The workspace must be a non-existent File GDB within an existing directory. This is because the
#            Data Interoperability tool 'Quick Import' creates a new File GDB and cannot import into an existing
#            File GDB. The created File GDB will serve as the workspace for this script and where all the resulting
#            feature classes will be placed.
#
#            Currently, both creation of the workspace File GDB and the boundary feature classes are necessary for the
#            other 3 processes to function, so it is recommended to complete all 5 steps at once.
#
#            Once this script finishes running, there will be steps that must be done within ArcGIS Pro. Restrictions
#            must be manually added to network datasets before they can be used.
########################################################################################################################

import sys, arcpy, os

class DataPrep:
    def __init__(
            self,
            workspace=None,
            total_roads=None,
            nfs_roads=None,
            sawmills=None,
            harvest_sites=None,
            park_boundaries=None,
            physio_boundary=None,
            spat_ref=None
    ):
        self.workspace = workspace
        self.total_roads = total_roads
        self.NFS_roads = nfs_roads
        self.harvest_sites = harvest_sites
        self.sawmills = sawmills
        self.park_boundaries = park_boundaries
        self.physio_boundary = physio_boundary
        self.spat_ref = arcpy.SpatialReference(int(spat_ref))

        self.transport_dataset = "Transportation"
        self.park_roads = os.path.join(self.transport_dataset, "park_roads")
        self.sm_boundaries = "sm_boundaries"
        self.combined_roads = None

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
            arcpy.management.CreateFeatureDataset(self.workspace, self.transport_dataset, self.spat_ref)

    def create_boundary_fcs(self, new_physio=None, new_park_boundaries=None, new_sm_boundaries=None, keep_temp=False):
        """Creates boundary feature classes for sawmills and parks"""
        #project physiographic region boundary and park boundaries
        if new_physio:
            bound_proj = new_physio
        else:
            bound_proj = os.path.basename(self.physio_boundary).split(".")[0]
        if not arcpy.Exists(bound_proj):
            arcpy.management.Project(self.physio_boundary, bound_proj, self.spat_ref)
        self.physio_boundary = bound_proj

        park_boundaries_proj = os.path.basename(self.park_boundaries).split(".")[0] + "_proj"
        if not arcpy.Exists(park_boundaries_proj):
            arcpy.management.Project(self.park_boundaries, park_boundaries_proj, self.spat_ref)
        self.park_boundaries = park_boundaries_proj

        #create boundary for parks
        if new_park_boundaries:
            park_boundaries_clipped = new_park_boundaries
        else:
            park_boundaries_clipped = self.park_boundaries + "_clipped"
        arcpy.analysis.Clip(self.park_boundaries, self.physio_boundary, park_boundaries_clipped)
        self.park_boundaries = park_boundaries_clipped
        if not keep_temp:
            arcpy.management.Delete(park_boundaries_proj)

        #create boundary for sawmills (125 mile buffer)
        if new_sm_boundaries:
            self.sm_boundaries = new_sm_boundaries
        arcpy.analysis.Buffer(
            self.park_boundaries,
            self.sm_boundaries,
            buffer_distance_or_field="125 Miles",
            dissolve_option="ALL"
        )

    def clean_harvest_site_data(self, keep_temp=False):
        """Projects and clips harvest site data. Also removes unwanted polygons that are too small."""
        # project harvest site data and boundary
        hs_proj = os.path.splitext(os.path.basename(self.harvest_sites))[0]
        if not arcpy.Exists(hs_proj):
            arcpy.management.Project(self.harvest_sites, hs_proj, self.spat_ref)

        # extract the harvest site feature class inside the boundary
        arcpy.management.MakeFeatureLayer(hs_proj, "harvest_layer")
        arcpy.management.SelectLayerByLocation(
            "harvest_layer", "WITHIN", self.physio_boundary, selection_type="NEW_SELECTION"
        )

        # filter out for the last 5 years, FS owndership, and accomplished stage description
        where_clause = ("FY_COMPLET >= '2019' AND FY_COMPLET <= '2024' " +
                        "AND OWNERSHIP_ = 'FS' AND STAGE_DESC = 'Accomplished'")
        arcpy.management.SelectLayerByAttribute(
            "harvest_layer",
            "SUBSET_SELECTION",
            where_clause
        )

        hs_bound = "harvest_sites_bounded"
        arcpy.management.CopyFeatures("harvest_layer", hs_bound)
        arcpy.management.Delete("harvest_layer")

        # remove all harvest sites under 60 square feet
        arcpy.management.AddField(hs_bound, "area", "DOUBLE")
        arcpy.management.CalculateGeometryAttributes(
            hs_bound, [["area", "AREA_GEODESIC"]], area_unit="SQUARE_FEET_US"
        )
        uc = arcpy.da.UpdateCursor(hs_bound, ["area"])
        for row in uc:
            if row[0] < 60:
                uc.deleteRow()
        del uc, row

        arcpy.management.Rename(hs_bound, "harvest_sites")
        self.harvest_sites = "harvest_sites"

        if not keep_temp:
            arcpy.management.Delete(hs_proj)

    def clean_sawmill_data(self, keep_temp=False):
        """Projects and clips sawmill data."""
        # project sawmill data and boundary
        sm_proj = os.path.splitext(os.path.basename(self.sawmills))[0]
        if not arcpy.Exists(sm_proj):
            arcpy.management.Project(self.sawmills, sm_proj, self.spat_ref)

        # extract sawmill feature class inside the boundary
        arcpy.management.MakeFeatureLayer(self.sawmills, "sawmill_layer")
        arcpy.management.SelectLayerByLocation(
            "sawmill_layer", "WITHIN", self.sm_boundaries, selection_type="NEW_SELECTION"
        )
        sm_bound = "sawmills_bounded"
        arcpy.management.CopyFeatures("sawmill_layer", sm_bound)
        arcpy.management.Delete("sawmill_layer")

        # reproject copied features to correct spatial reference
        arcpy.management.Project(sm_bound, "sawmills_bounded_proj", self.spat_ref)

        arcpy.management.Rename("sawmills_bounded_proj", "sawmills")
        self.sawmills = "sawmills"
        if not keep_temp:
            arcpy.management.Delete("sawmills_bounded_proj")
            arcpy.management.Delete(sm_bound)
            arcpy.management.Delete(sm_proj)

    def prep_roads(self, keep_temp=False):
        """Projects roads data into new spatial reference, clips roads to create feature class for park roads"""
        # project input roads into the transportation dataset
        roads_basename = os.path.basename(self.total_roads)
        output_path = os.path.join(self.transport_dataset, os.path.basename(self.total_roads) + "_proj")
        if not arcpy.Exists(output_path):
            arcpy.management.Project(self.total_roads, output_path, self.spat_ref)
        self.total_roads = output_path

        #clip roads to the boundaries for sawmills
        clipped_roads = os.path.join(self.transport_dataset, roads_basename + "_clipped")
        if arcpy.Exists(clipped_roads):
            arcpy.management.Delete(clipped_roads)
        arcpy.analysis.Clip(
            self.total_roads,
            self.sm_boundaries,
            clipped_roads
        )
        self.total_roads = clipped_roads

        #clip roads to create park roads
        if arcpy.Exists(self.park_roads):
            arcpy.management.Delete(self.park_roads)
        arcpy.analysis.Clip(
            self.total_roads,
            self.park_boundaries,
            self.park_roads
        )

        #project nfs roads
        if not arcpy.Exists(os.path.splitext(os.path.basename(self.NFS_roads))[0]):
            arcpy.management.Project(
                self.NFS_roads,
                os.path.splitext(os.path.basename(self.NFS_roads))[0],
                self.spat_ref
            )
        self.NFS_roads = os.path.splitext(os.path.basename(self.NFS_roads))[0]

        if not keep_temp:
            arcpy.management.Delete(output_path)
            arcpy.management.Delete(roads_basename)

    def merge_park_roads(self, keep_temp=False):
        """Merge NFS roads and OSM roads to create park roads for any relevant park"""
        # Clip the NFS roads to the boundary
        arcpy.management.MakeFeatureLayer(self.NFS_roads, "NFS_roads")
        arcpy.management.SelectLayerByLocation("NFS_roads", "INTERSECT", self.park_boundaries)
        self.NFS_roads = "NFS_bounded"
        arcpy.management.CopyFeatures("NFS_roads", self.NFS_roads)

        # generate points along each NFS road
        points = "NFS_points"
        arcpy.management.GeneratePointsAlongLines(
            self.NFS_roads, points, "PERCENTAGE", Percentage=4, Include_End_Points="END_POINTS"
        )

        # use Near on points to check for proximity to public roads
        # add a field to indicate if a point is near or not
        arcpy.analysis.Near(points, self.park_roads, search_radius="170 Feet")
        arcpy.management.AddField(points, "IS_NEAR", "SHORT")
        arcpy.management.CalculateField(
            points, "IS_NEAR", "0 if !NEAR_DIST! == -1 else 1", "PYTHON3"
        )

        arcpy.analysis.Near(points, self.park_roads, search_radius="50 Feet")
        arcpy.management.AddField(points, "VERY_NEAR", "SHORT")
        arcpy.management.CalculateField(
            points, "VERY_NEAR", "0 if !NEAR_DIST! == -1 else 1", "PYTHON3"
        )

        # mark every NFS road as a duplicate if more than 20 points is near a public road (> 80%)
        near_dict = {}
        very_near_dict = {}
        arcpy.management.AddField(self.NFS_roads, "DUPLICATE", "SHORT")
        sc = arcpy.da.SearchCursor(points, ["ORIG_FID", "IS_NEAR", "VERY_NEAR"])
        uc = arcpy.da.UpdateCursor(self.NFS_roads, ["OBJECTID", "DUPLICATE"])
        for row in sc:
            if not near_dict.get(row[0]):
                near_dict[row[0]] = row[1]
            else:
                near_dict[row[0]] += row[1]
            if not very_near_dict.get(row[0]):
                very_near_dict[row[0]] = row[2]
            else:
                very_near_dict[row[0]] += row[2]
        del row, sc

        for row in uc:
            if near_dict[row[0]] > 20 and very_near_dict[row[0]] > 5:
                row[1] = 1
            else:
                row[1] = 0
            uc.updateRow(row)
        del row, uc

        # export all NFS roads that are not flagged as duplicates
        arcpy.conversion.ExportFeatures(self.NFS_roads, "NFS_cleaned", "DUPLICATE = 0")
        self.NFS_roads = "NFS_cleaned"

        # get points to snap the NFS roads to
        end_points = "end_points"
        arcpy.management.GeneratePointsAlongLines(
            self.NFS_roads, end_points, Point_Placement="PERCENTAGE", Percentage=100, Include_End_Points="END_POINTS"
        )
        arcpy.analysis.Near(
            end_points,
            self.park_roads,
            search_radius="100 Feet",
            location="LOCATION",
            distance_unit="Miles"
        )
        arcpy.CreateFeatureclass_management(
            arcpy.env.workspace, "road_points", "POINT", spatial_reference=self.spat_ref
        )
        sc = arcpy.da.SearchCursor(end_points, ["SHAPE@", "NEAR_X", "NEAR_Y"])
        ic = arcpy.da.InsertCursor("road_points", ["SHAPE@"])
        for shape, near_x, near_y in sc:
            road_point = arcpy.PointGeometry(arcpy.Point(near_x, near_y), self.spat_ref)
            if near_x != -1 and near_y != -1:
                ic.insertRow([road_point])
        del sc, ic, shape, near_x, near_y

        # remove NFS_roads that won't snap to any public road
        remove_count = 1
        while remove_count > 0:
            remove_count = 0
            arcpy.management.MakeFeatureLayer(end_points, "end_points_neg")
            arcpy.management.SelectLayerByAttribute(
                "end_points_neg", "NEW_SELECTION", "NEAR_DIST = -1"
            )
            arcpy.analysis.SpatialJoin(
                target_features=end_points,
                join_features=self.NFS_roads,
                out_feature_class="spatial_join_output",
                join_operation="JOIN_ONE_TO_ONE",
                join_type="KEEP_ALL",
                match_option="INTERSECT",
                field_mapping="",
                search_radius=None,
                distance_field_name=""
            )
            arcpy.management.MakeFeatureLayer("spatial_join_output", "joined_lyr")
            arcpy.management.SelectLayerByAttribute(
                "joined_lyr", "NEW_SELECTION", '"Join_Count" >= 2'
            )

            orig_fid_dict = {}
            with arcpy.da.SearchCursor("end_points_neg", ["ORIG_FID"]) as sc:
                for row in sc:
                    if orig_fid_dict.get(row[0]):
                        orig_fid_dict[row[0]] += 1
                    else:
                        orig_fid_dict[row[0]] = 1

            with arcpy.da.SearchCursor("joined_lyr", ["ORIG_FID"]) as sc:
                for row in sc:
                    if orig_fid_dict.get(row[0]) and orig_fid_dict[row[0]] == 2:
                        orig_fid_dict[row[0]] -= 1

            with arcpy.da.UpdateCursor(self.NFS_roads, ["OBJECTID"]) as uc:
                for row in uc:
                    if orig_fid_dict.get(row[0]) and orig_fid_dict[row[0]] == 2:
                        uc.deleteRow()
                        remove_count += 1
            arcpy.management.Delete("joined_lyr")
            arcpy.management.Delete("spatial_join_output")
            arcpy.management.Delete("end_points_neg")

        # snap the cleaned NFS roads to the points on the public roads
        arcpy.edit.Snap(self.NFS_roads, [["road_points", "VERTEX", "100 Feet"]])

        # merge the two roads datasets
        output_roads = "all_roads"
        arcpy.management.Merge([self.park_roads, self.NFS_roads], output_roads)

        # integrate the roads dataset then convert to line so that each line ends at an intersection
        arcpy.management.Integrate(output_roads, cluster_tolerance="0.5 Feet")
        arcpy.management.FeatureToLine(output_roads, os.path.join(self.transport_dataset, "osm_nfs_combined"))
        self.combined_roads = os.path.join(self.transport_dataset, "osm_nfs_combined")

        if not keep_temp:
            arcpy.management.Delete(output_roads)
            arcpy.management.Delete(end_points)
            arcpy.management.Delete(points)
            arcpy.management.Delete("NFS_bounded")
            arcpy.management.Delete("road_points")
            arcpy.management.Delete("NFS_cleaned")

    def create_road_fc(self, keep_temp=False):
        """Cleans and merges the roads feature classes, then creates a network dataset out of the result"""
        # set workspace to transportation feature dataset
        arcpy.env.workspace = os.path.join(self.workspace, self.transport_dataset)

        # erase the osm-nfs combined roads from the larger roads data
        if arcpy.Exists("roads_erased"):
            arcpy.management.Delete("roads_erased")
        erasing_fc = os.path.basename(self.total_roads)
        arcpy.analysis.Erase(erasing_fc, os.path.basename(self.combined_roads), "roads_erased")

        # merge road feature classes
        final_roads = "merged_roads"
        if arcpy.Exists(final_roads):
            arcpy.management.Delete(final_roads)
        arcpy.management.Merge(["roads_erased", os.path.basename(self.combined_roads)], final_roads)
        complete_roads = "complete_roads"
        if arcpy.Exists(complete_roads):
            arcpy.management.Delete(complete_roads)
        arcpy.management.FeatureToLine(final_roads, complete_roads)
        arcpy.management.RepairGeometry(complete_roads)

        # add and calculate distance field
        arcpy.management.AddField(complete_roads, "distance", "DOUBLE")
        arcpy.management.CalculateGeometryAttributes(
            complete_roads, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
        )

        if not keep_temp:
            arcpy.management.Delete("merged_roads")
            arcpy.management.Delete("roads_erased")

    def process(
        self,
        create_gdb=True,
        create_boundaries=True,
        sawmill_data=True,
        harvest_site_data=True,
        merge_road_creation=True,
        create_nw_ds=True
    ):
        """Starts and runs the process of preparing data"""
        arcpy.AddMessage("Beginning Data Preparation")
        if create_gdb:
            arcpy.AddMessage("Importing Road Data and Creating File GDB")
            self.create_new_file_gdb()
        else:
            arcpy.AddMessage("Skipping Road Data import and File GDB creation")

        arcpy.env.workspace = self.workspace
        arcpy.env.overwriteOutput = True

        if create_boundaries:
            arcpy.AddMessage("Creating Boundary Feature Classes")
            self.create_boundary_fcs()
        else:
            arcpy.AddMessage("Skipping Boundary Feature Class creation")
        if sawmill_data:
            arcpy.AddMessage("Cleaning Sawmill Data")
            self.clean_sawmill_data()
        else:
            arcpy.AddMessage("Sawmill Data Cleaning Skipped")
        if harvest_site_data:
            arcpy.AddMessage("Cleaning Harvest Site Data")
            self.clean_harvest_site_data()
        else:
            arcpy.AddMessage("Harvest Site Data Cleaning Skipped")
        if merge_road_creation:
            arcpy.AddMessage("Starting Road Data Merging Process")
            self.prep_roads()
            arcpy.AddMessage("Merging Forest Service Roads with OSM Roads")
            self.merge_park_roads()
            arcpy.AddMessage("Combining All Road Feature Classes")
            self.create_road_fc()
        else:
            arcpy.AddMessage("Road Data Merging Process Skipped")
        if create_nw_ds:
            arcpy.AddMessage("Creating Network Dataset")
            arcpy.na.CreateNetworkDataset(
                os.path.join(self.workspace, self.transport_dataset),
                "streets_nd",
                "complete_roads",
                "NO_ELEVATION"
            )
        else:
            arcpy.AddMessage("Network Dataset Creation Skipped")

def main():
    """Main function to run data preparation script"""
    workspace = sys.argv[1]
    total_roads = sys.argv[2]
    nfs_roads = sys.argv[3]
    sawmills = sys.argv[4]
    harvest_sites = sys.argv[5]
    park_boundaries = sys.argv[6]
    physio_boundary = sys.argv[7]
    spat_ref = sys.argv[8]

    data_prepper = DataPrep(
        workspace=workspace,
        total_roads=total_roads,
        nfs_roads=nfs_roads,
        sawmills=sawmills,
        harvest_sites=harvest_sites,
        park_boundaries=park_boundaries,
        physio_boundary=physio_boundary,
        spat_ref=spat_ref,
    )

    data_prepper.process(
        create_gdb=True,
        create_boundaries=True,
        sawmill_data=True,
        harvest_site_data=True,
        merge_road_creation=True,
        create_nw_ds=True
    )
    print("Finished preparing data")

if __name__ == "__main__":
    main()
