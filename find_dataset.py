# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FindDataset
                                 A QGIS plugin
 Finds datatesets, from a specific folder(s), that intersect a location in the map
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2018-10-17
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Luis Calisto and Andre Mano
        email                : luis.calisto@hotmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox, QTreeWidgetItem

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .find_dataset_dockwidget import FindDatasetDockWidget
import os.path

from .GetMapCoordinates import GetMapCoordinates
from .GetMapBbox import GetMapBbox
from .DatasetTools import DatasetTools
import webbrowser

# add qgis interaction 
from qgis.core import *
#from qgis.gui import QgsMessageBar
#from qgis.utils import iface

#need some processing as well:
import processing
from osgeo import osr

class FindDataset():
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        #variable to hold folder name in results
        self.selectedFolder=None
        self.getMapCoordTool=None
        self.getMapBboxTool=None
        self.selectedCoords4326=None
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'FindDataset_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Find Dataset')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'FindDataset')
        self.toolbar.setObjectName(u'FindDataset')

        #print "** INITIALIZING FindDataset"

        self.pluginIsActive = False
        self.dockwidget = None
        self.getMapCoordinates = GetMapCoordinates(self,self.iface)
        self.getMapBbox = GetMapBbox(self,self.iface)
        self.canvas = iface.mapCanvas()
        self.datasetTools=DatasetTools(self.iface)
        
    def loadDatasets(self):
        " Loads raster and vectors from the selected items in the treeWidget"
        selectedItems=self.dockwidget.treeWidget.selectedItems()
        if len(selectedItems)<1:
            QMessageBox.information(None, "Warning!", "No datasets selected. Please select at least one dataset from the results." )
            return
        rasters=[]
        vectors=[]
        # Fill the lists with selected datasets
        for item in selectedItems:
            if item.parent().text(0)=='Rasters':
                rasters.append(item.text(0))
            if item.parent().text(0)=='Vectors':
                #We need to remove 
                vectors.append(item.text(0))
        # Load selected datasets
        for raster in rasters:
            rasterPath=os.path.join(self.selectedFolder,raster)
            layer = self.iface.addRasterLayer(rasterPath, os.path.splitext(os.path.basename(raster))[0])
            if not layer:
              print("Layer failed to load!")
        for vector in vectors:
            #|layername=entities
            #Split vector to exctract possible layer names. We only need the path
            vectorList=vector.split()
            vectorPath=os.path.join(self.selectedFolder,vectorList[0])
            layer = self.iface.addVectorLayer(vectorPath, os.path.splitext(os.path.basename(vector))[0], "ogr")
            if not layer:
              print("Layer failed to load!")
    
    def extractExtent(self,layer,srs):
        it = layer.getFeatures()
        #print(geometry)
    
    def exportDatasets(self):
        " exports raster and vectorsfrom the selected items with their extent in a polygon geopackage"
        selectedItems=self.dockwidget.treeWidget.selectedItems()
        if len(selectedItems)<1:
            QMessageBox.information(None, "Warning!", "No datasets selected. Please select at least one dataset from the results." )
            return
        rasters=[]
        vectors=[]
        # Fill the lists with selected datasets
        for item in selectedItems:
            if item.parent().text(0)=='Rasters':
                rasters.append(item.text(0))
            if item.parent().text(0)=='Vectors':
                #We need to remove 
                vectors.append(item.text(0))
        #create layer in memory
        vl = QgsVectorLayer("Polygon", "catalog" , "memory")
        QgsProject.instance().addMapLayer(vl)
        pr = vl.dataProvider()

        # Enter editing mode
        vl.startEditing()

        # add fields
        pr.addAttributes( [ QgsField("name", QVariant.String),
                        QgsField("path",  QVariant.String),
                        QgsField("last edited", QVariant.DateTime),
                        QgsField("fields", QVariant.String),
                        QgsField("file Extension", QVariant.String)] )
        for raster in rasters:

            rasterPath=os.path.join(self.selectedFolder,raster)
            rasterName=raster
            rasterEdited=os.path.getmtime(rasterPath)
            rasterfields=""
            filename, file_extension = os.path.splitext(rasterPath)
            #get extent:
            rasterExtent = processing.run("qgis:polygonfromlayerextent", {'INPUT':rasterPath,'OUTPUT':'memory:'})
            it = rasterExtent['OUTPUT'].getFeatures()
                #unfortunately we need to transform a bit
            sourceCrs = rasterExtent['OUTPUT'].crs()
            # = QgsCoordinateReferenceSystem(4326)
            src_srs=osr.SpatialReference()
            src_srs.ImportFromEPSG(int(sourceCrs.authid()[5:]))
            tgt_srs=osr.SpatialReference()
            tgt_srs.ImportFromEPSG(4326)
            transform = osr.CoordinateTransformation( src_srs, tgt_srs)
            fet = QgsFeature()
            for feat in it:
                polygon = feat.geometry().asPolygon()
                points = []
                for point in polygon[0]:
                    x,y,z = transform.TransformPoint(point.x(), point.y())
                    points.append(QgsPointXY(x,y))
                fet.setGeometry(QgsGeometry.fromPolygonXY([points]))
                #feat.geometry().transform(tr)
            fet.setAttributes( [rasterName, rasterPath, rasterEdited, rasterfields, file_extension])
            pr.addFeatures( [ fet ] )
        for vector in vectors:
            vectorList=vector.split()
            vectorPath=os.path.join(self.selectedFolder,vectorList[0])
            vectorName=vector
            vectorEdited=os.path.getmtime(vectorPath)
            #deal with the fields:
            layer = QgsVectorLayer(vectorPath, os.path.splitext(os.path.basename(vector))[0], "ogr")
            fields = layer.fields()
            field_names = [field.name() for field in fields]
            vectorFields="; ".join(field_names)
            filename, file_extension = os.path.splitext(vectorName)
            #get extent:
            vectorExtent = processing.run("qgis:polygonfromlayerextent", {'INPUT':vectorPath,'OUTPUT':'memory:'})
            it = vectorExtent['OUTPUT'].getFeatures()
                #unfortunately we need to transform a bit
            #if sourceCrs.authid() != "EPSG:4326":
            sourceCrs = vectorExtent['OUTPUT'].crs()
            # = QgsCoordinateReferenceSystem(4326)
            src_srs=osr.SpatialReference()
            src_srs.ImportFromEPSG(int(sourceCrs.authid()[5:]))
            tgt_srs=osr.SpatialReference()
            tgt_srs.ImportFromEPSG(4326)
            transform = osr.CoordinateTransformation( src_srs, tgt_srs)
            fet = QgsFeature()
            for feat in it:
                polygon = feat.geometry().asPolygon()
                points = []
                for point in polygon[0]:
                    x,y,z = transform.TransformPoint(point.x(), point.y())
                    points.append(QgsPointXY(x,y))
                fet.setGeometry(QgsGeometry.fromPolygonXY([points]))
            fet.setAttributes( [vectorName, vectorPath, vectorEdited, vectorFields, file_extension])
            pr.addFeatures( [ fet ] )
        vl.commitChanges()
        mySymbol=QgsFillSymbol.createSimple({'color':"#ff0000",
                                                        'color_border':'#ff0000',
                                                        'width_border':'1',
                                                        'style':'no'})
        myRenderer = vl.renderer()
        myRenderer.setSymbol(mySymbol)
        vl.triggerRepaint()

    def applyAction(self):
        '''On apply button click'''
        # check if all requirements are set
        folderText=self.dockwidget.searchFolder.displayText()
        if folderText=='':
            QMessageBox.information(None, "Warning!", "No datasets folder selected. Please select a folder." )
            return
        recursiveBolean=self.dockwidget.recursiveSearch.isChecked()
        if self.selectedCoords4326==None:
            QMessageBox.information(None, "Warning!", "Please capture a coordinate/bbox from map canvas." )
            return
        #save folder name for later loading the datasets
        self.selectedFolder=folderText
        # perform the folder search with 4326 crs, check for Datasets
        rastersCheck=self.dockwidget.rastersBox.isChecked()
        vectorsCheck=self.dockwidget.vectorsBox.isChecked()
        intersectingDict=self.datasetTools.getDataset(self.selectedCoords4326,folderText,recursiveBolean,rastersCheck,vectorsCheck)
        #populate the gui list with the results
        #clear tree
        self.dockwidget.treeWidget.clear()
        if len(intersectingDict["rasters"])==0 and len(intersectingDict["vectors"])==0:
            # Add no data found
            r = QTreeWidgetItem(self.dockwidget.treeWidget, ['No datasets found!'])
            r.setFlags(r.flags() & ~Qt.ItemIsSelectable)
            self.dockwidget.treeWidget.addTopLevelItem(r)
        if len(intersectingDict["rasters"])>0:
            # Add rasters to Tree
            r = QTreeWidgetItem(self.dockwidget.treeWidget, ['Rasters'])
            r.setFlags(r.flags() & ~Qt.ItemIsSelectable)
            self.dockwidget.treeWidget.addTopLevelItem(r)
            for raster in intersectingDict["rasters"]:
                QTreeWidgetItem(r, [raster])
        if len(intersectingDict["vectors"])>0:
            # Add vectors to Tree
            v = QTreeWidgetItem(self.dockwidget.treeWidget, ['Vectors'])
            v.setFlags(v.flags() & ~Qt.ItemIsSelectable)
            self.dockwidget.treeWidget.addTopLevelItem(v)
            for idx,vector in enumerate(intersectingDict["vectors"]):
                # Shapefiles only have 1 layer. Therefore no need to add layer name.
                if vector.endswith('.shp'):
                    QTreeWidgetItem(v, [vector])
                else:
                    # add the vector filepath + the layers string into the interface
                    #Join the vector layers into a string
                    vectorLayers=', '.join(intersectingDict["vectorLayers"][idx])
                    QTreeWidgetItem(v, [vector+" ("+vectorLayers+")"])
        self.dockwidget.treeWidget.expandAll()
    def helpAction(self):
        '''Display a help page'''
        webbrowser.open('https://github.com/lcalisto/qgis-finddataset-plugin', new=2)
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('FindDataset', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action
    
    def select_folder(self):
        foldername = QFileDialog.getExistingDirectory(self.dockwidget, "Select folder ","",)
        self.dockwidget.searchFolder.setText(foldername)
    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        
        #icon_path = ':/plugins/find_dataset/icon.png'
        icon_path = os.path.join(os.path.dirname(__file__),"icon.png")
        self.add_action(
            icon_path,
            text=self.tr(u'Find dataset'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""
        print('plugin closed')
        #Remove getMapCoordinates action
        self.canvas.unsetMapTool(self.getMapCoordinates)
        self.canvas.unsetMapTool(self.getMapBbox)
        #print "** CLOSING FindDataset"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD FindDataset"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Find Dataset'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        #Remove getMapCoordinates action. I'm not sure if this needs to be here!
        self.canvas.unsetMapTool(self.getMapCoordinates)

    #--------------------------------------------------------------------------
    def setGetMapToolCoord(self):
        """ Method that is connected to the target button. Activates and deactivates map tool """
        if self.dockwidget.captureButton.isChecked():
            #print('point not checked')
            self.canvas.unsetMapTool(self.getMapCoordTool)
            self.dockwidget.captureButton_2.setChecked(True)
        elif not self.dockwidget.captureButton.isChecked():
            #print('point checked')
            self.dockwidget.captureButton_2.setChecked(False)
            self.canvas.setMapTool(self.getMapCoordTool)
            
    def setGetMapToolBbox(self):
        """ Method that is connected to the target button. Activates and deactivates map tool """
        if self.dockwidget.captureButton_2.isChecked():
            #print('bbox not checked')
            self.canvas.unsetMapTool(self.getMapBboxTool)
            self.dockwidget.captureButton_2.setChecked(True)
        elif not self.dockwidget.captureButton_2.isChecked():
            #print('bbox checked')
            self.dockwidget.captureButton.setChecked(False)
            self.canvas.setMapTool(self.getMapBboxTool)
        
    def run(self):
        """Run method that loads and starts the plugin"""
        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING FindDataset"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = FindDatasetDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
            # clear previous selected folders
            self.dockwidget.searchFolder.clear()
            # Connect select button to select_output_file method
            self.dockwidget.toolButton.pressed.connect(self.select_folder)
            self.dockwidget.applyButton.pressed.connect(self.applyAction)
            self.dockwidget.loadButton.pressed.connect(self.loadDatasets)
            self.dockwidget.exportButton.pressed.connect(self.exportDatasets)
            self.dockwidget.helpButton.pressed.connect(self.helpAction)
            # Activate click tool in canvas.
            self.dockwidget.captureButton.setIcon(QIcon(os.path.join(os.path.dirname(__file__),"target.png")))
            self.dockwidget.captureButton.setChecked(True)
            self.dockwidget.captureButton.pressed.connect(self.setGetMapToolCoord)
            #deal with bbox button
            self.dockwidget.captureButton_2.setIcon(QIcon(os.path.join(os.path.dirname(__file__),"bbox.png")))
            self.dockwidget.captureButton_2.setChecked(False)
            self.dockwidget.captureButton_2.pressed.connect(self.setGetMapToolBbox)
            self.getMapBboxTool=self.getMapBbox
            self.getMapBboxTool.setButton(self.dockwidget.captureButton_2)  
            self.getMapBboxTool.setDockwidget(self.dockwidget)
            
            self.getMapCoordTool=self.getMapCoordinates
            self.getMapCoordTool.setButton(self.dockwidget.captureButton)  
            self.getMapCoordTool.setDockwidget(self.dockwidget)
            self.canvas.setMapTool(self.getMapCoordTool)
            

