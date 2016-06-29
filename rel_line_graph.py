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
    bar_l = [i for i in range(len(raw_data['0_100']))]

    # positions of the x-axis ticks (center of the bars as bar labels)
    tick_pos = [i+(bar_width/2) for i in bar_l]

    # define landcover type dictionary
    landcover_dict = [{'catnum': '1', 'catname': 'Segehen', 'color': "#92bef4"},
                      {'catnum': '2', 'catname': "Last Chance", 'color': "grey"},
                      {'catnum': '3', 'catname': "Kings River", 'color': "#957700"},
                      {'catnum': '4', 'catname': "PLAS", 'color': "#81bf5f"},
                      {'catnum': '25', 'catname': "Srewauger Canyon", 'color': "#0b8154"}]

    # Calc the percentage of the total pixels of each year for each landcover cat
    # total_pixels = float(raw_data['23'][-1]) #count total pixels in 2012 urban mask
    starting_num_pixels = [float(raw_data[i['catnum']][0]) for i in landcover_dict] #total num of pixels in 1991 for each cat
    for ind,i in enumerate(landcover_dict):
        landcover_dict[ind]['rel_pixels_per_year'] = raw_data[i['catnum']].astype('float')/starting_num_pixels[ind]*100

    # Set the ticks to be first names
    plt.xticks(tick_pos, raw_data['YEAR'])
    ax.set_ylabel("# of Pixels relative to 1991 (%)")
    ax.set_xlabel("")
    ax.set_title("Relative Change of California PADUS4 Landcover Classes")

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
    plt.ylim(90., 120.) #ZOOM LAYERS

    # rotate axis labels
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

        #create legend
    patches = []
    for i in landcover_dict:
        patches.append(mpatches.Patch(color=i['color'], label=i['catname']))
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.63, box.height])
    ax.legend(handles=patches, loc='center left', bbox_to_anchor=(1, 0.5))

    for ind,i in enumerate(landcover_dict):
        plt.plot(bar_l, list(i['rel_pixels_per_year']), color=i['color'], linewidth=2.0)

        
    # show & save plot
    # plt.show()
    plt.savefig(outputPath)

if __name__ == '__main__':
    args = sys.argv
    sys.exit(main(args[1], args[2]))

