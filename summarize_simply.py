#!/usr/bin/env python
'''
summarize_simply.py

INPUTS (in parameter file):
-masterMask: path to mask
-mapsTxt: path to .txt file containing list of map/band combos to summarize [map, band, band_name]
-breakdown: list of values or range of values of which to count pixels [ie. '1-10, 10-20, 20-30' or '11,12,23,31,41,42,52']
-stats: list of statistics to include in summary CSV [ie. mean, max, median, mode, etc..]
-outputPath: path to output summary CSV
-nodata: no data value of map

OUTPUTS:
-a summary CSV file
-a meta data .txt file
'''
import numpy as np
import gdal, os, sys, collections
from gdalconst import *
import cPickle as pickle
from lthacks.lthacks import *
from lthacks.intersectMask import *
from scipy.stats import mode
import numpy.ma as ma

def getTxt(file):
	'''reads parameter file & extracts inputs'''
	txt = open(file, 'r')
	next(txt)

	for line in txt:
		if not line.startswith('#'):
			lineitems = line.split(':')
			print lineitems
			title = lineitems[0].strip(' \n')
			var = lineitems[1].strip(' \n')

			if title.lower() == 'mastermask':
				masterMask = var
			elif title.lower() == 'mapstxt':
				mapsTxt = var	
			elif title.lower() == 'nodata':
				nodata = int(var)			
			elif title.lower() == 'breakdown':
				breakdown = var.split(',')
				if '-' in breakdown[0]:
					breakdown_tmp = []
					for i in breakdown:
						min_and_max = i.split('-')
						if len(min_and_max) != 2:
							sys.exit('Invalid number of arguments in breakdown:', min_and_max)
						else:
							breakdown_tmp.append(min_and_max)
					breakdown = breakdown_tmp
			elif title.lower() == 'stats':
				stats = [i.strip() for i in var.split(',')]
			elif title.lower() == 'options':
				options = [int(i) for i in var.split(',')]
			elif title.lower() == 'outputpath':
				outputPath = var
	txt.close()

	#assign empty list to breakdown if not defined in parameter file
	try:
		breakdown
	except NameError:
		breakdown = []
		
	try:
		options
	except NameError:
		options = []

	return masterMask, mapsTxt, nodata, breakdown, stats, options, outputPath

def loadMapList(mapsTxt):
	'''creates dictionary of map list from .txt file'''
	txt = open(mapsTxt, 'r')
	next(txt)

	mapDictList = []
	for line in txt:
		var = line.strip(' \n')
		var = var.split(',')
		if os.path.exists(var[0]):
			mapDictList.append({'path': var[0], 'band': int(var[1]), 'band_name': var[2].strip()})
		else:
			print "\nCannot find map:", var[0], "Excluding from summarization."
	txt.close()
	return mapDictList

def statFunct(astring, options=None):
	'''Returns a statistical function from a "stat string". '''

	if astring.strip(' ').lower() == 'mean':
		def func(anarray):
			return np.mean(anarray)
	elif astring.strip(' ').lower() == 'max':
		def func(anarray):
			return np.max(anarray)
	elif astring.strip(' ').lower() == 'median':
		def func(anarray):
			return np.median(anarray)
	elif astring.strip(' ').lower() == 'mode':
		def func(anarray):
			return mode(mode(anarray)[0][0])
	elif astring.strip(' ').lower() == 'min':
		def func(anarray):
			return np.min(anarray)
	elif astring.strip(' ').lower() == "num_pix_with_data":
		def func(anarray):
			return (anarray != options).sum()
	elif astring.strip(' ').lower() == "num_pix_equal":
		def func(anarray):
			return (anarray == options).sum()
	elif astring.strip(' ').lower() == "num_pix_between":
		def func(anarray):
			inds = np.where(np.logical_and(anarray>=options[0], anarray<options[1]))
			return len(inds[0])
			#return ((anarray >= options[0]) and (anarray <= options[1])).sum()
	elif astring.strip(' ').lower() == "stdev":
		def func(anarray):
			#mean = np.mean(anarray)
			#mean_array = np.zeros(anarray.shape)
			#mean_array[:] = mean
			#return np.mean(np.square(anarray - mean_array))
			return np.std(anarray)
	else:
		menu = "mean, max, median, mode, min, stdev, \
		        num_pix_with_data, num_pix_equal, num_pix_between"
		print sys.exit("Stat input not understood: "+ astring + "\nMenu: " + menu)
	
	return func 


def main(params):

	#load inputs from parameter file
	masterMask, mapsTxt, nodata, breakdown, stats, opts, outputPath = getTxt(params)

	#load lookup table & make a ordered dictionary for looping
# 	with open(lookupTable_pickle, 'rb') as handle:
# 		lookupTable = pickle.load(handle)
# 	lookupTable = collections.OrderedDict(lookupTable)
# 	print "\nLookup Table loaded."

	#create dictionary of map list from txt file
	mapDictList = loadMapList(mapsTxt)
	print mapDictList
	if len(mapDictList) > 0:
		print "\nSummarizing maps loaded."
	else:
		sys.exit("No summarizing maps found.")

	#define all statistics to be calculated
	print "\nDefining all statistics to calculate..."
	all_stats = []
	#if breakdown is specified, include # pixels equal to categories specified or between ranges specified
	for i in breakdown:
		if isinstance(i, list):
			all_stats.append({'header': i[0].upper()+"_"+i[1].upper(), 'func': statFunct('num_pix_between', options=[int(j) for j in i])})
			print " - num_pix_between ", i 
		else:
			all_stats.append({'header': i.upper(), 'func': statFunct('num_pix_equal', options=int(i))})
			print " - num_pix_equal ", i
	#also include statistics specified by user
	for ind,i in enumerate(stats):
		if i.lower() == "num_pix_with_data":
			all_stats.append({'header': i.upper(), 'func': statFunct(i, options=nodata)})
			print " - ", i
		elif i.lower() == "num_pix_equal":
			all_stats.append({'header': i.upper()+"_"+str(opts[ind]), 'func': statFunct(i, options=opts[ind])})
			print " - ", i, opts[ind]
		else:
			all_stats.append({'header': i.upper(), 'func': statFunct(i)})
			print " - ", i
	
	#define all masks:
	msk = gdal.Open(masterMask, GA_ReadOnly)
	mskBand = msk.GetRasterBand(1)
	mskBandArray = mskBand.ReadAsArray()
	mskValues = np.unique(mskBandArray)
	zeroInd = np.where(mskValues == 0)
	print mskValues
	mskValues = np.delete(mskValues, zeroInd)
	
	print mskValues
	
	del msk
	del mskBand
	del mskBandArray
	
		
	#loop thru stats & masks & populate summary table
	headers = ["BAND_NAME", os.path.basename(masterMask).upper()] + [i['header'].upper() for i in all_stats]
	dtypes = [(i,'a32') for i in headers]
	summarizeData = np.zeros(len(mskValues)*len(mapDictList), dtype=dtypes)
	
	row = 0
	for val in mskValues:
	
		print val
	
		for srcMap in mapDictList:
		
			print "\nWorking on Row #" + str(row) + " ..."
			
			srcPath = srcMap['path']
			srcBand = srcMap['band']
			mskPath = masterMask
			
			o_array, o_transform, o_projection, o_driver, o_nodata, o_datatype = maskAsArray(srcPath, mskPath, src_band=srcBand, msk_value=val)
			
			summarizeData[row]['BAND_NAME'] = srcMap['band_name']
			summarizeData[row][os.path.basename(masterMask).upper()] = val 
			
			
			for stat in all_stats:
				
				summarizeData[row][stat['header'].upper()] = stat['func'](o_array[o_array!=nodata])
				
			arrayToCsv(summarizeData, outputPath) #save as it loops
			
			row += 1
			
	#final save
	arrayToCsv(summarizeData, outputPath)
	print " Done!"

# 	find least common boundaries b/t mask & source maps only once, ASSUMING all source rasters are the same extent
# 	finalSize, finalTransform, projection, driver = findLeastCommonBoundaries([mapDictList[0]['path'],masterMask])
# 	cols = int(finalSize[0])
# 	rows = int(finalSize[1])
# 	(midx, midy) = transformToCenter(finalTransform, cols, rows)
# 	extract mask array once 
# 	print "\nReading Master Mask..."
# 	ds_mask = gdal.Open(masterMask, GA_ReadOnly)
# 	mskTransform = ds_mask.GetGeoTransform()
# 	mskBandArray = extract_kernel(ds_mask, midx, midy, cols, rows, 1, mskTransform)
# 
# 	define new structured array or read in existing CSV it already exists
# 	if os.path.exists(outputPath):
# 		print "\n!! Output Path already exists. Starting summary calcs from leave-off point..."
# 		summarizeData = csvToArray(outputPath)
# 		continuing = True
# 	else:
# 		headers = ["BAND_NAME", os.path.basename(masterMask).upper()] + [i.upper() for i in lookupTable[0].keys()] + [i.upper() for  i in breakdown] + [i.upper() for i in stats]
# 		dtypes = [(i,'a32') for i in headers]
# 		summarizeData = np.zeros(len(lookupTable)*len(mapDictList), dtype=dtypes)
# 		continuing = False
# 
# 	find starting row
# 	if continuing:
# 		emptyCells = np.where(summarizeData["BAND_NAME"] == -1)
# 		row = np.min(emptyCells) - 1 #starting point
# 
# 		find source map to start with & alter mapDictList to exclude maps already calculated
# 		year_left_off = summarizeData[row]["BAND_NAME"]
# 		for ind,i in enumerate(mapDictList):
# 			if str(i['band_name']).strip(' ')==str(year_left_off).strip(' '): 
# 				map_list_start = ind
# 				break
# 		mapDictList = mapDictList[map_list_start:]
# 
# 		find mask value to start with & re-order lookupTable dictionary to reflect starting point
# 		try:
# 			maskval_left_off = summarizeData[row][os.path.basename(masterMask).upper()]
# 		except IndexError:
# 			sometimes when converting CSV data into numpy array, header will exclude "."
# 			maskval_left_off = summarizeData[row][os.path.basename(masterMask).upper().replace('.','')]
# 		newLookup = collections.OrderedDict({})
# 		startNew = False
# 		for k,v in lookupTable.iteritems():
# 			if k == maskval_left_off:
# 				startNew = True
# 			if startNew:
# 				newLookup[k] = v
# 		fill in rest from beginning
# 		for k,v in lookupTable.iteritems():
# 			if k == maskval_left_off:
# 				break
# 			newLookup[k] = v
# 		lookupTable = newLookup
# 	
# 		print "\nStarting calculations at ROW", row, ", BAND_NAME", year_left_off, ", MASK VALUE", mask_start_val
# 
# 	else:
# 		print "\nStarting calculations."
# 		row = 0
# 
# 
# 	loop thru map/band combos
# 	for imap_ind,imap in enumerate(mapDictList):
# 		print "\nREADING MAP: " + os.path.basename(imap['path']) + " ....."	
# 
# 		extract source array
# 		ds_source = gdal.Open(imap['path'], GA_ReadOnly)
# 		srcTransform = ds_source.GetGeoTransform()
# 		srcBandArray = extract_kernel(ds_source, midx, midy, cols, rows, imap['band'], srcTransform)
# 
# 		for maskval in lookupTable:
# 			print "\nMASKING WITH VALUE: " + str(maskval) + " ..."
# 
# 			fill in year & map mask value fields
# 			summarizeData[row]['YEAR'] = imap['band_name']
# 			for i in lookupTable[0].keys(): 
# 				try:
# 					summarizeData[row][i.upper()] = lookupTable[maskval][i]
# 				except IndexError:
# 					when continuing from existing CSV, the mask header may exclude the "." in file name
# 					summarizeData[row][i.upper().replace('.','')] = lookupTable[maskval][i]  
# 
# 			mask out source array where mask array is equal to "msk_value"
# 			maskedArray = ma.masked_where(mskBandArray != maskval, srcBandArray)
# 
# 			calculate all stats & populate table
# 			for stat in all_stats:
# 				print "Calculating " + stat['header'] + " .."
# 				summarizeData[row][stat['header']] = stat['func'](maskedArray)
# 
# 			arrayToCsv(summarizeData, outputPath) #save as it loops
# 			row += 1 #increment
	
	#final save summarize data
	#arrayToCsv(summarizeData, outputPath)
	#print " Done!"

if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1]))