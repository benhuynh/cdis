'''
ABOUT:
This python script will take a hyperion image and produce a .txt file of reflectances per pixel per band. Based on eo1-demo/classify.py and eo1-wheel-demo/classifiermapper.py
DEPENDS:
gdal
numpy
HISTORY:
March 2015: Original script
USE:
tbd
'''
from osgeo import gdal,osr
import numpy as np
import argparse
import scipy.misc as mpimg
import time
import csv
import numpy.ma as ma
import os.path

# Class: test
#
# Object to retrieve reflectances from a hyp scene


class test(object):
    
    # initializer
    # 
    # str: filePre, prefix for EO-1 Scene files

    def __init__(self,filePre=object):
        self.fullTrainSet = np.array([])
        self.fullTestSet = np.array([])
        self.trainSet = np.array([])
        self.trainLab = None
        self.filePre = filePre
        self.createMetadata()
        self.bands = np.array([])
        self.testSet = np.array([])
        self.dims = None
        self.mask = None
        self.answers = None
        self.tester = None

    # setUpTest
    # 
    # Loads band GeoTiffs from gluster into test set

    def setUpTest(self):
        bandList = np.array(['_B001','_B002','_B003','_B004','_B005','_B006','_B007','_B008','_B009','_B010','_B011','_B012','_B013','_B014','_B015','_B016','_B017','_B018','_B019','_B020','_B021','_B022','_B023','_B024','_B025','_B026','_B027','_B028','_B029','_B030','_B031','_B032','_B033','_B034','_B035','_B036','_B037','_B038','_B039','_B040','_B041','_B042','_B043','_B044','_B045','_B046','_B047','_B048','_B049','_B050','_B051','_B052','_B053','_B054','_B055','_B056','_B057','_B058','_B059','_B060','_B061','_B062','_B063','_B064','_B065','_B066','_B067','_B068','_B069','_B070','_B071','_B072','_B073','_B074','_B075','_B076','_B077','_B078','_B079','_B080','_B081','_B082','_B083','_B084','_B085','_B086','_B087','_B088','_B089','_B090','_B091','_B092','_B093','_B094','_B095','_B096','_B097','_B098','_B099','_B100','_B101','_B102','_B103','_B104','_B105','_B106','_B107','_B108','_B109','_B110','_B111','_B112','_B113','_B114','_B115','_B116','_B117','_B118','_B119','_B120','_B121','_B122','_B123','_B124','_B125','_B126','_B127','_B128','_B129','_B130','_B131','_B132','_B133','_B134','_B135','_B136','_B137','_B138','_B139','_B140','_B141','_B142','_B143','_B144','_B145','_B146','_B147','_B148','_B149','_B150','_B151','_B152','_B153','_B154','_B155','_B156','_B157','_B158','_B159','_B160','_B161','_B162','_B163','_B164','_B165','_B166','_B167','_B168','_B169','_B170','_B171','_B172','_B173','_B174','_B175','_B176','_B177','_B178','_B179','_B180','_B181','_B182','_B183','_B184','_B185','_B186','_B187','_B188','_B189','_B190','_B191','_B192','_B193','_B194','_B195','_B196','_B197','_B198','_B199','_B200','_B201','_B202','_B203','_B204','_B205','_B206','_B207','_B208','_B209','_B210','_B211','_B212','_B213','_B214','_B215','_B216','_B217','_B218','_B219','_B220','_B221','_B222','_B223','_B224','_B225','_B226','_B227','_B228','_B229','_B230','_B231','_B232','_B233','_B234','_B235','_B236','_B237','_B238','_B239','_B240','_B241','_B242'])
        for band in np.arange(242):
            bandName = bandList[band]
            tifFile = gdal.Open(self.filePre+bandName+'_L1T.TIF')
            rast = tifFile.GetRasterBand(1)
            arr = rast.ReadAsArray()
            if self.dims == None: self.dims = arr.shape
            arra = np.reshape(arr,(arr.size,1))

            if self.mask == None: self.mask = np.reshape((arra==0),arra.size)
            mArra = ma.masked_array(arra,self.mask)
            if self.fullTestSet.size == 0:
                self.fullTestSet = mArra                
                self.bands = np.array([band])
            else:
                self.fullTestSet = np.concatenate((self.fullTestSet,mArra),axis=1)            
                self.bands = np.concatenate((self.bands,np.array([band])))
            print(band)
        self.hypSolarIrradiance()
        print('hsi complete!')
        self.geometricCorrection()
        print('gc complete!')

# metadata for ALI scene, and stores in test object for further reference

    def createMetadata(self):
        l1t = {}

        filename = self.filePre+"_MTL_L1T.TXT"

        with open(filename) as l1tFile:
            last = l1t
            stack = []
            for line in l1tFile.xreadlines():
                if line.rstrip() == "END": break
                name, value = line.rstrip().lstrip().split(" = ")
                value = value.rstrip("\"").lstrip("\"")
                if name == "GROUP":
                    stack.append(last)
                    last = {}
                    l1t[value] = last
                elif name == "END_GROUP":
                    last = stack.pop()
                else:
                    last[name] = value

        self.metadata = l1t
        pass

    def geometricCorrection(self):
    #Perform Geometric Correction for Hyperion and rescale ALI radiances for reflectance
    #metadata: L1T metadata dictionary
    #bands: dictionary of band values
    #output: modified band dictionary
    #
    #From http://eo1.usgs.gov/faq/question?id=21

        metadata = self.metadata
        earthSunDistance = np.array([[1,.9832], [15,.9836], [32,.9853], [46,.9878], [60,.9909],
                                     [74, .9945], [91, .9993], [106, 1.0033], [121, 1.0076], [135, 1.0109],
                                     [152, 1.0140], [166, 1.0158], [182, 1.0167], [196, 1.0165], [213, 1.0149],
                                     [227, 1.0128], [242, 1.0092], [258, 1.0057], [274, 1.0011], [288, .9972],
                                     [305, .9925], [319, .9892], [335, .9860], [349, .9843], [365, .9833],[366, .9832375]])
    
        julianDate = time.strptime(metadata["PRODUCT_METADATA"]["START_TIME"], "%Y %j %H:%M:%S").tm_yday
        eSD = np.interp( np.linspace(1,366,366), earthSunDistance[:,0], earthSunDistance[:,1] )
        esDist = eSD[julianDate-1]
    
        sunAngle = float(metadata["PRODUCT_PARAMETERS"]["SUN_ELEVATION"])
        sunAngle = sunAngle*np.pi/180.
        for i in self.bands:
            value = self.fullTestSet[i]
            self.fullTestSet[i] = np.pi * esDist**2 * value / np.sin(sunAngle)    # apply same correction to all bands
            print(i)
        pass

    def hypSolarIrradiance(self):
    #Correct irradiance for Hyperion data - convert radiance to reflectance.
    #bands: dictionary of band radiances
    #output: modified band dictionary
    
    # From http://eo1.usgs.gov/documents/hyp_irradiance.txt
    # Left column is band number, right is spectral irradiance in W/(m^2-um)
        Esun_hyp = np.array([
                [  1.00000000e+00,   9.49370000e+02],
                [  2.00000000e+00,   1.15878000e+03],
                [  3.00000000e+00,   1.06125000e+03],
                [  4.00000000e+00,   9.55120000e+02],
                [  5.00000000e+00,   9.70870000e+02],
                [  6.00000000e+00,   1.66373000e+03],
                [  7.00000000e+00,   1.72292000e+03],
                [  8.00000000e+00,   1.65052000e+03],
                [  9.00000000e+00,   1.71490000e+03],
                [  1.00000000e+01,   1.99452000e+03],
                [  1.10000000e+01,   2.03472000e+03],
                [  1.20000000e+01,   1.97012000e+03],
                [  1.30000000e+01,   2.03622000e+03],
                [  1.40000000e+01,   1.86024000e+03],
                [  1.50000000e+01,   1.95329000e+03],
                [  1.60000000e+01,   1.95355000e+03],
                [  1.70000000e+01,   1.80456000e+03],
                [  1.80000000e+01,   1.90551000e+03],
                [  1.90000000e+01,   1.87750000e+03],
                [  2.00000000e+01,   1.88351000e+03],
                [  2.10000000e+01,   1.82199000e+03],
                [  2.20000000e+01,   1.84192000e+03],
                [  2.30000000e+01,   1.84751000e+03],
                [  2.40000000e+01,   1.77999000e+03],
                [  2.50000000e+01,   1.76145000e+03],
                [  2.60000000e+01,   1.74080000e+03],
                [  2.70000000e+01,   1.70888000e+03],
                [  2.80000000e+01,   1.67209000e+03],
                [  2.90000000e+01,   1.63283000e+03],
                [  3.00000000e+01,   1.59192000e+03],
                [  3.10000000e+01,   1.55766000e+03],
                [  3.20000000e+01,   1.52541000e+03],
                [  3.30000000e+01,   1.47093000e+03],
                [  3.40000000e+01,   1.45037000e+03],
                [  3.50000000e+01,   1.39318000e+03],
                [  3.60000000e+01,   1.37275000e+03],
                [  3.70000000e+01,   1.23563000e+03],
                [  3.80000000e+01,   1.26613000e+03],
                [  3.90000000e+01,   1.27902000e+03],
                [  4.00000000e+01,   1.26522000e+03],
                [  4.10000000e+01,   1.23537000e+03],
                [  4.20000000e+01,   1.20229000e+03],
                [  4.30000000e+01,   1.19408000e+03],
                [  4.40000000e+01,   1.14360000e+03],
                [  4.50000000e+01,   1.12816000e+03],
                [  4.60000000e+01,   1.10848000e+03],
                [  4.70000000e+01,   1.06850000e+03],
                [  4.80000000e+01,   1.03970000e+03],
                [  4.90000000e+01,   1.02384000e+03],
                [  5.00000000e+01,   9.38960000e+02],
                [  5.10000000e+01,   9.49970000e+02],
                [  5.20000000e+01,   9.49740000e+02],
                [  5.30000000e+01,   9.29540000e+02],
                [  5.40000000e+01,   9.17320000e+02],
                [  5.50000000e+01,   8.92690000e+02],
                [  5.60000000e+01,   8.77590000e+02],
                [  5.70000000e+01,   8.34600000e+02],
                [  5.80000000e+01,   8.37110000e+02],
                [  5.90000000e+01,   8.14700000e+02],
                [  6.00000000e+01,   7.88040000e+02],
                [  6.10000000e+01,   7.78200000e+02],
                [  6.20000000e+01,   7.64290000e+02],
                [  6.30000000e+01,   7.51280000e+02],
                [  6.40000000e+01,   7.40250000e+02],
                [  6.50000000e+01,   7.10540000e+02],
                [  6.60000000e+01,   7.03560000e+02],
                [  6.70000000e+01,   6.95100000e+02],
                [  6.80000000e+01,   6.76900000e+02],
                [  6.90000000e+01,   6.61900000e+02],
                [  7.00000000e+01,   6.49640000e+02],
                [  7.10000000e+01,   9.64600000e+02],
                [  7.20000000e+01,   9.82060000e+02],
                [  7.30000000e+01,   9.54030000e+02],
                [  7.40000000e+01,   9.31810000e+02],
                [  7.50000000e+01,   9.23350000e+02],
                [  7.60000000e+01,   8.94620000e+02],
                [  7.70000000e+01,   8.76100000e+02],
                [  7.80000000e+01,   8.39340000e+02],
                [  7.90000000e+01,   8.41540000e+02],
                [  8.00000000e+01,   8.10200000e+02],
                [  8.10000000e+01,   8.02220000e+02],
                [  8.20000000e+01,   7.84440000e+02],
                [  8.30000000e+01,   7.72220000e+02],
                [  8.40000000e+01,   7.58600000e+02],
                [  8.50000000e+01,   7.43880000e+02],
                [  8.60000000e+01,   7.21760000e+02],
                [  8.70000000e+01,   7.14260000e+02],
                [  8.80000000e+01,   6.98690000e+02],
                [  8.90000000e+01,   6.82410000e+02],
                [  9.00000000e+01,   6.69610000e+02],
                [  9.10000000e+01,   6.57860000e+02],
                [  9.20000000e+01,   6.43480000e+02],
                [  9.30000000e+01,   6.23130000e+02],
                [  9.40000000e+01,   6.03890000e+02],
                [  9.50000000e+01,   5.82630000e+02],
                [  9.60000000e+01,   5.79580000e+02],
                [  9.70000000e+01,   5.71800000e+02],
                [  9.80000000e+01,   5.62300000e+02],
                [  9.90000000e+01,   5.51400000e+02],
                [  1.00000000e+02,   5.40520000e+02],
                [  1.01000000e+02,   5.34170000e+02],
                [  1.02000000e+02,   5.19740000e+02],
                [  1.03000000e+02,   5.11290000e+02],
                [  1.04000000e+02,   4.97280000e+02],
                [  1.05000000e+02,   4.92820000e+02],
                [  1.06000000e+02,   4.79410000e+02],
                [  1.07000000e+02,   4.79560000e+02],
                [  1.08000000e+02,   4.69010000e+02],
                [  1.09000000e+02,   4.61600000e+02],
                [  1.10000000e+02,   4.51000000e+02],
                [  1.11000000e+02,   4.44060000e+02],
                [  1.12000000e+02,   4.35250000e+02],
                [  1.13000000e+02,   4.29290000e+02],
                [  1.14000000e+02,   4.15690000e+02],
                [  1.15000000e+02,   4.12870000e+02],
                [  1.16000000e+02,   4.05400000e+02],
                [  1.17000000e+02,   3.96940000e+02],
                [  1.18000000e+02,   3.91940000e+02],
                [  1.19000000e+02,   3.86790000e+02],
                [  1.20000000e+02,   3.80650000e+02],
                [  1.21000000e+02,   3.70960000e+02],
                [  1.22000000e+02,   3.65570000e+02],
                [  1.23000000e+02,   3.58420000e+02],
                [  1.24000000e+02,   3.55180000e+02],
                [  1.25000000e+02,   3.49040000e+02],
                [  1.26000000e+02,   3.42100000e+02],
                [  1.27000000e+02,   3.36000000e+02],
                [  1.28000000e+02,   3.25940000e+02],
                [  1.29000000e+02,   3.25710000e+02],
                [  1.30000000e+02,   3.18270000e+02],
                [  1.31000000e+02,   3.12120000e+02],
                [  1.32000000e+02,   3.08080000e+02],
                [  1.33000000e+02,   3.00520000e+02],
                [  1.34000000e+02,   2.92270000e+02],
                [  1.35000000e+02,   2.93280000e+02],
                [  1.36000000e+02,   2.82140000e+02],
                [  1.37000000e+02,   2.85600000e+02],
                [  1.38000000e+02,   2.80410000e+02],
                [  1.39000000e+02,   2.75870000e+02],
                [  1.40000000e+02,   2.71970000e+02],
                [  1.41000000e+02,   2.65730000e+02],
                [  1.42000000e+02,   2.60200000e+02],
                [  1.43000000e+02,   2.51620000e+02],
                [  1.44000000e+02,   2.44110000e+02],
                [  1.45000000e+02,   2.47830000e+02],
                [  1.46000000e+02,   2.42850000e+02],
                [  1.47000000e+02,   2.38150000e+02],
                [  1.48000000e+02,   2.39290000e+02],
                [  1.49000000e+02,   2.27380000e+02],
                [  1.50000000e+02,   2.26690000e+02],
                [  1.51000000e+02,   2.25480000e+02],
                [  1.52000000e+02,   2.18690000e+02],
                [  1.53000000e+02,   2.09070000e+02],
                [  1.54000000e+02,   2.10620000e+02],
                [  1.55000000e+02,   2.06980000e+02],
                [  1.56000000e+02,   2.01590000e+02],
                [  1.57000000e+02,   1.98090000e+02],
                [  1.58000000e+02,   1.91770000e+02],
                [  1.59000000e+02,   1.84020000e+02],
                [  1.60000000e+02,   1.84910000e+02],
                [  1.61000000e+02,   1.82750000e+02],
                [  1.62000000e+02,   1.80090000e+02],
                [  1.63000000e+02,   1.75180000e+02],
                [  1.64000000e+02,   1.73000000e+02],
                [  1.65000000e+02,   1.68870000e+02],
                [  1.66000000e+02,   1.65190000e+02],
                [  1.67000000e+02,   1.56300000e+02],
                [  1.68000000e+02,   1.59010000e+02],
                [  1.69000000e+02,   1.55220000e+02],
                [  1.70000000e+02,   1.52620000e+02],
                [  1.71000000e+02,   1.49140000e+02],
                [  1.72000000e+02,   1.41630000e+02],
                [  1.73000000e+02,   1.39430000e+02],
                [  1.74000000e+02,   1.39220000e+02],
                [  1.75000000e+02,   1.37970000e+02],
                [  1.76000000e+02,   1.36730000e+02],
                [  1.77000000e+02,   1.33960000e+02],
                [  1.78000000e+02,   1.30290000e+02],
                [  1.79000000e+02,   1.24500000e+02],
                [  1.80000000e+02,   1.24750000e+02],
                [  1.81000000e+02,   1.23920000e+02],
                [  1.82000000e+02,   1.21950000e+02],
                [  1.83000000e+02,   1.18960000e+02],
                [  1.84000000e+02,   1.17780000e+02],
                [  1.85000000e+02,   1.15560000e+02],
                [  1.86000000e+02,   1.14520000e+02],
                [  1.87000000e+02,   1.11650000e+02],
                [  1.88000000e+02,   1.09210000e+02],
                [  1.89000000e+02,   1.07690000e+02],
                [  1.90000000e+02,   1.06130000e+02],
                [  1.91000000e+02,   1.03700000e+02],
                [  1.92000000e+02,   1.02420000e+02],
                [  1.93000000e+02,   1.00420000e+02],
                [  1.94000000e+02,   9.82700000e+01],
                [  1.95000000e+02,   9.73700000e+01],
                [  1.96000000e+02,   9.54400000e+01],
                [  1.97000000e+02,   9.35500000e+01],
                [  1.98000000e+02,   9.23500000e+01],
                [  1.99000000e+02,   9.09300000e+01],
                [  2.00000000e+02,   8.93700000e+01],
                [  2.01000000e+02,   8.46400000e+01],
                [  2.02000000e+02,   8.54700000e+01],
                [  2.03000000e+02,   8.44900000e+01],
                [  2.04000000e+02,   8.34300000e+01],
                [  2.05000000e+02,   8.16200000e+01],
                [  2.06000000e+02,   8.06700000e+01],
                [  2.07000000e+02,   7.93200000e+01],
                [  2.08000000e+02,   7.81100000e+01],
                [  2.09000000e+02,   7.66900000e+01],
                [  2.10000000e+02,   7.53500000e+01],
                [  2.11000000e+02,   7.41500000e+01],
                [  2.12000000e+02,   7.32500000e+01],
                [  2.13000000e+02,   7.16700000e+01],
                [  2.14000000e+02,   7.01300000e+01],
                [  2.15000000e+02,   6.95200000e+01],
                [  2.16000000e+02,   6.82800000e+01],
                [  2.17000000e+02,   6.63900000e+01],
                [  2.18000000e+02,   6.57600000e+01],
                [  2.19000000e+02,   6.52300000e+01],
                [  2.20000000e+02,   6.30900000e+01],
                [  2.21000000e+02,   6.29000000e+01],
                [  2.22000000e+02,   6.16800000e+01],
                [  2.23000000e+02,   6.00000000e+01],
                [  2.24000000e+02,   5.99400000e+01],
                [  2.25000000e+02,   5.91800000e+01],
                [  2.26000000e+02,   5.73800000e+01],
                [  2.27000000e+02,   5.71000000e+01],
                [  2.28000000e+02,   5.62500000e+01],
                [  2.29000000e+02,   5.50900000e+01],
                [  2.30000000e+02,   5.40200000e+01],
                [  2.31000000e+02,   5.37500000e+01],
                [  2.32000000e+02,   5.27800000e+01],
                [  2.33000000e+02,   5.16000000e+01],
                [  2.34000000e+02,   5.14400000e+01],
                [  2.35000000e+02,   0.00000000e+00],
                [  2.36000000e+02,   0.00000000e+00],
                [  2.37000000e+02,   0.00000000e+00],
                [  2.38000000e+02,   0.00000000e+00],
                [  2.39000000e+02,   0.00000000e+00],
                [  2.40000000e+02,   0.00000000e+00],
                [  2.41000000e+02,   0.00000000e+00],
                [  2.42000000e+02,   0.00000000e+00]])

        for i in self.bands:
            #ind = np.nonzero(Esun_hyp==int(i[1:]))[0][0]
            if i < 70: scale = 40     #additional scaling factor, depending on band #
            else: scale = 80
            value = self.fullTestSet[i]*1.0
            self.fullTestSet[i] = value/(Esun_hyp[i,1]*scale)
        pass

    def writecsv(self,filename):
        csv = self.fullTestSet
        #csv = fts.ReadAsArray()
        np.savetxt(filename+'.csv',csv,delimiter=',')
        pass
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Classify an ALI scene and output GeoTiff')
    parser.add_argument('imname',type=str,help='Scene ID of ALI scene.')
    parser.add_argument('outfile',type=str,help='Output tif file name.')    
    options = parser.parse_args()
    name = options.imname
    savepath = options.outfile
    path = '/glusterfs/users/bhuynh/cavsarps/'+str(name)+'_1T/'+str(name)
    f = test(path)
    f.setUpTest()
    f.writecsv(savepath)

    
