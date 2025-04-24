import os
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from utils import FileUtils
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from lifelines import KaplanMeierFitter
import config

def funct1():
    target_dir = config.MANUAL_ANALYSIS_PATH
    for f in FileUtils.traverse_directory(target_dir):
        f_data = FileUtils.load_json_file(f)
        
        for d in f_data:
            try:
                d["human_analysis"]["correct_mapping?"] = d["llm_analysis"]["correct_mapping?"]
                d["human_analysis"]["decreases_severity?"] = d["llm_analysis"]["decreases_severity?"]
            except Exception as e:
                print(f"An error occurred: {e}")
        
        # Save the updated data back to the JSON file
        FileUtils.save_json_file(f, f_data)
        print(f"Updated {f} with human analysis data.")
        
def calculate_kappa():
    human_res = []
    llm_res = []
    
    target_dir = config.MANUAL_ANALYSIS_PATH
    for f in FileUtils.traverse_directory(target_dir):        
        f_data = FileUtils.load_json_file(f)
        
        for d in f_data:
            try:
                human_res.append(d["human_analysis"]["correct_mapping?"])
                llm_res.append(d["llm_analysis"]["correct_mapping?"])
            except Exception as e:
                print(f"An error occurred: {e}")
        
    # Calculate Cohen's Kappa score
    kappa_score = cohen_kappa_score(human_res, llm_res)
    print(f"Cohen's Kappa Score: {kappa_score}")

def survival_analysis():
    CUTOFF_COMMITS = 15000
    CUTOFF_DAYS = 3650  # 10 years as a cutoff for days
    FIGSIZE_PER_PLOT = (7, 6)
    
    corpus_path = os.path.join(config.SMELL_REF_MAP_PATH, 'corpus.csv')
    plot_path = os.path.join(config.PLOTS_PATH)
    # Load your CSV file
    df = pd.read_csv(corpus_path, low_memory=False)  # Replace with your actual file path

    # Use all rows and determine event observed
    df["event_observed"] = df["is_alive"].apply(lambda alive: 0 if alive else 1)
    smell_kinds = df["smell_kind"].unique()
    
    ###############
    ### COMMITS ###
    ###############
    fig_commits, axes_commits = plt.subplots(1, len(smell_kinds), figsize=(FIGSIZE_PER_PLOT[0]*len(smell_kinds), FIGSIZE_PER_PLOT[1]), squeeze=False)
    for idx, smell_kind in enumerate(smell_kinds):
        ax = axes_commits[0, idx]
        kind_df = df[df["smell_kind"] == smell_kind]

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
                
        ax.set_title(f"{smell_kind} Smells")
        ax.set_xlabel("Commits")
        # ax.set_xscale("log")
        ax.set_ylabel("Survival Probability")
        ax.set_yscale("log")
        ax.grid(True)
        ax.legend(title="Smell Type")
        
        # Format y-axis ticks to show up to 4 decimal points
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.4f}'))

    plt.tight_layout()
    commits_plot_path = os.path.join(plot_path, f"kaplan_meier_commits_y_scaled.png")
    plt.savefig(commits_plot_path)
    plt.close()
    print(f"Kaplan-Meier plot (by commits) for saved to {commits_plot_path}")

    ###############
    #### DAYS #####
    ###############
    fig_days, axes_days = plt.subplots(1, len(smell_kinds), figsize=(FIGSIZE_PER_PLOT[0]*len(smell_kinds), FIGSIZE_PER_PLOT[1]), squeeze=False)
        
    for idx, smell_kind in enumerate(smell_kinds):
        ax = axes_days[0, idx]
        kind_df = df[df["smell_kind"] == smell_kind]

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
        
        ax.set_title(f"{smell_kind} Smells")
        ax.set_xlabel("Days")
        # ax.set_xscale("log")
        ax.set_ylabel("Survival Probability")
        ax.set_yscale("log")
        ax.grid(True)
        ax.legend(title="Smell Type")
        
        # Format y-axis ticks to show up to 4 decimal points
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.4f}'))

    plt.tight_layout()
    days_plot_path = os.path.join(plot_path, f"kaplan_meier_days_y_scaled.png")
    plt.savefig(days_plot_path)
    plt.close()
    print(f"Kaplan-Meier plot (by days) for saved to {days_plot_path}")

def no_of_samples_analyzed_manually():
    target_dir = config.MANUAL_ANALYSIS_PATH
    total_samples = 0
    for f in FileUtils.traverse_directory(target_dir):
        f_data = FileUtils.load_json_file(f)
        total_samples += len(f_data)
    
    print(f"Total samples analyzed manually: {total_samples}")

def refactoring_introduced_removed_distribution():
    corpus_path = os.path.join(config.SMELL_REF_MAP_PATH, 'corpus.csv')
    df = pd.read_csv(corpus_path, low_memory=False)
    
    df['introduction_refactorings'].replace('', pd.NA, inplace=True)
    df['removal_refactorings'].replace('', pd.NA, inplace=True)
    
    # Create boolean columns indicating presence of refactorings
    df['has_intro_refactorings'] = df['introduction_refactorings'].notna()
    df['has_removal_refactorings'] = df['removal_refactorings'].notna()
    
    #Distribution
    intro_dist = df['has_intro_refactorings'].value_counts().rename_axis('has_intro_refactorings').reset_index(name='count')
    removal_dist = df['has_removal_refactorings'].value_counts().rename_axis('has_removal_refactorings').reset_index(name='count')
    
    print("Introduction Refactorings Distribution:\n", intro_dist)
    print("\nRemoval Refactorings Distribution:\n", removal_dist)

def span_box_plots():
    CUTOFF_COMMITS = 15000
    CUTOFF_DAYS = 4000  # 10 years as a cutoff for days
    
    corpus_path = os.path.join(config.SMELL_REF_MAP_PATH, 'corpus.csv')
    df = pd.read_csv(corpus_path, low_memory=False)
    plots_path = os.path.join(config.PLOTS_PATH)
    
    # Replace 0 or negative values to avoid issues with log scale (if any)
    df['total_commits_span'] = df['total_commits_span'].apply(lambda x: x if 0 < x <= CUTOFF_COMMITS else np.nan)
    df['total_days_span'] = df['total_days_span'].apply(lambda x: x if 0 < x <= CUTOFF_DAYS else np.nan)
    
    
    
    # Plot 1: Box plot of total_commits_span per smell_kind
    plt.figure(figsize=(4, 4))
    sns.boxplot(x='smell_kind', y='total_commits_span', data=df, width=0.75, fliersize=0.05, gap=0.1, dodge=True, 
                boxprops=dict(alpha=0.7))  # Reduce box color brightness by setting alpha
    # plt.title('Total Commits Span by Smell Kind')
    plt.ylabel('Total Commits Span (Log Scale)')
    plt.yscale('log')
    
    # Add dotted grid lines for y-axis ticks
    ax = plt.gca()
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)  # Dotted lines with reduced opacity
    
    # Modify x-axis tick labels to add ' smells' and rotate them 45 degrees
    ax.set_xticklabels([f"{label.get_text()} Smell" for label in ax.get_xticklabels()])
    
    # Format y-axis ticks to show actual values instead of powers
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}'))
    
    plt.tight_layout()
    commits_box_plot_path = os.path.join(plots_path, 'box_plot_total_commits_span.png')
    plt.savefig(commits_box_plot_path)
    plt.close()
    print(f"Box plot for total commits span saved to {commits_box_plot_path}")



    # Plot 2: Box plot of total_days_span per smell_kind
    plt.figure(figsize=(4, 4))
    sns.boxplot(x='smell_kind', y='total_days_span', data=df, width=0.75, fliersize=0.05, gap=0.1, dodge=True,
                boxprops=dict(alpha=0.7))
    # plt.title('Total Days Span by Smell Kind')
    plt.ylabel('Total Days Span (Log Scale)')
    plt.yscale('log')
    
    # Add dotted grid lines for y-axis ticks
    ax = plt.gca()
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)  # Dotted lines with reduced opacity
    
    # Modify x-axis tick labels to add ' smells'
    ax = plt.gca()
    ax.set_xticklabels([f"{label.get_text()} Smell" for label in ax.get_xticklabels()])
    
    # Format y-axis ticks to show actual values instead of powers
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}'))
    
    plt.tight_layout()
    days_box_plot_path = os.path.join(plots_path, 'box_plot_total_days_span.png')
    plt.savefig(days_box_plot_path)
    plt.close()
    print(f"Box plot for total days span saved to {days_box_plot_path}")

def sankey_info():
    corpus_path = os.path.join(config.SMELL_REF_MAP_PATH, 'corpus.csv')
    df = pd.read_csv(corpus_path, low_memory=False)
    
    ### LAYER 1 and 2
    # Group and count the combinations
    grouped = df.groupby(['smell_kind', 'is_alive']).size().reset_index(name='value')
    # Generate output lines
    output_lines = grouped.apply(lambda row: f"{row['smell_kind']} [{row['value']}] {row['is_alive']}", axis=1)
    # Print each line
    for line in output_lines:
        print(line)
        
    ### LAYER 2 and 3
    # Determine if the smell is 'moved'
    df['moved'] = df.apply(lambda row: 'moved' if row['movements'] > 1 or row['chain_length'] > 1 else 'not_moved', axis=1)

    # Group and count
    grouped = df.groupby(['is_alive', 'moved']).size().reset_index(name='count')

    # Output in the requested format
    for _, row in grouped.iterrows():
        print(f"{row['is_alive']} [{row['count']}] {row['moved']}")
        
    ### LAYER 3 and 4
    df['mapping'] = df['removal_refactorings'].apply(
        lambda x: 'Mapped to refactorings' if pd.notna(x) and str(x).strip() != '' else 'No mapping'
    )

    grouped2 = df.groupby(['moved', 'mapping']).size().reset_index(name='count')
    for _, row in grouped2.iterrows():
        print(f"{row['moved']} [{row['count']}] {row['mapping']}")

if __name__ == "__main__":
    sankey_info()