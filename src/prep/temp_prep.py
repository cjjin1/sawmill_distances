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

    def create_new_file_gdb(self):
        """Uses the quick import tool from Data Interoperability to create a new File GDB with roads data"""
        if not arcpy.Exists(os.path.join(self.workspace, os.path.basename(self.total_roads))):
            arcpy.CheckOutExtension("DataInteroperability")
            arcpy.gp.QuickImport_interop(os.path.dirname(self.total_roads), self.workspace)
            arcpy.CheckInExtension("DataInteroperability")
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

    def prep_roads(self):
        """Projects roads data into new spatial reference, clips roads to create feature class for park roads"""
        # project input roads into the transportation dataset
        output_path = os.path.join(self.transport_dataset, os.path.basename(self.total_roads) + "_proj")
        if not arcpy.Exists(output_path):
            arcpy.management.Project(self.total_roads, output_path, self.spat_ref)
        self.total_roads = output_path

        #clip roads to create park roads
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

    def clean_harvest_site_data(self):
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

    def clean_sawmill_data(self):
        """Projects and clips sawmill data. Removes closed and announced sawmills."""
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

    def merge_park_roads(self):
        """Merge NFS roads and OSM roads to create park roads for any relevant park"""
        # Clip the NFS roads to the boundary
        arcpy.management.MakeFeatureLayer(self.NFS_roads, "NFS_roads")
        arcpy.management.SelectLayerByLocation("NFS_roads", "INTERSECT", self.park_boundaries)
        self.NFS_roads = "NFS_bounded"
        arcpy.management.Project("NFS_roads", self.NFS_roads, self.spat_ref)

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
        arcpy.management.AddField(self.park_roads, "DUPLICATE", "SHORT")
        sc = arcpy.da.SearchCursor(points, ["ORIG_FID", "IS_NEAR", "VERY_NEAR"])
        uc = arcpy.da.UpdateCursor(self.park_roads, ["OBJECTID", "DUPLICATE"])
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
            sc = arcpy.da.SearchCursor("end_points_neg", ["ORIG_FID"])
            for row in sc:
                if orig_fid_dict.get(row[0]):
                    orig_fid_dict[row[0]] += 1
                else:
                    orig_fid_dict[row[0]] = 1
            del row, sc

            sc = arcpy.da.SearchCursor("joined_lyr", ["ORIG_FID"])
            for row in sc:
                if orig_fid_dict.get(row[0]) and orig_fid_dict[row[0]] == 2:
                    orig_fid_dict[row[0]] -= 1
            del row, sc

            uc = arcpy.da.UpdateCursor(self.NFS_roads, ["OBJECTID"])
            for row in uc:
                if orig_fid_dict.get(row[0]) and orig_fid_dict[row[0]] == 2:
                    uc.deleteRow()
                    remove_count += 1
            del row, uc
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

    def create_road_fc(self):
        """Cleans and merges the roads feature classes, then creates a network dataset out of the result"""
        # set workspace to transportation feature dataset
        arcpy.env.workspace = self.transport_dataset

        # erase the osm-nfs combined roads from the larger roads data
        osm_nfs_roads = "osm_nfs_combined"
        erasing_fc = os.path.basename(self.total_roads)
        arcpy.analysis.Erase(erasing_fc, osm_nfs_roads, "roads_erased")

        # merge road feature classes
        final_roads = "merged_roads"
        arcpy.management.Merge(["roads_erased", osm_nfs_roads], final_roads)
        arcpy.management.FeatureToLine(final_roads, "complete_roads")
        final_roads = "complete_roads"
        arcpy.management.RepairGeometry(final_roads)

        # add and calculate distance field
        arcpy.management.AddField(final_roads, "distance", "DOUBLE")
        arcpy.management.CalculateGeometryAttributes(
            final_roads, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
        )

    def process(
        self,
        create_boundaries=True,
        create_new_gdb=True,
        road_prep=True,
        road_merge=True,
        sawmill_data=True,
        harvest_site_data=True,
        road_fc=True
    ):
        """Starts and runs the process of preparing data"""
        if create_new_gdb:
            self.create_new_file_gdb()

        arcpy.env.workspace = self.workspace
        arcpy.env.overwriteOutput = True

        if create_boundaries:
            self.create_boundary_fcs()
        if road_prep:
            self.prep_roads()
        if road_merge:
            self.merge_park_roads()
        if sawmill_data:
            self.clean_sawmill_data()
        if harvest_site_data:
            self.clean_harvest_site_data()
        if road_fc:
            self.create_road_fc()

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
        create_new_gdb=True,
        create_boundaries=False,
        road_prep=True,
        road_merge=False,
        sawmill_data=False,
        harvest_site_data=False,
        road_fc=False
    )
    print("Finished preparing data")

if __name__ == "__main__":
    main()
