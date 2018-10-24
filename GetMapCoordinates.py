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
from qgis.gui import QgsMapToolEmitPoint



class GetMapCoordinates(QgsMapToolEmitPoint):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed.'''
    def __init__(self, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.canvasClicked.connect(self.clicked)
        self.pt4326=None

    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        
    def clicked(self, pt, b):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to dashboard'''
        # transform the coordinate to 4326 but display it in the original crs
        canvasCRS = self.canvas.mapSettings().destinationCrs()
        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
        pt4326 = transform.transform(pt.x(), pt.y())
        lat = pt4326.y()
        lon = pt4326.x()
        #change dockwidget corrdinate with the original crs
        self.dockwidget.coordinateText.setText(str("%.4f" % pt.x())+' , '+str("%.4f" % pt.y()))
        #assign point in 4326 crs to attribute so it can be used in other classes.
        self.pt4326=pt4326
        
    def setDockwidget(self, dockwidget):
        self.dockwidget=dockwidget