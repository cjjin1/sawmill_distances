########################################################################################################################
# circuity_factor.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Finds the road circuity factor from between road distance and straight-line distance from harvest sites to
#          sawmills. Outputs mean and median multipliers as well as circuity factor for each sawmill type.
########################################################################################################################

import sys, arcpy, csv, os, random, gc, math, statistics
import statsmodels.api as sm
import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

class RouteFinder:
    """"Calculates the route between two points and finds the distance"""

    def __init__(self, network_ds, start_point, end_point, output_path, travel_mode):
        self.network_ds = network_ds
        self.start_point = start_point
        self.end_point = end_point
        self.output_path = output_path
        self.travel_mode = travel_mode

    def calculate_route_distance(self):
        """Finds the route from the starting point to the end point then calculates travel distance"""
        self.calculate_road_distance_nd()
        road_dist = self.calculate_distance_for_fc()
        arcpy.analysis.Near(self.start_point, self.output_path, search_radius="3 Miles", distance_unit="Miles")
        sc = arcpy.da.SearchCursor(self.start_point, ["NEAR_DIST"])
        for row in sc:
            road_dist += row[0]
            break
        del sc, row
        return road_dist

    def calculate_road_distance_nd(self):
        """Finds the road distance from a starting point to an end point using network analyst"""
        arcpy.CheckOutExtension("Network")
        route_layer_name = "sawmill_route"
        result = arcpy.na.MakeRouteAnalysisLayer(
            self.network_ds,
            layer_name=route_layer_name,
            travel_mode=self.travel_mode
        )
        route_layer = result.getOutput(0)
        try:
            solver = arcpy.na.GetSolverProperties(route_layer)
            solver.restrictions = ["Oneway"]
        except arcpy.ExecuteError:
            print("No oneway restriction implemented, solution will not include oneway functionality")
        sub_layers = arcpy.na.GetNAClassNames(route_layer)
        stops_layer_name = sub_layers["Stops"]

        arcpy.na.AddLocations(
            in_network_analysis_layer=route_layer,
            sub_layer=stops_layer_name,
            in_table=self.start_point,
            append="CLEAR",
            search_tolerance="20000 Feet"
        )

        arcpy.na.AddLocations(
            in_network_analysis_layer=route_layer,
            sub_layer=stops_layer_name,
            in_table=self.end_point,
            append="APPEND",
            search_tolerance="20000 Feet"
        )
        try:
            arcpy.na.Solve(route_layer, ignore_invalids="SKIP")
            if int(arcpy.management.GetCount(sub_layers["Routes"])[0]) == 0:
                raise arcpy.ExecuteError("Solve resulted in a failure")
        except arcpy.ExecuteError as e:
            arcpy.management.Delete(route_layer_name)
            raise arcpy.ExecuteError(e)
        arcpy.management.CopyFeatures(sub_layers["Routes"], self.output_path)
        arcpy.management.Delete(route_layer_name)
        arcpy.management.Delete(route_layer)
        del result, route_layer
        arcpy.CheckInExtension("Network")

    def calculate_distance_for_fc(self):
        """Calculates distance for a given polyline feature class"""
        arcpy.management.AddField(self.output_path, "distance", "DOUBLE")
        arcpy.management.CalculateGeometryAttributes(
            self.output_path, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
        )
        distance = 0
        sc = arcpy.da.SearchCursor(self.output_path, ["distance"])
        for row in sc:
            try:
                distance += row[0]
            except TypeError:
                continue
        del row, sc
        return distance

class CircuityCalculator:
    """Reads in data and conducts circuity analysis, producing multiple statistics"""

    def __init__(self, output_name, sawmill_type, pdf_file, rd_csv=None, rd_list=None, ed_list=None):
        self.output_name = output_name
        self.sawmill_type = sawmill_type
        self.pdf_file = pdf_file
        self.rd_csv = rd_csv
        self.rd_list = rd_list
        self.ed_list = ed_list
        self.use_lists = True
        if rd_csv:
            self.use_lists = False
        if not rd_csv and not rd_list and not ed_list:
            raise arcpy.ExecuteError("Invalid input.")

    def calculate_circuity_factor_from_csv(self):
        """Reads in road distance csv created by the road distance calculation functions. Returns coefficient
           for each regression."""
        rd_list = []
        ed_list = []

        rd_in = open(self.rd_csv, "r", newline="\n")
        rd_reader = csv.reader(rd_in)
        for row in rd_reader:
            ed_list.append(float(row[2]))
            rd_list.append(float(row[3]))
        rd_in.close()

        road_distance = np.array(rd_list)
        euclidean_distance = np.array(ed_list)

        self.generate_histogram(road_distance, "Road Distance")
        self.generate_histogram(euclidean_distance, "Euclidean Distance")
        self.generate_overlaid_histogram(
            [road_distance, euclidean_distance],
            ["Road Distance", "Euclidean Distance"],
        )

        df = pd.DataFrame({
            'sl': euclidean_distance,
            'sl_sq': euclidean_distance ** 2,
            'rd': road_distance
        })

        X1 = sm.add_constant(df[['sl', 'sl_sq']])
        y = df['rd']

        model1 = sm.OLS(y, X1).fit()

        X2 = sm.add_constant(df[['sl']])
        model2 = sm.OLS(y, X2).fit()

        X3 = df[['sl']]
        model3 = sm.OLS(y, X3).fit()

        b1 = model1.params['sl']
        b2 = model2.params['sl']
        b3 = model3.params['sl']
        arcpy.AddMessage(f"Circuity Factor for {os.path.basename(self.output_name)}: {b3}")

        results_file = open(self.output_name, "w+")
        results_file.write(str(model1.summary()) + "\n")
        results_file.write(str(model2.summary()) + "\n")
        results_file.write(str(model3.summary()) + "\n")
        results_file.write(f"Circuity factor: {b3}")
        results_file.close()

        return b1, b2, b3

    def calculate_circuity_factor_from_lists(self):
        """Reads in road distance csv created by the road distance calculation functions. Returns coefficient
           for each regression."""
        road_distance = np.array(self.rd_list)
        euclidean_distance = np.array(self.ed_list)

        self.generate_histogram(road_distance, "Road Distance")
        self.generate_histogram(euclidean_distance, "Euclidean Distance")
        self.generate_overlaid_histogram(
            [road_distance, euclidean_distance],
            ["Road Distance", "Euclidean Distance"],
        )

        df = pd.DataFrame({
            'sl': euclidean_distance,
            'sl_sq': euclidean_distance ** 2,
            'rd': road_distance
        })

        X1 = sm.add_constant(df[['sl', 'sl_sq']])
        y = df['rd']

        model1 = sm.OLS(y, X1).fit()

        X2 = sm.add_constant(df[['sl']])
        model2 = sm.OLS(y, X2).fit()

        X3 = df[['sl']]
        model3 = sm.OLS(y, X3).fit()

        b1 = model1.params['sl']
        b2 = model2.params['sl']
        b3 = model3.params['sl']
        arcpy.AddMessage(f"Circuity Factor for {os.path.basename(self.output_name)}: {b3}")

        results_file = open(self.output_name, "w+")
        results_file.write(str(model1.summary()) + "\n")
        results_file.write(str(model2.summary()) + "\n")
        results_file.write(str(model3.summary()) + "\n")
        results_file.write(f"Circuity factor: {b3}")
        results_file.close()

        return b1, b2, b3

    def generate_histogram(self, arr, value_name):
        """Generates a histogram based off an array for a sawmill type. Outputs to a pdf file."""
        plt.hist(arr, bins=40, edgecolor="black", linewidth=1.2)
        plt.xlim(0, 120)
        plt.xlabel(value_name + " (Miles)")
        plt.ylabel("Frequency")
        plt.title(f"Histogram of {value_name} for {self.sawmill_type}")
        self.pdf_file.savefig()
        plt.close()

    def generate_overlaid_histogram(self, arr_list, value_list):
        """Generates an overlaid histogram based off two arrays of both road and euclidean distance for a sawmill type.
           Outputs to a pdf file."""
        plt.hist(arr_list, label=value_list, bins=40, edgecolor="black", linewidth=0.5, color=["blue", "red"])
        plt.xlim(0, 120)
        plt.xlabel("Distance (Miles)")
        plt.ylabel("Frequency")
        plt.legend()
        plt.title(f"Histogram of Road and Euclidean Distances for {self.sawmill_type}")
        self.pdf_file.savefig()
        plt.close()

    def process(self):
        if self.use_lists:
            b1, b2, b3 = self.calculate_circuity_factor_from_lists()
            return b1, b2, b3
        else:
            b1, b2, b3 = self.calculate_circuity_factor_from_csv()
            return b1, b2, b3

class CircuityFactorAnalyzer:
    """Runs the total circuity factor analysis. Collects data and calculates circuity results."""

    def __init__(
            self,
            sl_dist_csv,
            output_dir,
            network_dataset,
            sawmills,
            harvest_sites,
            pairs_per_type,
            cost,
            single_sawmill_type,
            keep_output_paths,
            calculate_road_distances,
            workspace
        ):
        self.sl_dist_csv = sl_dist_csv
        self.output_dir = output_dir
        self.network_dataset = network_dataset
        self.sawmills = sawmills
        self.harvest_sites = harvest_sites
        self.pairs_per_type = pairs_per_type
        self.calculate_all = False
        if self.pairs_per_type == "All":
            self.calculate_all = True
        else:
            try:
                self.pairs_per_type = int(pairs_per_type)
            except ValueError:
                raise arcpy.ExecuteError("Invalid pairs-per-type input.")
        self.cost = cost
        self.single_sawmill_type = single_sawmill_type
        # set string inputs to proper boolean values
        if keep_output_paths.lower() == "true":
            self.keep_output_paths = True
        else:
            self.keep_output_paths = False
        if calculate_road_distances.lower() == "true":
            self.calculate_road_distances = True
        else:
            self.calculate_road_distances = False
        self.workspace = workspace
        arcpy.env.workspace = self.workspace
        arcpy.env.overwriteOutput = True
        arcpy.env.addOutputsToMap = False

        # check if calculate_road_distances and output_dir are valid
        if not calculate_road_distances and output_dir == "#":
            raise arcpy.ExecuteError("An directory input is required if road distances are not to be calculated.")

        # check if the necessary fields are present to record districts
        self.record_district = True
        field_list = arcpy.ListFields(harvest_sites)
        field_name_list = [field.name for field in field_list]
        self.hs_districts_fields = ["ADMIN_DIST", "DISTRICTNA"]
        for hs_d_field in self.hs_districts_fields:
            if hs_d_field not in field_name_list:
                print("Not recording districts")
                self.record_district = False
                break

        # convert harvest sites to points if given as polygons
        desc = arcpy.Describe(harvest_sites)
        self.oid_field = desc.OIDFieldName
        if desc.shapeType == "Polygon":
            if arcpy.Exists(f"{harvest_sites}_points"):
                arcpy.management.Delete(f"{harvest_sites}_points")
            arcpy.management.FeatureToPoint(
                harvest_sites, f"{harvest_sites}_points", "INSIDE"
            )
            self.harvest_sites = f"{harvest_sites}_points"
        elif desc.shapeType != "Point":
            raise arcpy.ExecuteError("Invalid harvest site: site must be polygon or point")

        # Setup output directory
        if output_dir != "#":
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
        else:
            output_dir = workspace + "/../" + f"outputs/circuity_factor_{datetime.datetime.now().strftime('%m%d_%H%M')}"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            self.output_dir = os.path.abspath(output_dir)

        # dict to store straight line distance and ids
        self.dist_id_dict = {
            "Lumber/Solid Wood": {},
            "Pellet": {},
            "Chip": {},
            "Pulp/Paper": {},
            "Composite Panel/Engineered Wood Product": {},
            "Plywood/Veneer": {}
        }

        # dictionary to store multipliers
        self.multi_dict = {
            "Lumber/Solid Wood": [],
            "Pellet": [],
            "Chip": [],
            "Pulp/Paper": [],
            "Composite Panel/Engineered Wood Product": [],
            "Plywood/Veneer": []
        }

        # create a pdf for histograms
        self.pdf = PdfPages(os.path.join(output_dir, "histograms.pdf"))

    def read_sl_distance_csv(self):
        """Reads in from straight line distance csv file"""
        sl_in = open(self.sl_dist_csv, "r", newline="\n")
        sl_reader = csv.reader(sl_in)
        for row in sl_reader:
            self.dist_id_dict[row[0]][row[1]] = (row[2], row[3])
        sl_in.close()

        # remove all other sawmill types from dictionaries if desired
        if self.single_sawmill_type != "All":
            temp_dict = self.dist_id_dict[self.single_sawmill_type]
            self.dist_id_dict = {self.single_sawmill_type: temp_dict}
            self.multi_dict = {self.single_sawmill_type: []}

    def calculate_road_distances_with_sampling(self):
        """Calculates the road distances using sampling."""
        # Z-score and margin of error values
        z = 1.96
        E = 0.1

        arcpy.AddMessage("Starting Road Distance Calculations")
        for sm_type in self.dist_id_dict:
            arcpy.AddMessage(f"Starting Calculations for {sm_type}")
            # output file for distance results so the full script doesn't have to run every time
            csv_out = os.path.join(self.output_dir, f"{sm_type[:3]}_distance.csv")
            output_file = open(csv_out, "w+", newline="\n")
            output_writer = csv.writer(output_file)

            oid_list = list(self.dist_id_dict[sm_type].keys())
            rand_id_list = random.sample(oid_list, len(oid_list))
            sample_size = self.pairs_per_type
            count = 0
            for i, rand_id in enumerate(rand_id_list):
                if count == self.pairs_per_type:
                    # calculate new sample size based on first pairs_per_type number of samples
                    # if less than originally set sample size
                    std_dev = np.std(self.multi_dict[sm_type])
                    n = (z ** 2 * float(std_dev) ** 2) / E ** 2
                    n = math.ceil(n)
                    if n > sample_size:
                        sample_size = n
                        arcpy.AddMessage(f"Calculated sample size for {sm_type} is greater than {self.pairs_per_type}.")
                        arcpy.AddMessage(f"New sample size for {sm_type} is {n}.")
                if count == sample_size:
                    break
                try:
                    # calculate route distance between harvest site and sawmill
                    # store results in dictionary and CSV file
                    # time.sleep(0.5)
                    gc.collect()
                    arcpy.management.MakeFeatureLayer(self.harvest_sites, f"harvest_site_{rand_id}")
                    arcpy.management.MakeFeatureLayer(self.sawmills, f"sawmill_layer_{rand_id}")
                    arcpy.management.SelectLayerByAttribute(
                        f"harvest_site_{rand_id}",
                        "NEW_SELECTION",
                        f"{self.oid_field} = {rand_id}"
                    )
                    arcpy.management.SelectLayerByAttribute(
                        f"sawmill_layer_{rand_id}",
                        "NEW_SELECTION",
                        f"OBJECTID = {self.dist_id_dict[sm_type][rand_id][0]}"
                    )
                    out_path = os.path.join(arcpy.env.workspace, f"path_{sm_type[:3]}_{rand_id}")
                    route_calc = RouteFinder(
                        f"harvest_site_{rand_id}",
                        self.network_dataset,
                        f"sawmill_layer_{rand_id}",
                        out_path,
                        self.cost)
                    road_dist = route_calc.calculate_route_distance()

                    rang_district = ""
                    if self.record_district:
                        with arcpy.da.SearchCursor(f"harvest_site_{rand_id}", self.hs_districts_fields) as sc:
                            for row in sc:
                                if row[0].strip():
                                    rang_district = row[0]
                                elif row[1]:
                                    rang_district = row[1]
                                break
                    # time.sleep(0.5)
                    gc.collect()
                    if not self.keep_output_paths:
                        arcpy.management.Delete(out_path)
                    if road_dist == 0:
                        raise arcpy.ExecuteError("Solve resulted in failure")
                    if road_dist > 120:
                        raise arcpy.ExecuteError("Route is longer than 120 miles")
                    if self.record_district:
                        output_writer.writerow(
                            [rand_id,
                             self.dist_id_dict[sm_type][rand_id][0],
                             self.dist_id_dict[sm_type][rand_id][1],
                             road_dist,
                             rang_district]
                        )
                    else:
                        output_writer.writerow(
                            [rand_id,
                             self.dist_id_dict[sm_type][rand_id][0],
                             self.dist_id_dict[sm_type][rand_id][1],
                             road_dist]
                        )
                    multiplier = road_dist / float(self.dist_id_dict[sm_type][rand_id][1])
                    self.multi_dict[sm_type].append(multiplier)
                except arcpy.ExecuteError as e:
                    arcpy.AddWarning(f"{sm_type}:{rand_id},{self.dist_id_dict[sm_type][rand_id][0]} failed: {str(e)}")
                    if i < len(rand_id_list) - 1:
                        attempt_id = self.dist_id_dict[sm_type][rand_id_list[i + 1]][0]
                        arcpy.AddMessage(
                            f"Attempting new ID: {rand_id_list[i + 1]}, {attempt_id}"
                        )
                        continue
                    else:
                        arcpy.AddWarning("No more IDs to try, skipping this distance calculation")
                        break
                finally:
                    # delete temporary layers, feature classes, and solvers
                    arcpy.management.Delete(f"harvest_site_{rand_id}")
                    arcpy.management.Delete(f"sawmill_layer_{rand_id}")
                    for name in arcpy.ListDatasets("*Solver*"):
                        arcpy.management.Delete(name)
                    # time.sleep(0.5)
                    gc.collect()
                    arcpy.management.ClearWorkspaceCache()
                count += 1
                if count % 5 == 0:
                    arcpy.AddMessage(f"{count} calculations done for {sm_type}.")
            arcpy.AddMessage(f"{sm_type} calculations have been completed. Sample size has been set to {sample_size}.")
            output_file.close()

    def calculate_road_distances_all_sites(self):
        """Calculates the road distances for every harvest site"""
        arcpy.AddMessage("Starting Road Distance Calculations")
        for sm_type in self.dist_id_dict:
            arcpy.AddMessage(f"Starting Calculations for {sm_type}")
            # output file for distance results so the full script doesn't have to run every time
            csv_out = os.path.join(self.output_dir, f"{sm_type[:3]}_distance.csv")
            output_file = open(csv_out, "w+", newline="\n")
            output_writer = csv.writer(output_file)

            oid_list = list(self.dist_id_dict[sm_type].keys())
            count = 0
            for i, oid in enumerate(oid_list):
                try:
                    # calculate route distance between harvest site and sawmill
                    # store results in dictionary and CSV file
                    # time.sleep(0.5)
                    gc.collect()
                    arcpy.management.MakeFeatureLayer(self.harvest_sites, f"harvest_site_{oid}")
                    arcpy.management.MakeFeatureLayer(self.sawmills, f"sawmill_layer_{oid}")
                    arcpy.management.SelectLayerByAttribute(
                        f"harvest_site_{oid}",
                        "NEW_SELECTION",
                        f"{self.oid_field} = {oid}"
                    )
                    arcpy.management.SelectLayerByAttribute(
                        f"sawmill_layer_{oid}",
                        "NEW_SELECTION",
                        f"OBJECTID = {self.dist_id_dict[sm_type][oid][0]}"
                    )
                    out_path = os.path.join(arcpy.env.workspace, f"path_{sm_type[:3]}_{oid}")
                    route_calc = RouteFinder(
                        f"harvest_site_{oid}",
                        self.network_dataset,
                        f"sawmill_layer_{oid}",
                        out_path,
                        self.cost)
                    road_dist = route_calc.calculate_route_distance()

                    rang_district = ""
                    if self.record_district:
                        with arcpy.da.SearchCursor(f"harvest_site_{oid}", self.hs_districts_fields) as sc:
                            for row in sc:
                                if row[0].strip():
                                    rang_district = row[0]
                                elif row[1]:
                                    rang_district = row[1]
                                break
                    # time.sleep(0.5)
                    gc.collect()
                    if not self.keep_output_paths:
                        arcpy.management.Delete(out_path)
                    if road_dist == 0:
                        raise arcpy.ExecuteError("Solve resulted in failure")
                    if road_dist > 120:
                        raise arcpy.ExecuteError("Route is longer than 120 miles")
                    if self.record_district:
                        output_writer.writerow(
                            [oid,
                             self.dist_id_dict[sm_type][oid][0],
                             self.dist_id_dict[sm_type][oid][1],
                             road_dist,
                             rang_district]
                        )
                    else:
                        output_writer.writerow(
                            [oid,
                             self.dist_id_dict[sm_type][oid][0],
                             self.dist_id_dict[sm_type][oid][1],
                             road_dist]
                        )
                    multiplier = road_dist / float(self.dist_id_dict[sm_type][oid][1])
                    self.multi_dict[sm_type].append(multiplier)
                except arcpy.ExecuteError as e:
                    arcpy.AddWarning(f"{sm_type}:{oid},{self.dist_id_dict[sm_type][oid][0]} failed: {str(e)}")
                    if i < len(oid_list) - 1:
                        arcpy.AddMessage(
                            f"Attempting new ID: {oid_list[i + 1]}, {self.dist_id_dict[sm_type][oid_list[i + 1]][0]}"
                        )
                        continue
                    else:
                        arcpy.AddWarning("No more IDs to try, skipping this distance calculation")
                        break
                finally:
                    # delete temporary layers, feature classes, and solvers
                    arcpy.management.Delete(f"harvest_site_{oid}")
                    arcpy.management.Delete(f"sawmill_layer_{oid}")
                    for name in arcpy.ListDatasets("*Solver*"):
                        arcpy.management.Delete(name)
                    # time.sleep(0.5)
                    gc.collect()
                    arcpy.management.ClearWorkspaceCache()
                count += 1
                if count % 5 == 0:
                    arcpy.AddMessage(f"{count} calculations done for {sm_type}.")
            arcpy.AddMessage(f"{sm_type} calculations have been completed. Sample size has been set to {count}.")
            output_file.close()

    def calculate_circuity_factor(self):
        """Calculates circuity factor from straight line and road distances"""
        rd_list = []
        ed_list = []

        # list for storing circuity factor results
        cf_list = []

        # find circuity factor for individual sawmill types
        for sm_type in self.dist_id_dict:
            multiplier_list = []
            csv_in = os.path.join(self.output_dir, f"{sm_type[:3]}_distance.csv")
            input_file = open(csv_in, "r", newline="\n")
            in_reader = csv.reader(input_file)
            for row in in_reader:
                rd_list.append(float(row[3]))
                ed_list.append(float(row[2]))
                multiplier_list.append(float(row[3]) / float(row[2]))
            input_file.close()
            circuity_results = CircuityCalculator(
                os.path.join(self.output_dir, f"{sm_type[:3]}_circuity_factor.txt"), sm_type, self.pdf, rd_csv=csv_in
            )
            b1, b2, b3 = circuity_results.process()
            mean_multiplier = statistics.mean(multiplier_list)
            median_multiplier = statistics.median(multiplier_list)
            cf_list.append([sm_type, b1, b2, b3, mean_multiplier, median_multiplier])

        # find circuity factor for all sawmill types combined
        if self.single_sawmill_type == "All":
            total_circuity_results = CircuityCalculator(
                os.path.join(self.output_dir, f"All_circuity_factor.txt"),
                "All Sawmills",
                self.pdf,
                rd_list=rd_list,
                ed_list=ed_list
            )
            b1, b2, b3 = total_circuity_results.process()

            multiplier_list = [rd / ed for rd, ed in zip(rd_list, ed_list)]
            cf_list.append(["All", b1, b2, b3, statistics.mean(multiplier_list), statistics.median(multiplier_list)])

            output_csv = open(os.path.join(self.output_dir, "total_results.csv"), "w", newline="\n")
            output_writer = csv.writer(output_csv)
            output_writer.writerow(["Sawmill Type", "OLS regression with sl, sl_sq, and intercept",
                                    "OLS regression with sl and intercept", "OLS regression with sl", "Mean Multiplier",
                                    "Median Multiplier"])
            for row in cf_list:
                output_writer.writerow(row)
            output_csv.close()

    def process(self):
        self.read_sl_distance_csv()
        if self.calculate_all:
            self.calculate_road_distances_all_sites()
        else:
            self.calculate_road_distances_with_sampling()
        self.calculate_circuity_factor()
        self.pdf.close()

def main():
    sl_dist_csv = sys.argv[1]
    output_dir = sys.argv[2]
    network_dataset = sys.argv[3]
    sawmills = sys.argv[4]
    harvest_sites = sys.argv[5]
    pairs_per_type = int(sys.argv[6])
    cost = sys.argv[7]
    single_sawmill_type = sys.argv[8]
    keep_output_paths = sys.argv[9]
    calculate_road_distances = sys.argv[10]

    # get workspace
    try:
        proj = arcpy.mp.ArcGISProject("CURRENT")
        workspace = proj.defaultGeodatabase
    except OSError:
        workspace = sys.argv[11]

    cf_analysis = CircuityFactorAnalyzer(
        sl_dist_csv,
        output_dir,
        network_dataset,
        sawmills,
        harvest_sites,
        pairs_per_type,
        cost,
        single_sawmill_type,
        keep_output_paths,
        calculate_road_distances,
        workspace
    )
    cf_analysis.process()

if __name__ == "__main__":
    main()