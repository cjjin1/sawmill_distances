########################################################################################################################
# utils.py
# Author: Makiko Shukunabe
# Purpose: Utility functions and classes for OSM road data processing
########################################################################################################################

import time
import logging
from datetime import datetime
from pathlib import Path


class TimeCounter:
    """Time counter utility class for tracking operation durations"""

    def __init__(self, operation_name=""):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        self.duration = None

    def start(self, custom_message=""):
        """Start timing an operation"""
        self.start_time = time.time()
        start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = custom_message or f"{self.operation_name} started"
        logging.info(f"{message} at: {start_datetime}")
        return self

    def stop(self, custom_message=""):
        """Stop timing and calculate duration"""
        if self.start_time is None:
            logging.warning("Timer was not started")
            return self

        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

        message = custom_message or f"{self.operation_name} completed"
        logging.info(f"{message} in: {self.duration:.2f} seconds")
        return self

    def get_duration(self):
        """Get the duration in seconds"""
        if self.duration is None and self.start_time is not None:
            return time.time() - self.start_time
        return self.duration

    def get_duration_minutes(self):
        """Get the duration in minutes"""
        duration = self.get_duration()
        return duration / 60 if duration else 0

    def format_duration(self):
        """Format duration as human-readable string"""
        duration = self.get_duration()
        if duration is None:
            return "Not started"

        if duration < 60:
            return f"{duration:.2f} seconds"
        else:
            minutes = duration / 60
            return f"{minutes:.2f} minutes ({duration:.2f} seconds)"


def time_operation(operation_name, custom_start_msg="", custom_end_msg=""):
    """Context manager for timing operations"""

    class TimeContext:
        def __init__(self, name, start_msg, end_msg):
            self.timer = TimeCounter(name)
            self.start_msg = start_msg
            self.end_msg = end_msg

        def __enter__(self):
            self.timer.start(self.start_msg)
            return self.timer

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.timer.stop(self.end_msg)

    return TimeContext(operation_name, custom_start_msg, custom_end_msg)


def print_timing_summary(timers, total_time, process_name="Process"):
    """Print a summary of all timing information"""
    logging.info("=" * 60)
    logging.info(f"=== {process_name.upper()} TIMING SUMMARY ===")
    logging.info("=" * 60)

    for timer in timers:
        if timer.duration is not None:
            logging.info(f"{timer.operation_name:30} : {timer.format_duration()}")

    logging.info("-" * 60)
    logging.info(
        f"{'TOTAL TIME':30} : {total_time:.2f} seconds ({total_time / 60:.2f} minutes)"
    )
    logging.info("=" * 60)


def create_project_folders(base_path=None):
    """Create project folder structure in osm_roads directory

    Args:
        base_path (str, optional): Base path for the project.
                                 If None, uses the parent directory of this file.

    Returns:
        dict: Dictionary with folder names as keys and paths as values
    """
    if base_path is None:
        # Get the parent directory of this utils.py file (osm_roads folder)
        #TODO change this to be more dynamic
        base_path = Path(__file__).parent.parent.parent.parent

    # Define the folders to create
    folders = ["final", "intermediate", "downloads"]

    # Dictionary to store created folder paths
    folder_paths = {}

    logging.info("Creating project folder structure...")

    for folder in folders:
        folder_path = Path(base_path) / folder

        if not folder_path.exists():
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
                logging.info(f"✓ Created folder: {folder_path}")
                folder_paths[folder] = str(folder_path)
            except Exception as e:
                logging.error(f"✗ Error creating folder '{folder}': {e}")
                folder_paths[folder] = None
        else:
            logging.info(f"✓ Folder already exists: {folder_path}")
            folder_paths[folder] = str(folder_path)

    logging.info("Project folder structure ready!")
    return folder_paths


def get_project_paths(base_path=None):
    """Get the standard project folder paths

    Args:
        base_path (str, optional): Base path for the project.
                                 If None, uses the parent directory of this file.

    Returns:
        dict: Dictionary with folder names as keys and paths as values
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent

    return {
        "final": str(Path(base_path) / "final"),
        "intermediate": str(Path(base_path) / "intermediate"),
        "downloads": str(Path(base_path) / "downloads"),
        "base": str(Path(base_path)),
    }


def setup_logging(log_file_path=None, log_level=logging.INFO):
    """Setup logging configuration for the application

    Args:
        log_file_path (str, optional): Path to the log file.
                                     If None, creates a log file in the project directory.
        log_level: Logging level (default: logging.INFO)

    Returns:
        str: Path to the created log file
    """
    if log_file_path is None:
        # Create log file in the project directory
        project_paths = get_project_paths()
        log_file_path = str(Path(project_paths["base"]) / "osm_roads.log")

    # Create log directory if it doesn't exist
    log_dir = Path(log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, mode="w", encoding="utf-8"),
            logging.StreamHandler(),  # Also print to console
        ],
    )

    # Log the start of the session
    logging.info("=" * 60)
    logging.info("OSM ROADS PROCESSING SESSION STARTED")
    logging.info("=" * 60)
    logging.info(f"Log file: {log_file_path}")

    return log_file_path


def get_logger(name=None):
    """Get a logger instance

    Args:
        name (str, optional): Name of the logger. If None, returns root logger.

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


def get_shapefile_bbox(shapefile_path, buffer_degrees=0.01):
    """Get bounding box from a shapefile

    Args:
        shapefile_path (str): Path to the shapefile
        buffer_degrees (float or None): Buffer to add around the shapefile extent (in degrees). If None, no buffer.

    Returns:
        list: Bounding box [min_lon, min_lat, max_lon, max_lat] or None if error
    """
    try:
        import geopandas as gpd

        # Read the shapefile
        gdf = gpd.read_file(str(shapefile_path))

        # Get the bounds
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]

        # Apply buffer (treat None as 0.0)
        buffer_value = 0.0 if buffer_degrees is None else buffer_degrees
        min_lon = bounds[0] - buffer_value
        min_lat = bounds[1] - buffer_value
        max_lon = bounds[2] + buffer_value
        max_lat = bounds[3] + buffer_value

        bbox = [min_lon, min_lat, max_lon, max_lat]

        logging.info(f"Shapefile bounds: {bounds}")
        logging.info(f"Bounding box with buffer ({buffer_value}°): {bbox}")

        return bbox

    except ImportError:
        logging.error("geopandas not available. Please install: pip install geopandas")
        return None
    except Exception as e:
        logging.error(f"Error reading shapefile {shapefile_path}: {e}")
        return None


def get_shapefile_bbox_arcpy(shapefile_path, buffer_degrees=0.01):
    """Get bounding box from a shapefile using ArcPy (alternative method)

    Args:
        shapefile_path (str): Path to the shapefile
        buffer_degrees (float or None): Buffer to add around the shapefile extent (in degrees). If None, no buffer.

    Returns:
        list: Bounding box [min_lon, min_lat, max_lon, max_lat] or None if error
    """
    try:
        import arcpy

        # Get the extent
        desc = arcpy.Describe(str(shapefile_path))
        extent = desc.extent

        # Extract coordinates (treat None as 0.0)
        buffer_value = 0.0 if buffer_degrees is None else buffer_degrees
        min_lon = extent.XMin - buffer_value
        min_lat = extent.YMin - buffer_value
        max_lon = extent.XMax + buffer_value
        max_lat = extent.YMax + buffer_value

        bbox = [min_lon, min_lat, max_lon, max_lat]

        logging.info(
            f"Shapefile extent: XMin={extent.XMin}, YMin={extent.YMin}, XMax={extent.XMax}, YMax={extent.YMax}"
        )
        logging.info(f"Bounding box with buffer ({buffer_value}°): {bbox}")

        return bbox

    except Exception as e:
        logging.error(f"Error reading shapefile with ArcPy {shapefile_path}: {e}")
        return None
