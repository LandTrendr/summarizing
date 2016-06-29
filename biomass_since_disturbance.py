'''
biomass_since_disturbance.py
skeleton script

Creates a CSV with mean biomass per patch per year since disturbance year. 

Inputs:
- map of disturbance (band 1 is year of disturbance)
- map of patch ids
- directory containing biomass maps 
	*make sure there are no other maps in here but the maps you want to use & the year 
	is somewhere in the file name of each map
- relative start year (relative to year of disturbance, ex. "-3")
- relative end year (relative to year of disturbance, ex. "10")
- output csv path

Output:
- csv with 1 row per unique patch id in map of patch ids
 & columns containing biomass data relative to year of disturbance

Usage:
python biomass_since_disturbance.py {disturbance_mappath} {patchid_mappath} {dir_of_biomassmaps} {start_relative_year} {end_relative_year} {output_csv_path}

'''

import os, gdal
import numpy as np
from gdalconst import *
from lthacks.lthacks import *

YEARS = range(1990,2013)

def main(disturbanceMosaic, patchMosaic, biomassDir, startRelYear, endRelYear, outputCsv):

	#extract biomass data
	biomassData = {}
	for y in YEARS:
		file = os.path.join(biomassDir, "*{0}*.bsq".format(str(y)))
		ds = gdal.Open(file, GA_ReadOnly)
		band = ds.GetRasterBand(1)
		biomassData[y] = band.ReadAsArray()
		del ds, band
		
	#get unique patch ids
	ds = gdal.Open(patchMosaic, GA_ReadOnly)
	band = ds.GetRasterBand(1)
	idData = band.ReadAsArray()
	ids = np.unique(patchData)
	del ds, band
	
	#extract year of disturbance data
	ds = gdal.Open(disturbanceMosaic, GA_ReadOnly)
	band = ds.GetRasterBand(1) #YOD band
	yearData = band.ReadAsArray()

	#define structured array to save CSV data
	headers = ['PATCH_ID'] +  ['BIOMASS_{0}YEARS'.format(str(i)) for i in range(startRelYear, endRelYear+1)]
	dtypes = [(i,'a32') for i in headers]
	csvdata = np.zeros(id.size - 1, dtype=dtypes)
	
	csvdata['PATCH_ID'] = ids
	
	#loop thru patch ids & array headers (which correspond to years since disturbance)
	for ind,i in enumerate(ids):
	
		#find year of disturbance of current patch
		patchPixels = np.where(idData == i)
		disturbanceYear = yearData[patchPixels][0,0] #pick any pixel in patch, they should all have the same year
		yearSince = 0
		
		for col in headers[1:]:
		
			#extract mean biomass from the patch
			try:
				csvdata[ind][col] = np.mean(biomassData[disturbanceYear + yearSince][patchPixels]) #or median?
			except IndexError:
				print "WARNING: Cannot find year '{0}' in biomass data".format(str(disturbanceYear+yearSince))
				
			yearSince += 1
			
	#save structured array as CSV
	arrayToCsv(csvdata, outputCsv) 
	
	
if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1], args[2], args[3], int(args[4]), int(args[5]), args[6]))
			
			
			
			
			
			
	
	
		
		