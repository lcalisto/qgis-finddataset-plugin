
# Welcome to FindDataset's plugin documentation!
============================================

## What is **FindDataset** plugin?

**FindDataset** plugin scans a directory and its subdirectories for raster and/or vector datasets that overlap the location the user specifies in QGIS map canvas. The location can be provided as a point or as an area. Once the datasets are identified there is the possibility to (1) add some or all of those datasets to QGIS map canvas and (2) export the results to a new catalag layer consisting of the bounding boxes of each of the identified layers along with these attributes: *name*, *path*, *last_edited*, *fields* and *file extension*

## How to install **FindDataset**?

You can install this plugin from the official QGIS plugin repository. [https://plugins.qgis.org/plugins/finddataset](https://plugins.qgis.org/plugins/finddataset) 

## How does **FindDataset** works?

The plugin takes the coordinates of the location the user specifies in the CRS of the QGIS project. It then converts that coordinate to WGS84. After a directory is specified, the plugin reads the metadata of the datasets that are in that directory and calculates the extent also in WGS84 CRS. Finally it looks for intersections between the location the user provided and the spatial extent of the datasets. 

## How to use **FindDataset**?

A usage example can be seen below.

Loading datasets:

![]( find_dataset.gif)



Exporting to catalog:*

![]( find_dataset_catalog.gif)



*the catalog layer is always created in WGS84.
