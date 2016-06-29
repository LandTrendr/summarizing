'''makeSimpleKey.py'''
import sys, os
import cPickle as pickle

def main(mapname, outPath):
	map_key = {0: {mapname: 0}, 1: {mapname: 1}}

	with open(outPath, 'wb') as handle:
		pickle.dump(map_key, handle)

	if os.path.exists(outPath):
		print "\nNew data structure pickled: ", outPath


if __name__ == '__main__':
	args = sys.argv
	sys.exit(main(args[1],args[2]))