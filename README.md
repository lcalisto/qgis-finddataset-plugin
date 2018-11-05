# qgis-finddataset-plugin

# H1 Welcome to FindDataset's documentation!
============================================

## H2 What is **FindDataset** plugin?

*FindDataset** plugin scans a directory and its subdirectories for raser and/or vector datasets that overlap the location the user specifies in QGIS map canvas. Once the datasets are identified, there is the possibility to add some or all of those datasets to QGIS map canvas.

## H2 How does **FindDataset** works?

The plugin takes the coordinates of the location the user specifies according to the CRS of the QGIS project. It then converts that coordinate to WGS 84. After a directory is specified, the plugin reads the metadata of the datasets that are in that directory and calculates the extent in the WGS84 CRS too. Finally it looks for intersections between the location the user provided and the spatial extent of the datasets. 

## H2 How to use **FindDataset** works?

A usage example can be seen below:

![]( find_dataset.gif)

