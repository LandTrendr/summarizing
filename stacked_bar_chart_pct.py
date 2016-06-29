
from validation_funs import *
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
# %matplotlib inline
# plt.use('Agg')

#PDF, EPS

def main(inputPath, outputPath):
    ####CREATE DATAFRAME#####
    raw_data = csvToArray(inputPath)

    ####PLOT########
    # Create a figure with a single subplot
    f, ax = plt.subplots(1, figsize=(10,5))

    # Set bar width at 1
    bar_width = 1

    # positions of the left bar-boundaries
    bar_l = [i for i in range(len(raw_data['11']))]

    # positions of the x-axis ticks (center of the bars as bar labels)
    tick_pos = [i+(bar_width/2) for i in bar_l]

    # define landcover type dictionary
    landcover_dict = [{'catnum': '11', 'catname': 'Water', 'color': "#92bef4"},
                      {'catnum': '12', 'catname': "Perennial Ice/Snow", 'color': "#ececec"},
                      {'catnum': '31', 'catname': "Barren", 'color': "#957700"},
                      {'catnum': '41', 'catname': "Deciduous", 'color': "#81bf5f"},
                      {'catnum': '42', 'catname': "Evergreen", 'color': "#0b8154"},
                      {'catnum': '52', 'catname': "Shrub/Grassland/Herbaceous", 'color': "#dcba8a"},
                      {'catnum': '23', 'catname': "Developed", 'color': "#9b6bd1"}]

    # Calc the percentage of the total pixels of each year for each landcover cat
    # total_pixels = float(raw_data['23'][-1]) #count total pixels in 2012 urban mask
    total_pixels = float(raw_data['23'][0]) #count total pixels in 1991 urban mask
    for ind,i in enumerate(landcover_dict):
        landcover_dict[ind]['pct_pixels_per_year'] = [float(j)/total_pixels*100 for j in raw_data[i['catnum']]]

    totals = []
    for j in range(len(raw_data['11'])):
        t = 0
        for i in landcover_dict:
            t += i['pct_pixels_per_year'][j]
        totals.append(t)

    # Set the ticks to be first names
    plt.xticks(tick_pos, raw_data['YEAR'])
    ax.set_ylabel("Percentage of Pixels (%)")
    ax.set_xlabel("")
    ax.set_title("Progression from Urban 1991 Pixels")

    # Let the borders of the graphic
    plt.xlim([min(tick_pos)-bar_width, max(tick_pos)+bar_width])
    plt.ylim(-2, 35)

    # rotate axis labels
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

    #create legend
    patches = []
    for i in landcover_dict:
        patches.append(mpatches.Patch(color=i['color'], label=i['catname']))
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.63, box.height])
    ax.legend(handles=patches, loc='center left', bbox_to_anchor=(1, 0.5))

    bottoms = np.zeros(len(landcover_dict[0]['pct_pixels_per_year']))
    for ind,i in enumerate(landcover_dict):
            if ind != 0:
                bottoms = bottoms + np.array(landcover_dict[ind-1]['pct_pixels_per_year'])
            ax.bar(bar_l, i['pct_pixels_per_year'], bottom=bottoms, label=i['catname'], color=i['color'], width=bar_width, edgecolor='white')
        
    # show & save plot
    # plt.show()
    plt.savefig(outputPath)

if __name__ == '__main__':
    args = sys.argv
    sys.exit(main(args[1], args[2]))