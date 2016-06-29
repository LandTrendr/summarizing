#!/usr/bin/env python
'''
Combine Masks Version 1.

Usage:
  combineMasks.py <maskstxt> <outputmask> <outputkey> [--meta=<m>]
  intersectMask.py -h | --help

Options:
  -h --help     	  Show this screen.
  --meta=<meta>  	  Additional notes for meta.txt file.
'''
import numpy as np
import gdal, sys, os, doctopt
from gdalconst import *
import cPickle as pickle
from lthacks.intersectMask import *

def readMaskList(file):
	txt = open(file, 'r')
	next(txt)

	listOfMasks = []
	for line in txt:
		var = line.strip(' \n')
		if os.path.exists(var):
			listOfMasks.append(var)
		else:
			print "\nCannot find mask:", var, "Excluding from combo."
	txt.close()

	return listOfMasks

def findGreatestCommonBoundaries(listOfMaps):
    '''Determine least common extent from a list of maps'''

    #extract corner coordinate info from all masks
    corners = np.zeros((len(listOfMaps), 4, 2))
    projections = []
    drivers = []
    pixelSizes = np.zeros((len(listOfMaps), 2))
    for ind,mask in enumerate(listOfMaps):
        src = gdal.Open(mask, GA_ReadOnly)
        projection = src.GetProjection()
        driver = src.GetDriver()
        transform = src.GetGeoTransform()
        cols = src.RasterXSize
        rows = src.RasterYSize
        corners[ind] = GetExtent(transform, cols, rows)
        projections.append(projection)
        drivers.append(driver)
        pixelSizes[ind] = (transform[1], transform[5])

    #define number of columns & rows for final mask
    upperLeftX = np.min(corners[:, 0, 0])
    upperLeftY = np.max(corners[:, 0, 1])
    lowerRightX = np.max(corners[:, 2, 0])
    lowerRightY = np.min(corners[:, 2, 1])
    pixSizeX = pixelSizes[np.argmin(np.abs(pixelSizes), axis=0)[0],0]
    pixSizeY = pixelSizes[np.argmin(np.abs(pixelSizes), axis=0)[1],1]
    numCols = abs((upperLeftX - lowerRightX)/abs(pixSizeX))
    numRows = abs((lowerRightY - upperLeftY)/abs(pixSizeY))
    finalSize = (numCols, numRows)

    #define transform for final mask
    finalTransform = (upperLeftX, pixSizeX, 0.0, upperLeftY, 0.0, pixSizeY)

    return corners, finalSize, finalTransform, projection, driver

def shrinkValues(an_array):
	uniqueValues = np.unique(an_array)
	uniqueValues = uniqueValues[uniqueValues != 0]
	rep = range(1, uniqueValues.size+1)
	key_dict = {}
	for ind,i in enumerate(uniqueValues):
		key_dict[rep[ind]] = int(i)
		print key_dict

	#convert array
	new_array = an_array
	for key, value in key_dict.iteritems():
		new_array[new_array==value] = int(key)

	return key_dict, new_array

def createMasterMask(listOfMasks, corners, finalSize, finalTransform, projection, driver, outPath):
	#save new raster
	out = driver.Create(outPath, int(finalSize[0]), int(finalSize[1]), 1, GDT_UInt32)
	if out is None:
		print sys.exit('\nCould not create ' + outPath)

	#calculate new mask values
	all_arrays = []
	all_keys = []
	maxValue = 0
	outBand = out.GetRasterBand(1)
	for ind,mask in enumerate(listOfMasks):
		print "\nReading Mask:", mask, " ..."
		src = gdal.Open(mask, GA_ReadOnly)
		srcBand = src.GetRasterBand(1)	
		srcBandArray = srcBand.ReadAsArray()
		nodata = srcBand.GetNoDataValue()
		if nodata is None:
			nodata = 0 #ASSUMPTION!
		if nodata != 0:
			srcBandArray[srcBandArray==nodata] = 0

		offsetX = int(corners[ind,0,0] - finalTransform[0])/30 #ASSUMPTION for final 
		offsetY = int(corners[ind,0,1] - finalTransform[3])/-30 
		cols = src.RasterXSize
		rows = src.RasterYSize
		srcBandArray_finalSize = np.zeros((finalSize[1], finalSize[0]))
		srcBandArray_finalSize[offsetY:offsetY+rows,offsetX:offsetX+cols] = srcBandArray

		key_dict, srcBandArray_finalValues = shrinkValues(srcBandArray_finalSize)
		all_arrays.append(srcBandArray_finalValues)
		all_keys.append(key_dict)
		maxValue = max(key_dict.keys() + [maxValue])

	print "\nCombining Masks..."	
	maxDigit = len(str(maxValue)) #each mask gets 'maxDigit' digits 
	total = np.zeros((finalSize[1], finalSize[0])).astype('int')
	for ind,i in enumerate(all_arrays):
		power = ind*maxDigit
		total += (i*(10**power))
	outBand.WriteArray(total)

	#flush data to disk
	outBand.FlushCache()
	#georeference the image and set the projection
	out.SetGeoTransform(finalTransform)
	out.SetProjection(projection)

	all_keys_pickle = os.path.join(os.path.dirname(outPath), 'all_keys.pickle')
	maxDigit_pickle = os.path.join(os.path.dirname(outPath), 'maxDigit.pickle')
	with open(all_keys_pickle, 'wb') as handle:
		pickle.dump(all_keys, handle)
	with open(maxDigit_pickle, 'wb') as handle:
		pickle.dump(maxDigit, handle)

	return all_keys, maxDigit, all_keys_pickle, maxDigit_pickle

def constructMasterKey(total, all_keys, listOfMasks, maxDigit):

	uniqueTotals = np.unique(total)
	masterKey = {}
	for ind,i in enumerate(uniqueTotals):
		masterKey[i] = {}
		for jind,j in enumerate(listOfMasks):
			nodata=False
			key_rep_for_mask = str(i)[::-1][maxDigit*jind:(maxDigit*jind)+maxDigit][::-1]
			try:
				key_rep_for_mask = int(key_rep_for_mask)
				if key_rep_for_mask == 0: nodata=True
			except ValueError:
				if key_rep_for_mask == '': 
					nodata=True
				else:
					sys.exit('unknown error')
			if nodata:
				masterKey[i][os.path.basename(j)] = 0
			else:
				masterKey[i][os.path.basename(j)] = all_keys[jind][key_rep_for_mask]
	return masterKey

def createMetadata(masksTxt, outputPath, picklePath, note):
  
    timeStamp = datetime.now().strftime('%Y%m%d %H:%M:%S')
    user = getpass.getuser()

    commandline = "combineMasks.py " + os.path.abspath(masksTxt) + " " + os.path.abspath(outputPath) + " " + os.path.abspath(picklePath) + " "

    outPath_meta = os.path.splitext(outPath)[0] + "_meta.txt"
    f = open(outPath_meta, "w")
    f.write("SCRIPT VERSION: v1 last updated 07/10/15")
    f.write("\nCOMMAND: " + commandline)
    f.write("\nTIME: " + timeStamp)
    f.write("\nUSER: " + user)
    if note:
        f.write("\nNOTES: " + note)
        f.close()


def main(masksTxt, outputPath, picklePath, note):

	listOfMasks = readMaskList(masksTxt)

	print "\nCalculating coordinate info for combo mask..."
	corners, finalSize, finalTransform, projection, driver = findGreatestCommonBoundaries(listOfMasks)

	print "\nCreating Master Mask..."
	if not os.path.exists(outputPath):
		all_keys, maxDigit, all_keys_pickle, maxDigit_pickle = createMasterMask(listOfMasks, corners, finalSize, finalTransform, projection, driver, outputPath)
		if os.path.exists(outputPath):
			print " Master Mask created: ", outputPath
	else:
		all_keys_pickle = os.path.join(os.path.dirname(outputPath), 'all_keys.pickle')
		maxDigit_pickle = os.path.join(os.path.dirname(outputPath), 'maxDigit.pickle')
		with open(all_keys_pickle, 'rb') as handle:
			all_keys = pickle.load(handle)
		with open(maxDigit_pickle, 'rb') as handle:
			maxDigit = pickle.load(handle)

	print "\nConstructing Master Key..."
	ds = gdal.Open(outputPath, GA_ReadOnly)
	dsBand = ds.GetRasterBand(1)	
	total = dsBand.ReadAsArray()
	masterKey = constructMasterKey(total, all_keys, listOfMasks, maxDigit)

	with open(picklePath, 'wb') as handle:
		pickle.dump(masterKey, handle)

	if os.path.exists(picklePath):
		createMetadata(masksTxt, outputPath, picklePath, note)
		print " Done! Key saved: ", picklePath
		os.remove(all_keys_pickle)
		os.remove(maxDigit_pickle)


if __name__ == '__main__':
	if __name__ == '__main__':

    try:
        #parse arguments, use file docstring as parameter definition
        args = docopt.docopt(__doc__)

        #call main function
        main(args['<maskstxt>'], args['<outputmask>'], args['<outputkey>'], args['--meta'])

    #handle invalid options
    except docopt.DocoptExit as e:
        print e.message
