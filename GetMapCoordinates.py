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
    def __init__(self, settings, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        #self.settings = settings
        self.canvasClicked.connect(self.clicked)
        
    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        
    def clicked(self, pt, b):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to dashboard'''
        canvasCRS = self.canvas.mapSettings().destinationCrs()
        #FindDataset.get_datasets(pt,canvasCRS)
        self.dockwidget.coordinateText.setText(str("%.4f" % pt.x())+' , '+str("%.4f" % pt.y()))
        print(self.dockwidget.recursiveSearch.isChecked())
        print(self.dockwidget.searchFolder.displayText())
    def setDockwidget(self, dockwidget):
        self.dockwidget=dockwidget