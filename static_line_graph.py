from lthacks.lthacks import *
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

def main(inputPath, outputPath):
    ####CREATE DATAFRAME#####
    raw_data = csvToArray(inputPath)

    ####PLOT########
    # Create a figure with a single subplot
    f, ax = plt.subplots(1, figsize=(10,5))

    # Set bar width at 1
    bar_width = 1

    # positions of the left bar-boundaries
    bar_l = [i for i in range(np.unique(raw_data['BAND_NAME']).size)]

    # positions of the x-axis ticks (center of the bars as bar labels)
    tick_pos = [i+(bar_width/2) for i in bar_l]

    # define landcover type dictionary
    graph_dict = [{'catnum': '1', 'catname': 'Segehen', 'color': "#92bef4", 'axes': (0,0)},
                      {'catnum': '2', 'catname': "Last Chance", 'color': "#3F5D7D", 'axes': (0,1)},
                      {'catnum': '3', 'catname': "Kings River", 'color': "#957700", 'axes': (1,0)},
                      {'catnum': '25', 'catname': "Srewauger Canyon", 'color': "#0b8154", 'axes': (1,1)}]

    # Calc the percentage of the total pixels of each year for each landcover cat
    # total_pixels = float(raw_data['23'][-1]) #count total pixels in 2012 urban mask
    #starting_num_pixels = [float(raw_data[i['catnum']][0]) for i in graph_dict] #total num of pixels in 1991 for each cat
    for ind,i in enumerate(graph_dict):
    	#csvInd = np.where(raw_data['CA_SDA.BSQ'] == i['catnum'])
    	graph_dict[ind]['mean_mg'] = [float(m)/10. for m in raw_data['MEAN'][raw_data['CA_SDABSQ'] == float(i['catnum'])]]
    	graph_dict[ind]['stdev_mg'] = [float(m)/10. for m in raw_data['STDEV'][raw_data['CA_SDABSQ'] == float(i['catnum'])]]
    	#graph_dict[ind]['mean_mg'] = np.array(raw_data['MEAN'][raw_data['CA_SDABSQ'] == float(i['catnum'])])/10.
    	#graph_dict[ind]['stdev_mg'] = np.array(raw_data['STDEV'][raw_data['CA_SDABSQ'] == float(i['catnum'])])/10.
    	if ind == 0:
    		ymin = min(graph_dict[ind]['mean_mg'])
    		ymax = max(graph_dict[ind]['mean_mg'])
    	else:
    		ymin = min([ymin] + graph_dict[ind]['mean_mg'])
    		ymax = max([ymax] + graph_dict[ind]['mean_mg'])	
        #graph_dict[ind]['mean_mg'] = raw_data[i['catnum']].astype('float')/starting_num_pixels[ind]*100
        
        
    # row and column sharing
	#f, axarr = plt.subplots(2, 2, sharex='col', sharey='row')

    # Set the ticks to be first names d
    plt.xticks(tick_pos, raw_data['BAND_NAME'])
    ax.set_ylabel("MEAN BIOMASS (Mg/Ha)")
    ax.set_xlabel("")
    ax.set_title("CRM Biomass")

    # Let the borders of the graphic
    plt.xlim([min(tick_pos)-bar_width, max(tick_pos)+bar_width])
    # highest_pct = 100.
    # lowest_pct = 100.
    # for i in landcover_dict:
    #     highest_pct = max(list(i['rel_pixels_per_year']) + [highest_pct])
    #     print list(i['rel_pixels_per_year']) + [highest_pct]
    #     lowest_pct = min(list(i['rel_pixels_per_year']) + [lowest_pct])
    #     print list(i['rel_pixels_per_year']) + [lowest_pct]
    #     print highest_pct, lowest_pct
    # plt.ylim(95., 145.) #OREGON PADUS2 
#     plt.ylim(90., 120.) #ZOOM LAYERS
    plt.ylim(ymin - 25., ymax + 25.) 
	
    # rotate axis labels
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

    #create legend
    patches = []
    for i in graph_dict:
        patches.append(mpatches.Patch(color=i['color'], label=i['catname']))
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.63, box.height])
    ax.legend(handles=patches, loc='center left', bbox_to_anchor=(1, 0.5))

	
    for ind,i in enumerate(graph_dict):
    	#axarr[i['axes'][0],i['axes'][1]].xticks(tick_pos, raw_data['BAND_NAME'])
#     	axarr[i['axes'][0],i['axes'][1]].set_ylabel("MEAN BIOMASS (Mg/Ha)")
#     	axarr[i['axes'][0],i['axes'][1]].set_title(i['catname'])
#     	stdev_min = list(np.array(i['mean_mg']) - np.array(i['stdev_mg']))
#     	stdev_max = list(np.array(i['mean_mg']) + np.array(i['stdev_mg']))
    	#axarr[i['axes'][0],i['axes'][1]].fill_between(bar_l, stdev_min, stdev_max, color="grey")  
        plt.plot(bar_l, list(i['mean_mg']), color=i['color'], linewidth=2.0)

    # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
#     plt.ylim(ymin - 25., ymax + 25.) 
#     plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
#     plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)

    # show & save plot
    #plt.show()
    plt.savefig(outputPath)

if __name__ == '__main__':
    args = sys.argv
    sys.exit(main(args[1], args[2]))
