########################################################################################################################
# district_cf.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Finds circuity factors for ranger districts
########################################################################################################################

import csv, os, sys, arcpy
import pandas as pd
import numpy as np
import statsmodels.api as sm

class DistrictCF:

    def __init__(self, csv_dir, write_out=False):
        self.csv_dir = csv_dir
        self.write_out = write_out
        #sm_type: {district: [(hs_oid, sm_oid, ed, rd), (hs_oid, sm_oid, ed, rd), ...]}
        self.district_dict = {
            "Lumber/Solid Wood": {},
            "Pellet": {},
            "Chip": {},
            "Pulp/Paper": {},
            "Composite Panel/Engineered Wood Product": {},
            "Plywood/Veneer": {}
        }
        # sm_type: {district: (cf, sample size)}
        self.district_results_dict = {
            "Lumber/Solid Wood": {},
            "Pellet": {},
            "Chip": {},
            "Pulp/Paper": {},
            "Composite Panel/Engineered Wood Product": {},
            "Plywood/Veneer": {}
        }

    def compile_data(self):
        """Reads in the data from the csv outputs from circuity_factor.py/cf_all_sites.py"""
        for sm_type in self.district_dict:
            csv_in = os.path.join(self.csv_dir, f"{sm_type[:3]}_distance.csv")
            input_file = open(csv_in, "r", newline="\n")
            in_reader = csv.reader(input_file)
            for line in in_reader:
                if self.district_dict[sm_type].get(line[4]):
                    self.district_dict[sm_type][line[4]].append((line[0], line[1], line[2], line[3]))
                else:
                    self.district_dict[sm_type][line[4]] = [(line[0], line[1], line[2], line[3])]
            input_file.close()

    def build_results_dict(self):
        """Calculates the circuity factor from results for each ranger district"""
        for sm_type in self.district_dict:
            for district in self.district_dict[sm_type]:
                ed_list = []
                rd_list = []
                for site in self.district_dict[sm_type][district]:
                    ed_list.append(float(site[2]))
                    rd_list.append(float(site[3]))
                road_distance = np.array(rd_list)
                euclidean_distance = np.array(ed_list)

                df = pd.DataFrame({
                    'sl': euclidean_distance,
                    'rd': road_distance
                })
                model = sm.OLS(df['rd'], df[['sl']]).fit()
                result = model.params['sl']

                self.district_results_dict[sm_type][district] = (result, len(ed_list))

    def write_csv_output(self):
        """Writes out the circuity factor results into csv files"""
        for sm_type in self.district_results_dict:
            csv_out = os.path.join(self.csv_dir, f"{sm_type[:3]}_cf_by_district.csv")
            output_file = open(csv_out, "w", newline="\n")
            out_writer = csv.writer(output_file)
            for district in self.district_results_dict[sm_type]:
                out_writer.writerow(
                    [district,
                     self.district_results_dict[sm_type][district][0],
                     self.district_results_dict[sm_type][district][1]
                    ])
            output_file.close()

    def write_total_cf_output(self):
        """Writes out the total circuity factor results for each ranger district into csv file"""
        #district: [(ed_list, rd_list), (ed_list, rd_list), ...]
        by_districts = {}
        for sm_type in self.district_dict:
            for district in self.district_dict[sm_type]:
                compiled_list = self.district_dict[sm_type][district]
                ed_list = [float(entry[2]) for entry in compiled_list]
                rd_list = [float(entry[3]) for entry in compiled_list]
                if not by_districts.get(district):
                    by_districts[district] = []
                by_districts[district].append((ed_list, rd_list))

        csv_out = os.path.join(self.csv_dir, f"total_cf_by_district.csv")
        output_file = open(csv_out, "w", newline="\n")
        out_writer = csv.writer(output_file)
        for district in by_districts:
            ed_rd_lists = by_districts[district]

            ed_list = []
            rd_list = []

            for pair in ed_rd_lists:
                ed_list += pair[0]
                rd_list += pair[1]

            road_distance = np.array(rd_list)
            euclidean_distance = np.array(ed_list)

            df = pd.DataFrame({
                'sl': euclidean_distance,
                'rd': road_distance
            })
            model = sm.OLS(df['rd'], df[['sl']]).fit()
            result = model.params['sl']
            out_writer.writerow([district, result, len(ed_list)])

    def process(self):
        self.compile_data()
        self.build_results_dict()
        if self.write_out:
            self.write_csv_output()
            self.write_total_cf_output()

def main():
    try:
        dg = DistrictCF(sys.argv[1], True)
        dg.process()
    except IndexError:
        print("Provide a directory to retrieve all necessary data and ranger district feature class.")
        exit(1)

if __name__ == "__main__":
    main()