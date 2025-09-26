########################################################################################################################
# extract_oneway.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Extracts the oneway tag from OSM roads data if needed.
# Usage: <Roads data>
########################################################################################################################

import arcpy,sys

def extract_oneway(roads_data):
    fields = arcpy.ListFields(roads_data)
    field_names = [f.name for f in fields]
    if "other_tags" not in field_names:
        raise arcpy.ExecuteError("Roads data does not contain necessary other_tags field.")
    arcpy.management.AddField(roads_data, "oneway", "SHORT")
    arcpy.management.AddField(roads_data, "reversed", "SHORT")

    with arcpy.da.UpdateCursor(roads_data, ["other_tags", "oneway", "reversed"]) as cursor:
        for row in cursor:
            if row[0] and "\"oneway\"" in row[0]:
                tags_list = row[0].split(",")
                for tag in tags_list:
                    if "\"oneway\"" in tag:
                        expression_list = tag.split("=>")
                        oneway_value = expression_list[1]
                        if oneway_value == "\"yes\"":
                            row[1] = 1
                            row[2] = 0
                        elif oneway_value == "\"-1\"":
                            row[1] = 1
                            row[2] = 1
                        else:
                            row[1] = 0
                            row[2] = 0
            else:
                row[1] = 0
                row[2] = 0
            cursor.updateRow(row)

roads = sys.argv[1]
arcpy.env.overwriteOutput = True

extract_oneway(roads)