Documentation:
For the data preparation scripts, use in the order shown below.

Data preparation:
- All input files are done as full path unless specified otherwise
- Three scripts must be run in order.
1. create_boundaries.py (optional)
  - This script is very simple and can be done manually instead. 
    - Simply clip the ranger districts shapefile using the physiographic region.
    - Then buffer the resulting shapefile by 125 miles.
  - The output needs to be a shapefile, it cannot be a feature class in a File GDB. By default, the script puts the output
    in the same directory as the physiographic region feature class. If this is a File GDB, use the full path for the 
    output file. Otherwise, just the basename is acceptable.
  - Input:
    - park boundaries (ranger_districts.shp)
      - the ranger_districts.shp shapefile contains data for all of US. Every run of this tool (and following tools) 
        should use this shapefile
    - physiographic shapefile/fc
      - This shapefile/fc should be the desired physiographic region (boundaries for desired harvest sites.)
    - output name
      - The output name for the new boundary shapefile. This will be used to get roads for osm_roads_planet.py. 

2. osm_roads_planet.py
  - This script returns osm roads for a bounding box derived from a boundary shapefile
  - Input:
    - osm planet file
      - This will be a file ending in .osm.pbf, usually called us-<yymmdd>.osm.pbf. This file is for the entire US,
        this input should not change unless the file path changes.
    - boundary file
      - Defines the bounding box for obtaining roads. Must be a shapefile. This is obtained from the 
        create_boundaries.py script but can also be obtained manually.
    - output name
      - Name of the created feature class. Use only the basename as the script will create a File GDB to store the
        output. Do not include an extension.
    - directory path
      - Full path for a directory to store the results. Does not need to be empty but is recommended to store all 
        outputs from multiple runs of this script separately.
    - log file path (optional)
      - Full file path and file name for where to store the log. If no option is selected, the default location
        is the project folder for where the script is in and is called 'osm_road.log'

3. data_prep.py
  - This script does the bulk of the data preparation:
    - cleaning harvest site data
    - cleaning sawmill data
    - merging the roads 
    - creating the network dataset
  - This script DOES NOT build the network nor does it implement the one way restriction. Those must be done manually.
    - Go to the BEFORE CALCULATIONS selection for more details.
  - In this script, there is a process function that has parameters for skipping steps. By default the entire process 
    will run. DO NOT change this as some functions are required to be run first before others. This is more for 
    testing purposes.
  - Input:
    - New File GDB
      - This File GDB will be created by using Data Interoperability's Quick Import tool.
        - This cannot be an existing File GDB. It also must be a File GDB.
      - This File GDB will also act as the workspace and store all other output files
      - A feature dataset called 'Transportation' is created in this File GDB which will contain the network dataset
    - total roads feature class
      - This is the file path for the osm roads feature class created by the osm_roads_planet.py script
    - NFS roads (RoadCore_FS.shp)
      - This argument should always be the RoadCore_FS.shp shapefile as it covers the entire US
    - sawmill dataset (forisk_sawmills_US_only.shp)
      - This argument should always be the forisk_sawmills_US_only.shp shapefile as it covers the entire US. 
      - The exact shapefile may be under a different name.
    - harvest site dataset (Activity_TimberHarvest.shp)
      - This argument should always be Activity_TimberHarvest.shp shapefile as it covers the entire US.
      - The exact shapefile may be under a different name
    - park boundaries (ranger_districts.shp)
      - The ranger district shapefile will likely be under a different name
      - This shapefile will be the boundaries for all forests containing harvest sites.
      - This is the same shapefile used in create_boundaries.py
    - physiographic shapefile/fc
      - This shapefile/fc should be the desired physiographic region (boundaries for desired harvest sites.)
      - This is the same argument used in create_boundaries.py
    - spatial reference
      - Use the EPSG code for spatial reference
    
BEFORE CALCULATIONS:
1. Time cost functionality must be manually implemented in ArcGSI Pro. To do so, follow these steps:
  - Open the streets_nd network dataset properties in the catalog
  - Create a new travel mode called "Driving Distance"
  - Under the Costs tab, create a new cost by clicking the 3 lines in the top right and selecting "New"
    - name the cost "TimeCost"
    - Set the units to hours
    - For evaluators:
      - set the type as "Field Script" for both Along and Against
      - for both Along and Against, set the value to the !travel_time! field
  - While at the Costs tab, ensure the created distance field is used for the default "Length" cost with Miles as units
  - It is not necessary to select this new time cost in the "Travel Modes" tab
2. Oneway functionality must also be manually implemented in ArcGIS Pro. To do so, follow these steps:
  - Under the Restrictions tab, create a new restriction called "Oneway"
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

