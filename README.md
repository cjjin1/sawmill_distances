Documentation:
Data required for scripts:
1. NFS Roads Dataset
2. Sawmill dataset
3. [Optional] Boundary dataset

Data prep:
- All input files are done as full path
1. roads_data_prep.py
  - Uses OSM data to retrieve road data for network analyst
  - Depending on size of location chosen, may take several minutes
  - Inputs: <output_roads_file> <output_nodes_files> <aoi>   OR    <output_roads_file> <output_nodes_files> <north> <south> <east> <west>
      - output roads File GDB (must be created beforehand)
      - output nodes File GDB (must be created beforehand, currently not used in script)
      - aoi (string of place to gather data for, eg. "Mississippi, USA")
        - or -
      - North, South, East, West coordinates for a bounding box
  - Example Input:
      F:/timber_project/data/ms_roads.gdb
      F:/timber_project/data/ms_nodes.gdb
      "Mississippi, USA"

2. data_prep.py
  - Prepares data with various operations:
      - projection
      - clipping
      - Creating intersection points
      - adding distance field to roads dataset
      - creating network dataset
  - Building the network dataset is done within ArcGIS Pro manually, not in the script
  - Inputs: <Workspace> <Feature Dataset> <Roads Dataset> <NFS Roads Shapefile> <sawmill shapefile> <[optional] Boundary Shapefile>
      - Workspace (directory to store data)
      - Feature Dataset (Feature Dataset within a File GDB, must be created beforehand)
      - Roads Dataset (path to roads dataset created in roads_data_prep.py)
      - NFS Roads Shapefile (dataset of NFS roads)
      - sawmill shapefile (dataset of sawmills)
      - [optional] Boundary Shapefile (if any dataset extends past the desired area of interest)
  - Example Input:
      F:/timber_project/scratch/MS_OSM_test
      F:/timber_project/scratch/MS_OSM_test/MS_OSM_ND.gdb/Transportation
      F:/timber_project/data/ms_roads.gdb/roads
      F:/timber_project/data/RoadCore_FS.shp
      F:/timber_project/data/sawmill_geocoded.shp
      F:/timber_project/data/GOVTUNIT_Mississippi_State_Shape/Shape/GU_StateOrTerritory.shp

To run distance calculations:
- Create a script and import the distance_calculator.py script
- Call on specific distance calculation function with input files produced by data prep scripts
- Will need to input only one start and end point when using network analyst based distance calculations, only designed for one start and end point
