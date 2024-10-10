import matplotlib.pyplot as plt
import squarify
import math
from matplotlib.gridspec import GridSpec
import json
import numpy as np


def main():
    with open('current_counts.txt', 'r') as file:
        counts = json.load(file)
    del counts["Sirayat"]
    total = sum(counts.values())
    
    # Sample data
    labels = [key+"\n"+str(counts[key]) for key in counts]
    sizes = [int(label.split("\n")[-1]) for label in labels]
    sizes = [math.sqrt(x) for x in sizes]
    # Normalize the sizes to sum up to 1
    sizes_normalized = squarify.normalize_sizes(sizes, 10, 20)

    color_palette = [
    '#1f77b4',  # Teal
    '#ff7f0e',  # Orange
    '#2ca02c',  # Green
    '#d62728',  # Red
    '#9467bd',  # Purple
    '#8c564b',  # Brown
    '#e377c2',  # Pink
    '#7f7f7f',  # Gray
    '#bcbd22',  # Olive
    '#17becf',  # Cyan
    '#e41a1c',  # Magenta
    '#ffcc00',  # Yellow
    '#2bcbba',  # Light Green
    '#393b79',  # Dark Blue
    '#9edae5',  # Light Purple
    '#8c6d31',  # Dark Red
    ]
    
    # # Plot the treemap
    sqrt_values = np.sqrt([total, 1000000, 1000000, 672429])
    total_grid_cells = 10 * 12
    normalized_values = (sqrt_values / sum(sqrt_values)) * total_grid_cells

    rows = [int(value // 12) for value in normalized_values]  # Allocate rows based on normalized values
    extra_rows = total_grid_cells // 12 - sum(rows)  # Calculate any extra rows to distribute

    # Adjust the rows if there are remaining cells
    for i in range(extra_rows):
        rows[i % 4] += 1

    # Plot the results using a grid layout
    plt.figure(figsize=(12, 8))

    # Create subplots with varying sizes
    plot1 = plt.subplot2grid((10, 12), (0, 0), colspan=12, rowspan=rows[0])
    plot2 = plt.subplot2grid((10, 12), (rows[0], 0), colspan=12, rowspan=rows[1])
    plot3 = plt.subplot2grid((10, 12), (rows[0] + rows[1], 0), colspan=12, rowspan=rows[2])
    plot4 = plt.subplot2grid((10, 12), (rows[0] + rows[1] + rows[2], 0), colspan=12, rowspan=rows[3])


    plot1.axis('off')
    plot1.set_title(f'Words scraped per Formosan language ({total} total)', fontsize=16)
    squarify.plot(sizes=sizes_normalized, label=labels, color=color_palette, alpha=.8, ax=plot1, text_kwargs={'fontsize': 14})

    plot2.set_title('Francis & Kucera Corpus', fontsize=16)
    plot2.axis('off')
    squarify.plot(sizes=[1], label=['~ 1 Million Words'], alpha=.8, ax=plot2, text_kwargs={'fontsize': 14})

    plot3.set_title('Penn Treebank - WSJ section', fontsize=16)
    plot3.axis('off')
    squarify.plot(sizes=[1], label=['~ 1 Million Words'], alpha=.8, ax=plot3, text_kwargs={'fontsize': 14})

    plot4.set_title('Adam, Eve, and Sarah Corpus', fontsize=16)
    plot4.axis('off')
    squarify.plot(sizes=[1], label=['672,429 Words'], alpha=.8, ax=plot4, text_kwargs={'fontsize': 14})


    plt.tight_layout()
    plt.savefig("Treemap.png")
    plt.show()



   

if __name__ == "__main__":
    main()