'''
summarizeKernels.py

Adds additional columns to a CSV by extracting kernels from maps 
and performing summary stats on those kernels.

Inputs:
	1) input CSV, contains X,Y coordinates
	2) key CSV, contains 1 row per additional column, fields include:
		- HEADER (column header name)
		- STAT (statistic to perform on kernel)
		- STATOPTS (options for statistics, separated by semicolons - OPTIONAL)
		- XFIELD (column header name of x-field in input CSV)
		- YFIELD (column header name of y-field in input CSV)
		- MAP (path to map from which to extract kernel)
		- MAPFIELD (column header name of map from which to extract kernel in input CSV)
			*either MAPPATH or MAPFIELD can be filled out, other will be blank
		- BAND (band number from which to extract kernel)
		- BANDFIELD (column header name of band number from which to extract kernel in input CSV)
			*either BAND or BANDFIELD can be filled out, other will be blank
		- KERNELSHAPE (shape of kernel to extract)
			- menu: rectangle, circle, triangle, pieslice
		- KERNELDEFS (definitions for specific kernel shape, separated by semicolons)
			*these will vary based on KERNELSHAPE:
				- rectangle: width;height
				- circle: diameter
				- triangle: width;height;quadrant
				- pieslice: diameter;startangle;endangle;arc_negative_bool
				
Output:
	1) a CSV that contains data from input CSV with additional columns added
	
Usage:
	python summarizeKernels.py {path_to_inputdata_csv} {path_to_key_csv} {output_path} [{metadata_description}]
	
Author: Tara Larrue (tlarrue2991@gmail.com)
'''

from lthacks.lthacks import *
import lthacks.kernelshapes as ks
from numpy.lib.recfunctions import append_fields
import os, sys, gdal
from gdalconst import *

def main(inputDataPath, keyPath, outputPath, metaDesc=None):

	
	# extract input csv info
	inputData = csvToArray(inputDataPath)
	
	# extract additional columns key info
	additionalColumns = csvToArray(keyPath)
	
	#add dummy column if only 1 key item
	if additionalColumns.size == 1:
		oneColumn = True
		dummy = np.zeros(1, dtype=additionalColumns.dtype)
		additionalColumns = np.append(additionalColumns, dummy)
	else:
		oneColumn = False
	
	# initialize loop
	outputData = inputData
	
	# loop thru additional columns
	for iter,col in enumerate(additionalColumns):
	
		if oneColumn and (iter == 1):
			continue
			
		print "\nCalculating " + col['HEADER'].strip().upper() + " ...."
	
		# append field to data array
		print outputData
# 		if outputData.size == 1:
# 			numRows = len(np.atleast_1d(outputData))
# 		else:
# 			numRows = outputData.size
		outputData = append_fields(outputData, [col['HEADER'].strip().upper()], 
		                           data=[np.zeros(outputData.size)])
		
		# loop thru rows & calc stats for additional column
		for r,row in enumerate(inputData):
		
			#open map dataset & get transform info
			if col['MAPFIELD']:
				ds = gdal.Open(row[col['MAPFIELD'].strip().upper()], GA_ReadOnly)
			else:
				ds = gdal.Open(col['MAP'].strip(), GA_ReadOnly)
			transform = ds.GetGeoTransform()
				
			#define kernel
			shapedefs = [i.strip() for i in col['KERNELDEFS'].split(';')]
			shape = ks.defineShapeInstance(col['KERNELSHAPE'], shapedefs)
				
			#get band and coordinate info
			if col['BANDFIELD']:
				band = int(row[col['BANDFIELD'].strip().upper()])
			else:
				band = int(col['BAND'])

			x = float(row[col['XFIELD'].upper()])
			y = float(row[col['YFIELD'].upper()])
			
			#extract kernel pixels as array
			masked_kernel, kernel = shape.extract_kernel(ds, band, x, y, transform)
			
			if (masked_kernel is None) and (kernel is None):
				
				outputData[r][col['HEADER'].strip().upper()] = -9999 #out of range default
				print "\nWARNING: Row " + str(r) + " kernel is out of range of extraction map!" 
				
			else:
			
				#calc summary statistic
				if col['STATOPTS'] is not False: 
					try:
						options = [float(i.strip()) for i in col['STATOPTS'].split(';')]
					except AttributeError:
						options = [float(col['STATOPTS'])]

				else:
					options = None
				
				statFunc = getStatFunc(col['STAT'].strip().lower(), options)
			
				summary = statFunc(kernel)
			
				#add summary stat to output data array
				outputData[r][col['HEADER'].strip().upper()] = summary
				
		arrayToCsv(outputData, outputPath)
			
	arrayToCsv(outputData, outputPath)
	
	createMetadata(sys.argv, outputPath, description=metaDesc, 
	               lastCommit=getLastCommit(os.path.realpath('__file__')))
	
	
if __name__ == '__main__': 	
	args = sys.argv
		
	if (len(args) == 4):
		sys.exit(main(*args[1:]))
	
	elif (len(args) == 5):
		sys.exit(main(*args[1:4], metaDesc=args[4]))
		
	else:
		usage = "python summarizeKernels.py {path_to_inputdata_csv} \
		 {path_to_key_csv} {output_path} [{metadata_description}]"
		sys.exit("Invalid number of arguments. \nUsage: " + usage)
		
	
			
			
			
			
				
			
				
				
				
			
			
	
	
	