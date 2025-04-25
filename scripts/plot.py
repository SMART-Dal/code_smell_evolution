import os
import pandas as pd
import matplotlib.pyplot as plt
import config
from utils import FileUtils

def no_removal_refs():
    # Read CSV
    df = pd.read_csv(os.path.join(config.SMELL_REF_MAP_PATH, 'corpus.csv'), low_memory=False)

    # Filter only where is_alive is False i.e, removed smell instances
    df = df[df['is_alive'] == False]
    
    # Filter where removal_refactorings is missing or empty
    no_removal_refactorings = df[df['removal_refactorings'].isna() | (df['removal_refactorings'].astype(str).str.strip() == '')]

    # Group by smell_type
    total_by_type = df.groupby('smell_type').size()
    no_removal_by_type = no_removal_refactorings.groupby('smell_type').size()
    
    print(f"total no_removal_by_type: {no_removal_by_type.sum()}")
    print(f"Percentage of total no_removal_by_type compared to total: {(no_removal_by_type.sum() / total_by_type.sum()) * 100:.2f}%")

    # Calculate percentage
    percent_no_removal = (no_removal_by_type / total_by_type * 100).sort_values(ascending=True)

    # Create new labels: "smell_type (total count)"
    labels_with_counts = [f"{stype} ({total_by_type[stype]})" for stype in percent_no_removal.index]

   
    # Plot the bars
    fig, ax = plt.subplots(figsize=(10, 12))
    bars = ax.barh(labels_with_counts, percent_no_removal.values, color='#1f77b4')  # Classic "paper blue"
    
    # Add count labels on top-left of bar tips
    for bar, stype in zip(bars, percent_no_removal.index):
        count = no_removal_by_type.get(stype, 0)
        bar_width = bar.get_width()
        bar_center = bar.get_y() + bar.get_height() / 2

        ax.text(
            bar_width - 0.1,         # a little to the left of the bar tip
            bar_center,
            str(count),
            va='center',
            ha='right',
            fontsize=9,
        )

    # Set x-axis range to zoom from 80 to 100
    ax.set_xlim(85, 100)
    # Show x-axis ticks and labels on both top and bottom
    ax.tick_params(axis='x', which='both', labeltop=True, labelbottom=True)
    ax.xaxis.set_label_position('top')
    ax.set_xlabel('Percentage of smell instances without any removal refactorings', fontsize=12)
    ax.set_ylabel('Smell Type', rotation=90, fontsize=12)
    ax.xaxis.label.set_color('black')
    ax.yaxis.label.set_color('black')
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    fig.subplots_adjust(left=0.40)
    
    plt_save_dir = os.path.join(config.PLOTS_PATH)
    os.makedirs(plt_save_dir, exist_ok=True)
    plot_path = os.path.join(plt_save_dir, 'unmapped_smell_instances.png')
    # plt.savefig(plot_path)
    plt.close()

def unmapped_refactorings():
    '''
    this function will generate latex table for the refactorings that are not mapped to any smell
    '''
    table = {}
    table_plot_path = os.path.join(config.PLOTS_PATH)
    
    maps_path = os.path.join(config.SMELL_REF_MAP_PATH)
    for f in FileUtils.traverse_directory(maps_path):
        if f.endswith('.json') and not f.endswith('.stats.json') and not f.endswith('.chain.json'):
            data = FileUtils.load_json_file(f)
            unmapped_refactorings = data.get('unmapped_refactorings', [])
            for r in unmapped_refactorings:
                r_type = r.get('type_name')
                if r_type not in table:
                    table[r_type] = 1
                else:
                    table[r_type] += 1
    
    # Calculate total unmapped refactorings
    total_unmapped = sum(table.values())

    # Sort by count in descending order
    sorted_table = dict(sorted(table.items(), key=lambda item: item[1], reverse=True))

    # Limit to top 14 and group the rest as 'other refactoring types'
    top_15 = list(sorted_table.items())[:15]
    others = list(sorted_table.items())[15:]
    
    # Calculate 'other refactoring types' count and percentage
    others_count = sum(count for _, count in others)

    # Prepare final table with top 14 and 'other refactoring types'
    final_table = top_15 + [('other refactoring types', others_count)]

    # Save LaTeX table rows to a .txt file
    output_file = os.path.join(table_plot_path, 'unmapped_ref_latex_table.txt')
    with open(output_file, 'w') as f:
        for r, count in final_table:
            percentage = (count / total_unmapped) * 100
            f.write(f"{r.replace('_', ' ')} & ${count}$ & ${percentage:.2f}\\%$ \\\\\n")

if __name__ == "__main__":
    no_removal_refs()