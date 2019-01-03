'''
Part of this code was adapted from the Lat Lon Tools Plugin
https://github.com/NationalSecurityAgency/qgis-latlontools-plugin

More precisely from
https://github.com/NationalSecurityAgency/qgis-latlontools-plugin/blob/master/showOnMapTool.py

'''
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import Qgis,QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.gui import QgsMapToolExtent



class GetMapBbox(QgsMapToolExtent):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed.'''
    def __init__(self,find_dataset, iface):
        QgsMapToolExtent.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.extentChanged.connect(self.extentChange)
        self.find_dataset=find_dataset
        #self.bbox4326=None # This will be a QgsRectangle object
          


    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        
        
    def extentChange(self, bbox):
        '''Capture the bbox when the mouse button has been released,
        format it, and copy it to dashboard'''
        # transform the coordinate to 4326 but display it in the original crs
        canvasCRS = self.canvas.mapSettings().destinationCrs()
        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
        bbox4326 = transform.transformBoundingBox(bbox)
        #change dockwidget corrdinate with the original crs
        self.dockwidget.coordinateText.setText(bbox.toString(3))
        #assign point in 4326 crs to attribute so it can be used in other classes.
        #self.bbox4326=bbox4326
        self.find_dataset.selectedCoords4326=bbox4326
        
    def setDockwidget(self, dockwidget):
        self.dockwidget=dockwidget