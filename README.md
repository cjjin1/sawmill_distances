Documentation:
For the data prepration scripts, use in the order shown below.

Data prep:
- All input files are done as full path
1. osm_roads.py
  - IMPORTANT: This script needs to be run twice if the study area is very large:
    - Once for the entire study area: this includes paths to every desirable sawmill
    - Second time is for a smaller study area, which encapsulates where the NFS roads will
      need to be connected to OSM roads. roads_data_prep.py will not run properly if the roads data set is too large
  - Uses OSM data to retrieve road data
  - Depending on size of location chosen, may take several minutes
  - Inputs:
      - output roads File GDB (must be created beforehand)
      - Area of Interest:
        - two options for inputs: name of place or shapefile
      - for third argument, use either the keyword "aoi" or "shapefile" to signify which method to use
      - Output name
    - Example Input:
      - C:/timber_project/data/nc_va_roads.gdb 
      - C:/timber_project/data/boundaries/nc_va_boundaries
      - shapefile
      - osm_roads

2. road_data_prep.py
  - Handles combining NFS roads and OSM roads
  - Inputs: 
      - Workspace (FileGDB to store data)
      - Feature Dataset (Feature Dataset within the File GDB, must be created beforehand)
      - Roads feature class (path to smaller roads dataset created in osm_roads.py)
      - NFS Roads feature class (dataset of NFS roads)
      - Boundary feature class (to clip the NFS roads fc)
      - Spatial reference (Input needs to be the WKID/SRID code)
      - output name (for the output roads data)
  - Example Input:
      - C:/timber_project/scratch/App_test/app_nd.gdb
      - C:/timber_project/scratch/App_test/app_nd.gdb/Transportation
      - C:/timber_project/data/nc_va_roads.gdb/osm_roads 
      - C:/timber_project/data/RoadCore_FS.shp
      - C:/timber_project/data/boundaries/nc_va_boundaries.shp
      - 3404
      - nc_va_osm_NFS_roads

3. data_prep
  - Handles projecting and cleaning harvest site and sawmill data
  - Merges the combined NFS/OSM roads with the larger OSM road feature class
  - Inputs:
    - Workspace (FileGDB to store data)
    - Feature Dataset (same feature dataset the combined NFS/OSM road feature class is in)
    - roads (the larger roads feature class created by osm_roads.py)
    - harvest sites
    - sawmills
    - harvest site boundary (to clip harvest sites)
    - sawmill boundary (to clip sawmill data)
    - Spatial Reference (Input needs to be the WKID/SRID code)
  - Example Input:
    - C:/timber_project/scratch/App_test/app_nd.gdb
    - C:/timber_project/scratch/App_test/app_nd.gdb/Transportation
    - C:/timber_project/data/app_roads.gdb/osm_roads
    - C:/timber_project/data/Activity_TimberHarvest.shp
    - C:/timber_project/data/sawmills.shp
    - C:/timber_project/data/boundaries/app_boundaries.shp
    - C:/timber_project/data/boundaries/app_study_area.shp
    - 3404

BEFORE CALCULATIONS:
1. First, the Create Network dataset tool must be run. Inputs include:
  - Feature dataset (containing the complete merged roads (complete_roads) feature class)
  - Dataset name (call it streets_nd)
  - Source feature class (select the merged_roads feature class created in data_prep.py)
  - Select no elevation model
2. Oneway functionality must be manually implemented in ArcGIS Pro. To do so, follow these steps:
  - Open the streets_nd network dataset properties in the catalog
  - Create a new travel mode called "Driving Distance"
    - Under costs, ensure length is used for impedance
  - Under the costs tab at the top, ensure the distance field is used for the evaluators
  - Under the restrictions tab, create a new restriction called "Oneway"
    - usage Type: prohibited (-1)
    - under evaluators, for the Along source, set the type to field script and use this value and code block
      - Value=evaluator(!oneway!, !reversed!)
      - Code Block:
        def evaluator(oneway, reversed):
          return oneway == 1 and reversed == 1
    - under evaluators, for the Against source, set the type to field script and use this value and code block
      - Value=evaluator(!oneway!, !reversed!)
      - Code Block:
        def evaluator(oneway, reversed):
          return oneway == 1 and reversed == 0
  - Go back to the travel mode tab and for driving distance, make sure the Oneway restriction is checked
3. Build the network using the Build Network tool

Circuity Factor calculation:
circuity_factor.py
  - Calculates straight line distance for every harvest site to the nearest sawmill of each type
  - Randomly selects a number (specified by user) of site-to-sawmill pairs for each type and calculates road distance
  - Runs OLS analysis using straight line distance and road distance
  - Inputs:
    - Workspace (FileGDB to store data)
    - Network dataset (created manually using the merged roads feature class)
    - sawmills (the modified feature class created by data_prep.py)
    - harvest sites (the modified feature class created by data_prep.py)
    - output directory (to store results)
    - Number of site-to-sawmill pairs per mill type (recommended at least 30)
    - Keep Output Paths? (simply true or false for if the output paths should be kept)
    - sawmill type (for if a single sawmill type is desired)