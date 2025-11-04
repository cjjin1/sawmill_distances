#!/usr/bin/env python3
"""
Extract road data from OSM Planet files for very large areas using GDAL VectorTranslate
and bounding boxes.

Usage:
```
python osm_roads_planet.py

Arguments:
- planet_file: Path to the OSM planet file (.pbf)
- bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
- layer_name: Name for the output layer
- overwrite: Whether to overwrite existing files
- keep_intermediate: Whether to keep the intermediate GPKG

Example:
python osm_roads_planet.py
-planet_file "us-latest-osm.pbf"
-bbox [-95.55452488285067, 28.65376380642857, -74.51856375734542, 36.94887553746901]
-layer_name "s_sm_coastal_roads"
-overwrite False
-keep_intermediate False

Output:
- Intermediate GPKG file in "intermediate" directory.
- File Geodatabase in "final" directory.

Project: Timber Suitability
PI: Dr. Laura Tateosian
Author: Makiko Shukunobe
Date: 2025-09-18
"""

import os
import sys
import arcpy
from pathlib import Path
import time
from osgeo import gdal

gdal.UseExceptions()  # Suppress GDAL warnings
from utils import (
    time_operation,
    print_timing_summary,
    create_project_folders,
    setup_logging,
    get_logger,
    get_shapefile_bbox,
    get_shapefile_bbox_arcpy,
)


class OSMRoadsPlanet:
    def _build_where_clause(self):
        return (
            "highway IN ("
            "'motorway','trunk','primary','secondary','tertiary',"
            "'residential','unclassified','road','service')"
        )

    def _build_translate_options(self, where_clause):
        opts = {
            "format": "GPKG",
            "where": where_clause,
            "layers": ["lines"],
            "layerName": self.layer_name,
        }
        if self.overwrite:
            opts["accessMode"] = "overwrite"
        if self.bbox is not None:
            opts["spatFilter"] = [
                self.bbox[0],
                self.bbox[1],
                self.bbox[2],
                self.bbox[3],
            ]
        return opts

    def _open_osm_dataset(self):
        return gdal.OpenEx(
            str(self.planet_file),
            gdal.OF_VECTOR,
            allowed_drivers=["OSM"],
            open_options=["USE_CUSTOM_INDEXING=YES", "MAX_TMPFILE_SIZE=2048"],
        )

    def _progress_callback(self):
        try:
            from tqdm import tqdm  # type: ignore

            bar = tqdm(total=100, desc="GDAL VectorTranslate", unit="%", leave=False)

            def _cb(complete, message, user_data):
                try:
                    bar.n = int(complete * 100)
                    bar.refresh()
                except Exception:
                    pass
                return 1

            return _cb, bar
        except Exception:
            last_report = {"v": -1}

            def _log_cb(complete, message, user_data):
                pct = int(complete * 100)
                if pct // 5 > last_report["v"]:
                    last_report["v"] = pct // 5
                    self.logger.info(f"GDAL translate progress: {pct}%")
                return 1

            return _log_cb, None

    def _log_bbox_where(self, opts, where_clause):
        if "spatFilter" in opts:
            bbox_log = f"{opts['spatFilter']} (minX,minY,maxX,maxY)"
        else:
            bbox_log = "None (no spatial filter)"
        self.logger.info("Extracting roads with GDAL VectorTranslate...")
        self.logger.info(f"Bounding box: {bbox_log}")
        self.logger.info("Output format: GPKG")
        self.logger.info(f"Where clause: {where_clause}")

    def __init__(
        self,
        planet_file,
        bbox,
        state_fc,
        layer_name="roads",
        base_path=None,
        overwrite=False,
        keep_intermediate=False,
    ):
        """Initialize OSM Roads Planet processor

        Args:
            planet_file (str): Path to the OSM planet file (.pbf)
            bbox (list): Bounding box [min_lon, min_lat, max_lon, max_lat]
            layer_name (str): Name for the output layer
            overwrite (bool): Whether to overwrite existing files
        """
        self.planet_file = planet_file
        self.bbox = bbox
        self.states = state_fc
        self.layer_name = layer_name
        self.overwrite = overwrite
        self.keep_intermediate = keep_intermediate
        self.logger = get_logger()

        # Setup project folders and paths
        self.project_paths = create_project_folders(base_path)
        self.file_gdb = str(Path(self.project_paths["final"]) / "roads.gdb")
        self.downloads_dir = self.project_paths["downloads"]
        self.intermediate_dir = self.project_paths["intermediate"]

        # Intermediate files
        self.gpkg_output = os.path.join(
            self.intermediate_dir, f"{self.layer_name}.gpkg"
        )

        self.logger.info(f"OSMRoadsPlanet initialized for bbox: {bbox}")
        self.logger.info(f"Planet file: {planet_file}")
        self.logger.info(f"Layer name: {layer_name}")
        self.logger.info(f"Overwrite mode: {overwrite}")

        self.speed_limit_dict = {
            "West Virginia": {
                "motorway": 70,
                "trunk": 65,
                "primary": 55,
                "secondary": 55,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 25,
                "road": 5,
            },
            "Florida": {
                "motorway": 70,
                "trunk": 45,
                "primary": 45,
                "secondary": 45,
                "tertiary": 30,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Illinois": {
                "motorway": 70,
                "trunk": 45,
                "primary": 45,
                "secondary": 30,
                "tertiary": 30,
                "residential": 30,
                "unclassified": 30,
                "service": 10,
                "road": 5,
            },
            "Minnesota": {
                "motorway": 60,
                "trunk": 65,
                "primary": 55,
                "secondary": 30,
                "tertiary": 30,
                "residential": 20,
                "unclassified": 20,
                "service": 10,
                "road": 5,
            },
            "Maryland": {
                "motorway": 55,
                "trunk": 55,
                "primary": 30,
                "secondary": 30,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Rhode Island": {
                "motorway": 55,
                "trunk": 50,
                "primary": 25,
                "secondary": 25,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 15,
                "service": 15,
                "road": 5,
            },
            "Idaho": {
                "motorway": 80,
                "trunk": 65,
                "primary": 35,
                "secondary": 35,
                "tertiary": 25,
                "residential": 20,
                "unclassified": 25,
                "service": 10,
                "road": 5,
            },
            "New Hampshire": {
                "motorway": 65,
                "trunk": 40,
                "primary": 30,
                "secondary": 30,
                "tertiary": 30,
                "residential": 25,
                "unclassified": 30,
                "service": 15,
                "road": 5,
            },
            "North Carolina": {
                "motorway": 65,
                "trunk": 55,
                "primary": 45,
                "secondary": 45,
                "tertiary": 35,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 15,
            },
            "Vermont": {
                "motorway": 65,
                "trunk": 50,
                "primary": 50,
                "secondary": 25,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 25,
                "road": 5,
            },
            "Connecticut": {
                "motorway": 65,
                "trunk": 45,
                "primary": 35,
                "secondary": 35,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 20,
                "service": 15,
                "road": 5,
            },
            "Delaware": {
                "motorway": 65,
                "trunk": 55,
                "primary": 25,
                "secondary": 40,
                "tertiary": 50,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "New Mexico": {
                "motorway": 75,
                "trunk": 45,
                "primary": 35,
                "secondary": 35,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 5,
                "road": 5,
            },
            "California": {
                "motorway": 65,
                "trunk": 65,
                "primary": 35,
                "secondary": 35,
                "tertiary": 35,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 70,
            },
            "New Jersey": {
                "motorway": 65,
                "trunk": 50,
                "primary": 35,
                "secondary": 40,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Wisconsin": {
                "motorway": 70,
                "trunk": 55,
                "primary": 45,
                "secondary": 35,
                "tertiary": 30,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Oregon": {
                "motorway": 65,
                "trunk": 55,
                "primary": 35,
                "secondary": 35,
                "tertiary": 25,
                "residential": 20,
                "unclassified": 20,
                "service": 15,
                "road": 5,
            },
            "Nebraska": {
                "motorway": 75,
                "trunk": 65,
                "primary": 45,
                "secondary": 35,
                "tertiary": 50,
                "residential": 25,
                "unclassified": 50,
                "service": 25,
                "road": 5,
            },
            "Pennsylvania": {
                "motorway": 55,
                "trunk": 45,
                "primary": 35,
                "secondary": 35,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Washington": {
                "motorway": 60,
                "trunk": 60,
                "primary": 35,
                "secondary": 35,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 25,
            },
            "Louisiana": {
                "motorway": 70,
                "trunk": 50,
                "primary": 55,
                "secondary": 35,
                "tertiary": 35,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Georgia": {
                "motorway": 70,
                "trunk": 55,
                "primary": 45,
                "secondary": 45,
                "tertiary": 35,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Alabama": {
                "motorway": 70,
                "trunk": 55,
                "primary": 45,
                "secondary": 45,
                "tertiary": 45,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Utah": {
                "motorway": 70,
                "trunk": 65,
                "primary": 40,
                "secondary": 35,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Ohio": {
                "motorway": 65,
                "trunk": 55,
                "primary": 35,
                "secondary": 35,
                "tertiary": 35,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Texas": {
                "motorway": 65,
                "trunk": 75,
                "primary": 45,
                "secondary": 40,
                "tertiary": 30,
                "residential": 30,
                "unclassified": 30,
                "service": 10,
                "road": 5,
            },
            "Colorado": {
                "motorway": 75,
                "trunk": 55,
                "primary": 45,
                "secondary": 35,
                "tertiary": 30,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 20,
            },
            "South Carolina": {
                "motorway": 70,
                "trunk": 45,
                "primary": 45,
                "secondary": 45,
                "tertiary": 35,
                "residential": 25,
                "unclassified": 25,
                "service": 10,
                "road": 5,
            },
            "Oklahoma": {
                "motorway": 75,
                "trunk": 65,
                "primary": 65,
                "secondary": 40,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 45,
                "service": 45,
                "road": 45,
            },
            "Tennessee": {
                "motorway": 70,
                "trunk": 55,
                "primary": 45,
                "secondary": 40,
                "tertiary": 30,
                "residential": 25,
                "unclassified": 30,
                "service": 10,
                "road": 5,
            },
            "Wyoming": {
                "motorway": 75,
                "trunk": 70,
                "primary": 70,
                "secondary": 45,
                "tertiary": 30,
                "residential": 25,
                "unclassified": 45,
                "service": 45,
                "road": 5,
            },
            "Hawaii": {
                "motorway": 55,
                "trunk": 35,
                "primary": 35,
                "secondary": 25,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 5,
                "road": 5,
            },
            "North Dakota": {
                "motorway": 80,
                "trunk": 65,
                "primary": 65,
                "secondary": 65,
                "tertiary": 55,
                "residential": 25,
                "unclassified": 55,
                "service": 15,
                "road": 5,
            },
            "Kentucky": {
                "motorway": 70,
                "trunk": 55,
                "primary": 35,
                "secondary": 35,
                "tertiary": 35,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Michigan": {
                "motorway": 70,
                "trunk": 55,
                "primary": 45,
                "secondary": 45,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Arkansas": {
                "motorway": 75,
                "trunk": 65,
                "primary": 45,
                "secondary": 35,
                "tertiary": 30,
                "residential": 20,
                "unclassified": 20,
                "service": 10,
                "road": 5,
            },
            "Mississippi": {
                "motorway": 70,
                "trunk": 65,
                "primary": 45,
                "secondary": 55,
                "tertiary": 30,
                "residential": 20,
                "unclassified": 30,
                "service": 10,
                "road": 5,
            },
            "Missouri": {
                "motorway": 70,
                "trunk": 65,
                "primary": 40,
                "secondary": 35,
                "tertiary": 35,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Montana": {
                "motorway": 80,
                "trunk": 70,
                "primary": 70,
                "secondary": 45,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Kansas": {
                "motorway": 75,
                "trunk": 65,
                "primary": 65,
                "secondary": 40,
                "tertiary": 30,
                "residential": 25,
                "unclassified": 45,
                "service": 15,
                "road": 5,
            },
            "Indiana": {
                "motorway": 70,
                "trunk": 60,
                "primary": 35,
                "secondary": 35,
                "tertiary": 30,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "South Dakota": {
                "motorway": 80,
                "trunk": 65,
                "primary": 35,
                "secondary": 35,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Massachusetts": {
                "motorway": 65,
                "trunk": 40,
                "primary": 25,
                "secondary": 25,
                "tertiary": 30,
                "residential": 25,
                "unclassified": 25,
                "service": 25,
                "road": 5,
            },
            "Virginia": {
                "motorway": 55,
                "trunk": 45,
                "primary": 45,
                "secondary": 35,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 5,
                "road": 5,
            },
            "District of Columbia": {
                "motorway": 50,
                "trunk": 25,
                "primary": 25,
                "secondary": 25,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 10,
                "service": 15,
                "road": 5,
            },
            "Maine": {
                "motorway": 70,
                "trunk": 35,
                "primary": 25,
                "secondary": 35,
                "tertiary": 35,
                "residential": 25,
                "unclassified": 25,
                "service": 5,
                "road": 5,
            },
            "New York": {
                "motorway": 65,
                "trunk": 55,
                "primary": 30,
                "secondary": 25,
                "tertiary": 30,
                "residential": 30,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Nevada": {
                "motorway": 65,
                "trunk": 55,
                "primary": 45,
                "secondary": 35,
                "tertiary": 35,
                "residential": 25,
                "unclassified": 25,
                "service": 15,
                "road": 5,
            },
            "Alaska": {
                "motorway": 65,
                "trunk": 55,
                "primary": 45,
                "secondary": 45,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 5,
                "road": 5,
            },
            "Iowa": {
                "motorway": 65,
                "trunk": 65,
                "primary": 55,
                "secondary": 35,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 20,
                "road": 5,
            },
            "Arizona": {
                "motorway": 65,
                "trunk": 65,
                "primary": 45,
                "secondary": 45,
                "tertiary": 25,
                "residential": 25,
                "unclassified": 25,
                "service": 25,
                "road": 5,
            }
        }

    def extract_roads_with_gdal(self):
        """Extract roads using GDAL VectorTranslate directly"""
        if not os.path.exists(self.planet_file):
            self.logger.error(f"Planet file not found: {self.planet_file}")
            return False, None

        # Check if output file exists and handle accordingly
        if os.path.exists(self.gpkg_output) and not self.overwrite:
            self.logger.info(f"Output file already exists: {self.gpkg_output}")
            self.logger.info("Skipping extraction, using existing data...")
            return True, None

        where_clause = self._build_where_clause()

        # Check if planet file exists and get its size
        planet_size_mb = os.path.getsize(self.planet_file) / (1024 * 1024)
        self.logger.info(f"Planet file size: {planet_size_mb:.2f} MB")

        # Configure GDAL options for VectorTranslate
        options_kwargs = self._build_translate_options(where_clause)
        bbox_log = (
            f"{options_kwargs['spatFilter']} (order: minX, minY, maxX, maxY)"
            if "spatFilter" in options_kwargs
            else "None (no spatial filter)"
        )

        # Progress callback (tqdm if available, else log every ~5%)
        progress_callback, bar = self._progress_callback()

        options = gdal.VectorTranslateOptions(
            callback=progress_callback, **options_kwargs
        )

        self._log_bbox_where(options_kwargs, where_clause)

        with time_operation(
            "GDAL VectorTranslate Extraction",
            "GDAL extraction started",
            "GDAL extraction completed",
        ) as timer:
            try:
                # Use GDAL VectorTranslate to extract roads
                src_ds = self._open_osm_dataset()
                if src_ds is None:
                    raise RuntimeError("Failed to open source dataset with GDAL OpenEx")
                try:
                    gdal.VectorTranslate(self.gpkg_output, src_ds, options=options)
                finally:
                    src_ds = None
                    if bar is not None:
                        try:
                            bar.close()
                        except Exception:
                            pass

                # Get output file size
                if os.path.exists(self.gpkg_output):
                    output_size_mb = os.path.getsize(self.gpkg_output) / (1024 * 1024)
                    self.logger.info(f"Output file size: {output_size_mb:.2f} MB")
                    self.logger.info(f"Output file saved to: {self.gpkg_output}")
                    return True, timer
                else:
                    self.logger.warning("Output file not found after extraction")
                    return False, timer

            except Exception as e:
                self.logger.error(f"GDAL VectorTranslate failed: {e}")
                return False, timer

    def create_file_geodatabase(self):
        """Create File Geodatabase if it doesn't exist"""
        if not os.path.exists(self.file_gdb):
            self.logger.info(f"File Geodatabase not found: {self.file_gdb}")
            try:
                arcpy.management.CreateFileGDB(
                    os.path.dirname(self.file_gdb), os.path.basename(self.file_gdb)
                )
                self.logger.info(f"File Geodatabase created: {self.file_gdb}")
                return True
            except Exception as e:
                self.logger.error(f"Error creating File Geodatabase: {e}")
                return False
        else:
            self.logger.info(f"File Geodatabase already exists: {self.file_gdb}")
            return True

    def import_to_arcgis(self):
        """Import GPKG to ArcGIS File Geodatabase"""
        if not os.path.exists(self.gpkg_output):
            self.logger.error(f"GPKG file not found: {self.gpkg_output}")
            return False, None

        # Create File Geodatabase if it doesn't exist
        if not self.create_file_geodatabase():
            self.logger.error("Failed to create File Geodatabase, aborting import")
            return False, None

        self.logger.info(f"Importing to ArcGIS File Geodatabase...")

        with time_operation(
            "ArcGIS Import", "ArcGIS import started", "ArcGIS import completed"
        ) as timer:
            try:
                # Start an indeterminate progress indicator while CopyFeatures runs
                import threading

                stop_event = threading.Event()

                def _spinner():
                    try:
                        from tqdm import tqdm  # type: ignore

                        bar = tqdm(total=100, desc="ArcGIS Import", leave=False)
                        i = 0
                        while not stop_event.is_set():
                            i = (i + 5) % 100
                            bar.n = i
                            bar.refresh()
                            time.sleep(0.5)
                        bar.close()
                    except Exception:
                        # Fallback to periodic logging
                        ticks = 0
                        while not stop_event.is_set():
                            ticks += 1
                            if ticks % 6 == 0:
                                self.logger.info("ArcGIS import in progress...")
                            time.sleep(0.5)

                spinner_thread = threading.Thread(target=_spinner, daemon=True)
                spinner_thread.start()

                # Input GeoPackage layer and output FGDB feature class
                in_features = f"{self.gpkg_output}\\{self.layer_name}"
                temp_feature_class = f"{self.file_gdb}\\{self.layer_name}_temp"
                out_feature_class = f"{self.file_gdb}\\{self.layer_name}"

                # If output exists and overwrite is true, delete first to avoid schema conflicts
                if arcpy.Exists(out_feature_class) and self.overwrite:
                    self.logger.info(
                        f"Overwriting existing feature class: {out_feature_class}"
                    )
                    arcpy.management.Delete(out_feature_class)
                if arcpy.Exists(temp_feature_class):
                    arcpy.management.Delete(temp_feature_class)

                self.logger.info(f"Copying features from: {in_features}")
                self.logger.info(f"To feature class: {temp_feature_class}")
                arcpy.management.CopyFeatures(in_features, temp_feature_class)
                arcpy.management.RepairGeometry(temp_feature_class)

                self.logger.info(f"Spatially joining states to roads")
                arcpy.analysis.SpatialJoin(
                    target_features=temp_feature_class,
                    join_features=self.states,
                    out_feature_class=out_feature_class,
                    join_operation="JOIN_ONE_TO_ONE",
                    join_type="KEEP_ALL",
                    match_option="INTERSECT"
                )
                arcpy.management.Delete(temp_feature_class)

                self.extract_oneway()
                self.extract_max_speed()

                # Stop spinner
                stop_event.set()
                spinner_thread.join(timeout=2)

                self.logger.info(
                    f"Successfully imported to {self.file_gdb}\\{self.layer_name}"
                )
                return True, timer

            except Exception as e:
                try:
                    stop_event.set()
                    spinner_thread.join(timeout=2)
                except Exception:
                    pass
                self.logger.error(f"ArcGIS import failed: {e}")
                return False, timer

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        if os.path.exists(self.gpkg_output):
            import gc

            # Attempt to release common locks (ArcGIS, Python refs)
            try:
                try:
                    arcpy.ClearWorkspaceCache_management()
                except Exception:
                    pass
                gc.collect()
            except Exception:
                pass

            # Retry deletion with small backoff and rename fallback (Windows lock patterns)
            attempts = 5
            for i in range(attempts):
                try:
                    os.remove(self.gpkg_output)
                    self.logger.info(f"Cleaned up temporary file: {self.gpkg_output}")
                    return
                except Exception as e:
                    if i == attempts - 1:
                        # Final attempt: try rename then delete
                        try:
                            temp_renamed = self.gpkg_output + ".to_delete"
                            try:
                                if os.path.exists(temp_renamed):
                                    os.remove(temp_renamed)
                            except Exception:
                                pass
                            os.rename(self.gpkg_output, temp_renamed)
                            os.remove(temp_renamed)
                            self.logger.info(
                                f"Cleaned up temporary file after rename: {self.gpkg_output}"
                            )
                            return
                        except Exception as e2:
                            self.logger.warning(
                                f"Could not delete temporary file {self.gpkg_output}: {e2}"
                            )
                            self.logger.warning(
                                "File may be locked by another process (e.g., ArcGIS/Explorer). Close apps and try again."
                            )
                            return
                    time.sleep(0.5)

    def extract_oneway(self):
        """Extracts the oneway tag from OSM roads data and puts it into its own field"""
        out_feature_class = f"{self.file_gdb}\\{self.layer_name}"
        fields = arcpy.ListFields(out_feature_class)
        field_names = [f.name for f in fields]
        if "other_tags" not in field_names:
            raise arcpy.ExecuteError("Roads data does not contain necessary other_tags field.")
        arcpy.management.AddField(out_feature_class, "oneway", "SHORT")
        arcpy.management.AddField(out_feature_class, "reversed", "SHORT")

        with arcpy.da.UpdateCursor(out_feature_class, ["other_tags", "oneway", "reversed"]) as cursor:
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

    def extract_max_speed(self):
        """Extracts the max speed tag from OSM roads data and puts it into its own field. Will populate will default
           values if no max speed tag is provided."""
        overall_default_speeds = {
            "motorway": 70,
            "trunk": 65,
            "primary": 45,
            "secondary": 45,
            "tertiary": 35,
            "residential": 25,
            "unclassified": 25,
            "service": 25,
            "road": 25,
        }

        out_feature_class = f"{self.file_gdb}\\{self.layer_name}"
        fields = arcpy.ListFields(out_feature_class)
        field_names = [f.name for f in fields]
        if "other_tags" not in field_names:
            raise arcpy.ExecuteError("Roads data does not contain necessary other_tags field.")
        arcpy.management.AddField(out_feature_class, "maxspeed", "LONG")

        fields = ["other_tags", "highway", "maxspeed", "STATE_NAME"]
        with arcpy.da.UpdateCursor(out_feature_class, fields) as cursor:
            for row in cursor:
                if row[0] and "\"maxspeed\"" in row[0]:
                    tags_list = row[0].split(",")
                    for tag in tags_list:
                        if "\"maxspeed\"" in tag:
                            expression_list = tag.split("=>")
                            speed_value = expression_list[1]
                            speed_value = speed_value.strip("\"")
                            try:
                                speed_value = int(speed_value[:2].strip())
                            except ValueError:
                                continue
                            if speed_value % 5 == 0:
                                row[2] = speed_value
                            else:
                                road_type = row[1]
                                if row[3]:
                                    row[2] = self.speed_limit_dict[row[3]][road_type]
                                else:
                                    row[2] = overall_default_speeds[road_type]
                else:
                    road_type = row[1]
                    if row[3]:
                        row[2] = self.speed_limit_dict[row[3]][road_type]
                    else:
                        row[2] = overall_default_speeds[road_type]
                cursor.updateRow(row)

    def process(self):
        """Main processing method that orchestrates the entire workflow"""
        self.logger.info("=" * 50)
        self.logger.info(f"Starting OSM Roads Planet processing for {self.layer_name}")
        self.logger.info(f"Planet file: {self.planet_file}")
        self.logger.info(f"Bounding box: {self.bbox}")
        self.logger.info(f"Downloads directory: {self.downloads_dir}")
        self.logger.info(f"Intermediate directory: {self.intermediate_dir}")
        self.logger.info(f"Final output: {self.file_gdb}\\{self.layer_name}")
        self.logger.info("=" * 50)

        arcpy.env.overwriteOutput = True

        # Track all timers for summary
        timers = []

        # Main process with total timing
        with time_operation(
            "Total Process",
            "OSM Planet Processing Started",
            "PROCESS COMPLETED SUCCESSFULLY",
        ) as total_timer:
            timers.append(total_timer)

            # Step 1: Extract roads with GDAL
            extraction_success, extraction_timer = self.extract_roads_with_gdal()
            if extraction_timer:
                timers.append(extraction_timer)

            if not extraction_success:
                self.logger.error("Failed to extract roads from planet file")
                return False

            # Step 2: Import to ArcGIS and add oneway/reversed fields
            import_success, import_timer = self.import_to_arcgis()
            if import_timer:
                timers.append(import_timer)

            if not import_success:
                self.logger.error("Failed to import to ArcGIS")
                return False

            # Step 3: Cleanup temporary files (optional)
            if not self.keep_intermediate:
                self.cleanup_temp_files()
            else:
                self.logger.info(
                    "Keeping intermediate files as requested (keep_intermediate=True)"
                )

            # Print detailed timing summary
            print_timing_summary(
                timers, total_timer.get_duration(), "OSM Planet Processing"
            )
            self.logger.info(f"Final output: {self.file_gdb}\\{self.layer_name}")
            return True

def main():
    """Main function to run OSM Roads Planet processing"""
    osm_log = None
    if len(sys.argv) > 6:
        osm_log = sys.argv[6]
    # Setup logging
    log_file = setup_logging(osm_log)
    logger = get_logger()

    # Configuration
    planet_file = sys.argv[1]  # Update this path
    shapefile_path = sys.argv[2]
    state_fc = sys.argv[3]
    layer_name = sys.argv[4]
    base_path = sys.argv[5]
    overwrite = True
    keep_intermediate = False  # Set True to keep the intermediate GPKG
    buffer_degrees = None  # Buffer around shapefile extent

    # Get bounding box from shapefile
    logger.info(f"Getting bounding box from shapefile: {shapefile_path}")
    bbox = get_shapefile_bbox(shapefile_path, buffer_degrees)
    if bbox is not None:
        logger.info(f"Shapefile-derived bbox (minX, minY, maxX, maxY): {bbox}")
    else:
        # Fallback to ArcPy method
        logger.info("Trying ArcPy method for bounding box...")
        bbox = get_shapefile_bbox_arcpy(shapefile_path, buffer_degrees)
        if bbox is not None:
            logger.info(f"ArcPy-derived bbox (minX, minY, maxX, maxY): {bbox}")
        else:
            logger.error(
                "Failed to determine bounding box from shapefile. Aborting to avoid unbounded extraction."
            )
            return

    # Create OSM Roads Planet processor instance
    osm_roads = OSMRoadsPlanet(
        planet_file=planet_file,
        bbox=bbox,
        state_fc=state_fc,
        layer_name=layer_name,
        base_path=base_path,
        overwrite=overwrite,
        keep_intermediate=keep_intermediate
    )

    # Run the complete processing workflow
    success = osm_roads.process()

    if success:
        print(f"OSM Roads Planet processing completed successfully!")
        print(f"Log file: {log_file}")
    else:
        print(f"OSM Roads Planet processing failed. Check log file: {log_file}")


if __name__ == "__main__":
    main()
