########################################################################################################################
# cf_from_calc_data.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates circuity factor from existing data. Samples data using Neyman Allocation.
########################################################################################################################


import sys, csv, os, random, math, statistics
import distance_calculator as dc
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

class CfFromDataCalculator:

    def __init__(self, csv_dir, out_dir, min_sample_size=30, seed_val=None):
        """Sets up attributes"""
        self.csv_dir = csv_dir
        self.out_dir = out_dir
        self.min_sample_size = min_sample_size
        if seed_val:
            random.seed(seed_val)
        self.results_dict = {
            "Lumber/Solid Wood": [],
            "Pellet": [],
            "Chip": [],
            "Pulp/Paper": [],
            "Composite Panel/Engineered Wood Product": [],
            "Plywood/Veneer": []
        }
        self.samples_dict = {}
        self.cf_list = []

    def import_distance_results(self):
        """Read in the distance results from calculations of all sites"""
        for sm_type in self.results_dict:
            csv_out = os.path.join(self.csv_dir, f"{sm_type[:3]}_distance.csv")
            in_file = open(csv_out, "r+", newline="\n")
            in_reader = csv.reader(in_file)

            for line in in_reader:
                self.results_dict[sm_type].append((line[0], line[1], line[2], line[3]))

    def collect_samples(self):
        """Collect random samples. Determine sample sizes using Neyman Allocation based on the standard deviation
           of multipliers."""
        z = 1.96
        e = 0.1

        for sm_type in self.results_dict:
            multi_list = []
            samples = []
            rand_idx_list = random.sample(range(0, len(self.results_dict[sm_type])), len(self.results_dict[sm_type]))
            sample_size = self.min_sample_size
            count = 0
            collected_sample_size = False
            while count < sample_size and not collected_sample_size:
                count += 1
                if count == sample_size:
                    std_dev = np.std(multi_list)
                    n = (z ** 2 * float(std_dev) ** 2) / e ** 2
                    n = math.ceil(n)
                    if n > sample_size:
                        sample_size = n
                        collected_sample_size = True
                sample = self.results_dict[sm_type][rand_idx_list[count]]
                multi_list.append(float(sample[2]) / float(sample[3]))
                samples.append(sample)
            self.samples_dict[sm_type] = samples

    def export_sampling_results(self):
        """Write out the sampling results"""
        for sm_type in self.samples_dict:
            csv_out = os.path.join(self.out_dir, f"{sm_type[:3]}_distance.csv")
            output_file = open(csv_out, "w+", newline="\n")
            output_writer = csv.writer(output_file)
            for sample in self.samples_dict[sm_type]:
                output_writer.writerow(sample)

    def calculate_cf(self):
        """Calculates the circuity factor and outputs the results"""
        pdf = PdfPages(os.path.join(self.out_dir, "histograms.pdf"))
        for sm_type in self.samples_dict:
            b1, b2, b3 = dc.calculate_circuity_factor_from_csv(
                os.path.join(self.out_dir, f"{sm_type[:3]}_distance.csv"),
                f"{sm_type[:3]}_circuity_factor.txt",
                self.out_dir,
                sm_type,
                pdf
            )
            samples = self.samples_dict[sm_type]
            ed_list = [float(sample[2]) for sample in samples]
            rd_list = [float(sample[3]) for sample in samples]
            multiplier_list = [ed / rd for rd, ed in zip(rd_list, ed_list)]
            mean_multiplier = statistics.mean(multiplier_list)
            median_multiplier = statistics.median(multiplier_list)
            self.cf_list.append([sm_type, b1, b2, b3, mean_multiplier, median_multiplier])

        ed_list = []
        rd_list = []
        for sm_type in self.samples_dict:
            type_ed_list = [float(sample[2]) for sample in self.samples_dict[sm_type]]
            type_rd_list = [float(sample[3]) for sample in self.samples_dict[sm_type]]
            ed_list += type_ed_list
            rd_list += type_rd_list
        b1, b2, b3 = dc.calculate_circuity_factor_from_lists(
            ed_list, rd_list, os.path.join(self.out_dir, f"All_circuity_factor.txt"), "All Sawmills", pdf
        )
        multiplier_list = [ed / rd for rd, ed in zip(rd_list, ed_list)]
        mean_multiplier = statistics.mean(multiplier_list)
        median_multiplier = statistics.median(multiplier_list)
        self.cf_list.append(["All Sawmills", b1, b2, b3, mean_multiplier, median_multiplier])
        pdf.close()

    def process(self):
        """Runs the full process"""
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.import_distance_results()
        self.collect_samples()
        self.export_sampling_results()
        self.calculate_cf()

def main():
    csv_dir = sys.argv[1]
    out_dir = sys.argv[2]
    cf_calc = CfFromDataCalculator(csv_dir, out_dir)
    cf_calc.process()

if __name__ == "__main__":
    main()
