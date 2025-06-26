Documentation:
Data required for scripts:
1. NFS roads dataset
2. Sawmill dataset
3. Harvest sites dataset
3. [Optional] Boundary dataset

Data prep:
- All input files are done as full path
1. roads_data_prep.py
  - Uses OSM data to retrieve road data for network analyst
  - Depending on size of location chosen, may take several minutes
  - Inputs:
      - output roads File GDB (must be created beforehand)
      - output nodes File GDB (must be created beforehand, currently not used in script)
      - aoi (string of place to gather data for, eg. "Mississippi, USA")
        - or -
      - North, South, East, West coordinates for a bounding box
      - [optional] select a single road type to export as a feature class
    - Example Input:
      - E:/timber_project/data/ms_roads.gdb 
      - E:/timber_project/data/ms_nodes.gdb
      - "Mississippi, USA"
      - Residential

2. data_prep.py
  - Prepares data with various operations:
      - projection
      - clipping
      - Creating intersection points
      - adding distance field to roads dataset
      - creating network dataset
  - Building the network dataset is done within ArcGIS Pro manually, not in the script
  - Inputs: 
      - Workspace (FileGDB to store data)
      - Feature Dataset (Feature Dataset within a File GDB, must be created beforehand)
      - Roads Dataset (path to roads dataset created in roads_data_prep.py)
      - NFS Roads Shapefile (dataset of NFS roads)
      - sawmill shapefile (dataset of sawmills)
      - harvest sites (dataset of harvest sites)
      - [optional] Boundary Shapefile (if any dataset extends past the desired area of interest)
  - Example Input:
      - E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb
      - E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb/Transportation
      - E:/timber_project/data/ms_roads.gdb/roads 
      - E:/timber_project/data/RoadCore_FS.shp
      - E:/timber_project/data/sawmill_geocoded.shp
      - E:/timber_project/data/TimberHarvestBienville.shp
      - E:/timber_project/data/GOVTUNIT_Mississippi_State_Shape/Shape/GU_StateOrTerritory.shp

3. slope_raster.py
  - Creates a slope raster for least cost distance from centroid to road
    - Takes in several polygon and polyline feature classes for roadless areas
    - Takes in DEM for slope
    - Creates slope raster then removes roadless areas from said raster
  - Inputs:
    - Workspace (to store files)
    - Stream feature dataset (to store projected and clipped streams)
    - Stream directory (directory that holds original streams data)
    - Roadless area (feature class of areas deemed roadless)
    - Roads dataset (dataset of roads)
    - DEM raster (original DEM of study area)
    - [optional] Boundary Shapefile (if any dataset extends past the desired area of interest)
  - Example Input:
    - E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb
    - E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb/streams
    - E:/timber_project/data/streams
    - E:/timber_project/data/roadless_areas
    - E:/timber_project/scratch/Bienville_OSM_test/BV_ND.gdb/Transportation/all_roads
    - E:/timber_project/data/USGS_13_n33w090_20221121.tif
    - E:/timber_project/data/BienvilleBoundary

To run distance calculations:
- Ensure network dataset is built
- Create a script and import the distance_calculator.py script
- Call on main distance calculation function with input files produced by data prep scripts
- The calculate_distance() function will calculate road distance and Euclidean distance from harvest site
  centroid to sawmill destination
- Needs 7 inputs:
  - harvest site (singular harvest site to act as starting point)
  - roads (roads dataset (featureclass/shapefile, not network dataset))
  - network dataset (network dataset of roads)
  - sawmills (can be a single sawmill or multiple sawmills)
    - if multiple sawmills, will find the nearest sawmill
  - slope raster
  - off-limit areas feature class
  - output path (user designated file path for output route feature class)
  - [optional] sawmill type (only works with multiple sawmill inputs)