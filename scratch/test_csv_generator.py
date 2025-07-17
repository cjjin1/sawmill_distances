import csv, random

csv_file = open("C:/timber_project/data/testing_app_all.csv", "w", newline = "\n")
mill_type_list = ["chip","lumber", "OSB","panel","pellet","plywood/veneer","pulp/paper"]
writer = csv.writer(csv_file)
sample_size = len(mill_type_list) * 20

random.seed(50)
random_numbers = random.sample(range(1, 1608), sample_size)

count = 0
mill_idx = 0
for num in random_numbers:
    writer.writerow([num, mill_type_list[mill_idx]])
    count += 1
    if count % (sample_size / len(mill_type_list)) == 0:
        mill_idx += 1

csv_file.close()