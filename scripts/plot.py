import os
import pandas as pd
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter
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
            color='white',
            fontweight='bold',
        )

    # Set x-axis range to zoom from 80 to 100
    ax.set_xlim(85, 101)
    ax.set_ylim(-0.4, len(labels_with_counts) - 0.4)
    # Show x-axis ticks and labels on both top and bottom
    ax.tick_params(axis='x', which='both', labeltop=True, labelbottom=True)
    ax.xaxis.set_label_position('top')
    ax.set_xlabel('Percentage of smell instances without any removal refactorings', fontsize=12, labelpad=10)
    ax.set_ylabel('Smell Type', rotation=90, fontsize=12)
    ax.xaxis.label.set_color('black')
    ax.yaxis.label.set_color('black')
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    # Remove all axis spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(left=0.45)    
    plt_save_dir = os.path.join(config.PLOTS_PATH)
    os.makedirs(plt_save_dir, exist_ok=True)
    plot_path = os.path.join(plt_save_dir, 'unmapped_smell_instances.png')
    plt.savefig(plot_path)
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

def survival_analysis():    
    FIGSIZE_PER_PLOT = (8, 5)
    
    corpus_path = os.path.join(config.SMELL_REF_MAP_PATH, 'corpus.csv')
    plot_path = os.path.join(config.PLOTS_PATH)
    # Load your CSV file
    df = pd.read_csv(corpus_path, low_memory=False)  # Replace with your actual file path

    # Use all rows and determine event observed
    df["event_observed"] = df["is_alive"].apply(lambda alive: 0 if alive else 1)
    smell_kinds = ["Design", "Implementation"]
    
    ###############
    ### COMMITS ###
    ###############
    CUTOFF_COMMITS = 1200
    CHECKPOINTS_COMMITS = [10, 100, 500]
    fig_commits, axes_commits = plt.subplots(1, len(smell_kinds), figsize=(FIGSIZE_PER_PLOT[0]*len(smell_kinds), FIGSIZE_PER_PLOT[1]), squeeze=False)
    for idx, smell_kind in enumerate(smell_kinds):
        ax = axes_commits[0, idx]
        kind_df = df[df["smell_kind"] == smell_kind]
        survival_table = []

        # Plot by smell_type within the smell_kind
        for smell in kind_df["smell_type"].unique():
            kmf = KaplanMeierFitter()
            smell_df = kind_df[kind_df["smell_type"] == smell]
            durations = pd.to_numeric(smell_df["total_commits_span"], errors='coerce').dropna()
            events = smell_df.loc[durations.index, "event_observed"] 

            # Remove outliers with commit spans greater than the cutoff
            durations = durations[durations > 0]  # remove zeros
            durations = durations[durations <= CUTOFF_COMMITS]
            events = events.loc[durations.index]
            
            if len(durations) > 0:
                kmf.fit(durations=durations, event_observed=events, label=smell)
                kmf.plot_survival_function(ax=ax, ci_show=False, show_censors=True)
                survival_probs = {cp: kmf.predict(cp) for cp in CHECKPOINTS_COMMITS}
                survival_probs["smell_type"] = smell
                survival_table.append(survival_probs)
                
        ax.set_title(f"{smell_kind} Smells", fontsize=15)
        ax.set_xlabel("Commits (Log Scale)", fontsize=13)
        ax.set_xscale("log")
        ax.set_ylabel("Survival Probability", fontsize=13)
        ax.grid(True)
        
        # Move legend to the right outside the plot and remove the border box
        ax.legend(title="Smell Type", fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
        
        # Remove plot axis borders
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        # Show x-axis ticks explicitly
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}'))
        ax.tick_params(axis='x', which='both', length=0, labelsize=10)  # Remove all tick markers but keep labels
        ax.tick_params(axis='y', which='both', length=0, labelsize=10)  # Remove all tick markers but keep labels

        survival_table_df = pd.DataFrame(survival_table).set_index("smell_type")
        print(f"\nSurvival Table for {smell_kind} Smells:")
        print(survival_table_df)
        
        # Calculate the average survival probabilities across all smell types
        avg_survival_probs = survival_table_df.mean()
        print("\nAverage Survival Probabilities:")
        print(avg_survival_probs)

    plt.tight_layout()
    commits_plot_path = os.path.join(plot_path, f"kaplan_meier_commits_x_scaled.png")
    plt.savefig(commits_plot_path)
    plt.close()
    print(f"Kaplan-Meier plot (by commits) for saved to {commits_plot_path}")

    ###############
    #### DAYS #####
    ###############
    CUTOFF_DAYS = 3650  # 10 years as a cutoff for days
    CHECKPOINTS_DAYS = [10, 100]
    fig_days, axes_days = plt.subplots(1, len(smell_kinds), figsize=(FIGSIZE_PER_PLOT[0]*len(smell_kinds), FIGSIZE_PER_PLOT[1]), squeeze=False)
        
    for idx, smell_kind in enumerate(smell_kinds):
        ax = axes_days[0, idx]
        kind_df = df[df["smell_kind"] == smell_kind]
        survival_table = []

        for smell in kind_df["smell_type"].unique():
            kmf = KaplanMeierFitter()
            smell_df = kind_df[kind_df["smell_type"] == smell]
            durations = pd.to_numeric(smell_df["total_days_span"], errors='coerce').dropna()
            events = smell_df.loc[durations.index, "event_observed"] 

            # Remove outliers with days spans greater than the cutoff
            durations = durations[durations > 0]
            durations = durations[durations <= CUTOFF_DAYS]
            events = events.loc[durations.index]
            
            if len(durations) > 0:
                kmf.fit(durations=durations, event_observed=events, label=smell)
                kmf.plot_survival_function(ax=ax, ci_show=False, show_censors=True)
                survival_probs = {cp: kmf.predict(cp) for cp in CHECKPOINTS_DAYS}
                survival_probs["smell_type"] = smell
                survival_table.append(survival_probs)
        
        ax.set_title(f"{smell_kind} Smells", fontsize=15)
        ax.set_xlabel("Days (Log Scale)", fontsize=13)
        ax.set_xscale("log")
        ax.set_ylabel("Survival Probability", fontsize=13)
        ax.grid(True)
        
        # Move legend to the right outside the plot and remove the border box
        ax.legend(title="Smell Type", fontsize=10, loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
        
        # Remove plot axis borders
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        # Show x-axis ticks explicitly
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}'))
        
        ax.tick_params(axis='x', which='both', length=0, labelsize=10)  # Remove all tick markers but keep labels
        ax.tick_params(axis='y', which='both', length=0, labelsize=10)  # Remove all tick markers but keep labels
        
        survival_table_df = pd.DataFrame(survival_table).set_index("smell_type")
        print(f"\nSurvival Table for {smell_kind} Smells:")
        print(survival_table_df)
        
        # Calculate the average survival probabilities across all smell types
        avg_survival_probs = survival_table_df.mean()
        print("\nAverage Survival Probabilities:")
        print(avg_survival_probs)

    plt.tight_layout()
    days_plot_path = os.path.join(plot_path, f"kaplan_meier_days_x_scaled.png")
    plt.savefig(days_plot_path)
    plt.close()
    print(f"Kaplan-Meier plot (by days) for saved to {days_plot_path}")

def sankey_plot_input():
    corpus_path = os.path.join(config.SMELL_REF_MAP_PATH, 'corpus.csv')
    df = pd.read_csv(corpus_path, low_memory=False)

    # Add 'moved' column first since it's needed early now
    df['moved'] = df.apply(lambda row: 'moved' if row['movements'] > 1 or row['chain_length'] > 1 else 'not_moved', axis=1)
    
    ### LAYER 1 to 2: smell_kind -> moved
    grouped1 = df.groupby(['smell_kind', 'moved']).size().reset_index(name='value')
    for _, row in grouped1.iterrows():
        print(f"{row['smell_kind']} [{row['value']}] {row['moved']}")
    
    ### LAYER 2 to 3: moved -> is_alive
    grouped2 = df.groupby(['moved', 'is_alive']).size().reset_index(name='value')
    for _, row in grouped2.iterrows():
        print(f"{row['moved']} [{row['value']}] {row['is_alive']}")
    
    ### LAYER 3 to 4: is_alive -> mapping
    df['mapping'] = df['removal_refactorings'].apply(
        lambda x: 'Mapped to refactorings' if pd.notna(x) and str(x).strip() != '' else 'No mapping'
    )
    grouped3 = df.groupby(['is_alive', 'mapping']).size().reset_index(name='value')
    for _, row in grouped3.iterrows():
        print(f"{row['is_alive']} [{row['value']}] {row['mapping']}")