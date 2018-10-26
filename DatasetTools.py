from osgeo import gdal,ogr,osr
gdal.UseExceptions() 
import os, stat

class DatasetTools():
    '''Class to interact with raster files'''
    def __init__(self, iface):
        self.iface = iface
        #endswith also accepts tuples. This is the tuple of vector extensions
        self.vectorFiles=('shp')
        self.exclude= (".3g2", ".3gp", ".asf", ".asx", ".avi", ".flv", 
           ".m2ts", ".mkv", ".mov", ".mp4", ".mpg", ".mpeg",
           ".rm", ".swf", ".vob", ".wmv" ".docx", ".pdf",".rar", ".zip", ".7z", ".exe", 
           ".tar.gz", ".tar", ".mp3", ".sh", ".c", ".cpp", ".h", 
       ".gif", ".py", ".pyc", ".jar", ".sql", ".bundle",
       ".html", ".php", ".log", ".bak", ".deb", "py","pdf","ppt","pptx","doc","docx","jar","shx","dbf","ini","dll","xls","xlsx")
    def isHiddenWindows(self,filepath):
        """ This function returns True is a file is hidden in windows"""
        try:
            return bool(os.stat(filepath).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)
        except:
            return None
    def GetExtent(self,gt,cols,rows):
        ''' Return list of corner coordinates from a geotransform
    
            @type gt:   C{tuple/list}
            @param gt: geotransform
            @type cols:   C{int}
            @param cols: number of columns in the dataset
            @type rows:   C{int}
            @param rows: number of rows in the dataset
            @rtype:    C{[float,...,float]}
            @return:   coordinates of each corner, ORDER is: tr,lr,ll,tl
        '''
        ext=[]
        xarr=[0,cols]
        yarr=[0,rows]
    
        for px in xarr:
            for py in yarr:
                x=gt[0]+(px*gt[1])+(py*gt[2])
                y=gt[3]+(px*gt[4])+(py*gt[5])
                ext.append([x,y])
            yarr.reverse()
        return ext
    def ReprojectCoords(self,coords,src_srs,tgt_srs):
        ''' Reproject a list of x,y coordinates.
    
            @type geom:     C{tuple/list}
            @param geom:    List of [[x,y],...[x,y]] coordinates
            @type src_srs:  C{osr.SpatialReference}
            @param src_srs: OSR SpatialReference object
            @type tgt_srs:  C{osr.SpatialReference}
            @param tgt_srs: OSR SpatialReference object
            @rtype:         C{tuple/list}
            @return:        List of transformed [[x,y],...[x,y]] 
        '''
        trans_coords=[]
        transform = osr.CoordinateTransformation( src_srs, tgt_srs)
        for x,y in coords:
            x,y,z = transform.TransformPoint(x,y)
            trans_coords.append([x,y])
        return trans_coords
    def CheckIntersection(self,pt,ext,vector):
        ''' Check if a poin is inside an extent
    
            @type ext:     C{tuple/list}
            @param ext:    List of [[x,y],...[x,y]] extent coordinates
            @type pt:  C{tuple/list}
            @param pt: Point coordinates
            @type vector:  Boolean
            @param vector: If the extent is from a vector or a raster. Raster extents are 4 coordinates and vectors are 2 coordinates
            @rtype:         Boolean
            @return:        Is inside or not, True or False
        '''
        #print(pt.x())
        #print(pt.y())
        #print(ext)
        if vector:
            return ext[0][0] < pt.x() < ext[1][0] and ext[0][1] < pt.y() < ext[1][1]
        else:
            return ext[1][0] < pt.x() < ext[3][0] and ext[1][1] < pt.y() < ext[3][1]
    
    def getRasters(self, pt, folder, recursive):
        '''
        Process raster files and return intersecting rasters
        '''
        #loop in the folder files
        #print('start the loop',folder)
        intersectingRasters=[]
        if recursive:
            for dir_, _, files in os.walk(folder):
                # exclude linux hidden files and folders
                if os.name=='posix':
                    files[:] = [f for f in files if not f.startswith('.')]
                    _[:] = [f for f in _ if not f.startswith('.')]
                # exclude the folowing extencions, both windows or linux
                files[:] = [f for f in files if not f.endswith(self.exclude)]
                for filename in files:
                    relDir = os.path.relpath(dir_, folder)
                    relFile = os.path.join(relDir, filename)
                    #In linux
                    relFile=relFile.replace('./', '')
                    #In windows
                    relFile = relFile.replace('.\\', '')
                    fullFile= os.path.join(dir_, filename)
                    # Excape windows hidden files.
                    if os.name=='nt':
                        if self.isHiddenWindows(fullFile):
                            continue
                    try:
                        #Open raster file and get its extent
                        ds=gdal.Open(fullFile)
                        gt=ds.GetGeoTransform()
                        cols = ds.RasterXSize
                        rows = ds.RasterYSize
                        ext=self.GetExtent(gt,cols,rows)
                        # reproject the extent to 4326 because the point will always be 4326 (to keep srs consistency)
                        src_srs=osr.SpatialReference()
                        src_srs.ImportFromWkt(ds.GetProjection())
                        tgt_srs=osr.SpatialReference()
                        tgt_srs.ImportFromEPSG(4326)
                        wgs84_ext=self.ReprojectCoords(ext,src_srs,tgt_srs)
                        #Check if raster files intersect this 4 pair of coordinates
                        isIntersecting=self.CheckIntersection(pt,wgs84_ext,False)
                        if isIntersecting:
                            intersectingRasters.append(relFile)
                        continue  
                    except:
                        continue       
                    
        else:
            for filename in os.listdir(folder):
                # Excape windows hidden files.
                if os.name=='nt':
                    if self.isHiddenWindows(os.path.join(folder, filename)):
                        continue
                # Excape linux hidden files.
                if os.name=='posix':
                    if filename.startswith('.'):
                        continue
                #excluding custom files
                if filename.endswith(self.exclude):
                    continue
                try:
                    #Open raster file and get its extent
                    ds=gdal.Open(os.path.join(folder, filename))
                    gt=ds.GetGeoTransform()
                    cols = ds.RasterXSize
                    rows = ds.RasterYSize
                    ext=self.GetExtent(gt,cols,rows)
                    # reproject the extent to 4326 because the point will always be 4326 (to keep srs consistency)
                    src_srs=osr.SpatialReference()
                    src_srs.ImportFromWkt(ds.GetProjection())
                    tgt_srs=osr.SpatialReference()
                    tgt_srs.ImportFromEPSG(4326)
                    wgs84_ext=self.ReprojectCoords(ext,src_srs,tgt_srs)
                    #Check if raster files intersect this 4 pair of coordinates
                    isIntersecting=self.CheckIntersection(pt,wgs84_ext,False)
                    if isIntersecting:
                        intersectingRasters.append(filename)
                    continue
                except:
                    continue
        return intersectingRasters
    
    def getVectors(self, pt, folder, recursive):
        '''
        Process vector files and return intersecting vectos
        '''
        #loop in the folder files
        #print('start the loop',folder)
        intersectingVectors=[]
        if recursive:
            for dir_, _, files in os.walk(folder):
                # exclude linux hidden files and folders
                if os.name=='posix':
                    files[:] = [f for f in files if not f.startswith('.')]
                    _[:] = [f for f in _ if not f.startswith('.')]
                # exclude the folowing extencions, both windows or linux
                files[:] = [f for f in files if not f.endswith(self.exclude)]
                for filename in files:
                    relDir = os.path.relpath(dir_, folder)
                    relFile = os.path.join(relDir, filename)
                    #in linux
                    relFile=relFile.replace('./', '')
                    #in Windows
                    relFile = relFile.replace('.\\', '')
                    fullFile= os.path.join(dir_, filename)
                    # Excape windows hidden files.
                    if os.name=='nt':
                        if self.isHiddenWindows(fullFile):
                            continue
                    #removing folders ('')
#                     if filename.endswith(''):
#                         continue
                    try:
                        #Open vector file and get its extent
                        ds=ogr.Open(fullFile)
                        #todo loop to all the vector layers and check if the point intersects at least one Layer. Shapes only have one layer but other formats may have more.
                        layer=ds.GetLayer(0)
                        layerExtents=layer.GetExtent()
                        #print("x_min = %.2f x_max = %.2f y_min = %.2f y_max = %.2f" % (layerExtents[0], layerExtents[1], layerExtents[2], layerExtents[3]))
                        # reproject the extent to 4326 because the point will always be 4326 (to keep srs consistency)
                        src_srs=osr.SpatialReference()
                        src_srs.ImportFromWkt(str(layer.GetSpatialRef()))
                        tgt_srs=osr.SpatialReference()
                        tgt_srs.ImportFromEPSG(4326)
                        layerExt=[[layerExtents[0],layerExtents[2]],[layerExtents[1],layerExtents[3]]]
                        wgs84_ext=self.ReprojectCoords(layerExt,src_srs,tgt_srs)
                        #Check if point intersects this pair of coordinates (vector extents)
                        isIntersecting=self.CheckIntersection(pt,wgs84_ext,True)
                        if isIntersecting:
                            intersectingVectors.append(relFile)
                        continue
                    except:
                        continue
        else:
            for filename in os.listdir(folder):
                # Excape windows hidden files.
                if os.name=='nt':
                    if self.isHiddenWindows(os.path.join(folder, filename)):
                        continue
                # Excape linux hidden files.
                if os.name=='posix':
                    if filename.startswith('.'):
                        continue
                #excluding custom files, folders ('')
                if filename.endswith(self.exclude):
                    continue
                try:
                    #Open vector file and get its extent
                    ds=ogr.Open(os.path.join(folder, filename))
                    #todo loop to all the vector layers and check if the point intersects at least one Layer. Shapes only have one layer but other formats may have more.
                    layer=ds.GetLayer(0)
                    layerExtents=layer.GetExtent()
                    #print("x_min = %.2f x_max = %.2f y_min = %.2f y_max = %.2f" % (layerExtents[0], layerExtents[1], layerExtents[2], layerExtents[3]))
                    # reproject the extent to 4326 because the point will always be 4326 (to keep srs consistency)
                    src_srs=osr.SpatialReference()
                    src_srs.ImportFromWkt(str(layer.GetSpatialRef()))
                    tgt_srs=osr.SpatialReference()
                    tgt_srs.ImportFromEPSG(4326)
                    layerExt=[[layerExtents[0],layerExtents[2]],[layerExtents[1],layerExtents[3]]]
                    wgs84_ext=self.ReprojectCoords(layerExt,src_srs,tgt_srs)
                    #Check if point intersects this pair of coordinates (vector extents)
                    isIntersecting=self.CheckIntersection(pt,wgs84_ext,True)
                    if isIntersecting:
                        intersectingVectors.append(filename)
                    continue
                except:
                    continue
#                 if filename.endswith(self.vectorFiles): 
#                     #print(os.path.join(folder, filename))
#                     #Open vector file and get its extent
#                     ds=ogr.Open(os.path.join(folder, filename))
#                     #todo loop to all the vector layers and check if the point intersects at least one Layer. Shapes only have one layer but other formats may have more.
#                     layer=ds.GetLayer(0)
#                     layerExtents=layer.GetExtent()
#                     #print("x_min = %.2f x_max = %.2f y_min = %.2f y_max = %.2f" % (layerExtents[0], layerExtents[1], layerExtents[2], layerExtents[3]))
#                     # reproject the extent to 4326 because the point will always be 4326 (to keep srs consistency)
#                     src_srs=osr.SpatialReference()
#                     src_srs.ImportFromWkt(str(layer.GetSpatialRef()))
#                     tgt_srs=osr.SpatialReference()
#                     tgt_srs.ImportFromEPSG(4326)
#                     layerExt=[[layerExtents[0],layerExtents[2]],[layerExtents[1],layerExtents[3]]]
#                     wgs84_ext=self.ReprojectCoords(layerExt,src_srs,tgt_srs)
#                     #Check if point intersects this pair of coordinates (vector extents)
#                     isIntersecting=self.CheckIntersection(pt,wgs84_ext,True)
#                     if isIntersecting:
#                         intersectingVectors.append(filename)
#                     continue
#                 else:
#                     # do nothing. This are not raster files
#                     continue
        return intersectingVectors