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
    CUTOFF_COMMITS = 15000
    CHECKPOINTS_COMMITS = [10, 100]
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
                
        ax.set_title(f"{smell_kind} Smells")
        ax.set_xlabel("Commits (Log Scale)")
        ax.set_xscale("log")
        ax.set_ylabel("Survival Probability")
        ax.grid(True)
        ax.legend(title="Smell Type")
        
        # Show x-axis ticks explicitly
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}'))

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
        
        ax.set_title(f"{smell_kind} Smells")
        ax.set_xlabel("Days (Log Scale)")
        ax.set_xscale("log")
        ax.set_ylabel("Survival Probability")
        ax.grid(True)
        ax.legend(title="Smell Type")
        
        # Show x-axis ticks explicitly
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}'))
        
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

def group_unmapped_manual_analysis_results():
    target_dir = config.MANUAL_ANALYSIS_FOR_UNMAPPED_PATH
    reason_to_files = {}

    for f in FileUtils.traverse_directory(target_dir):
        f_data = FileUtils.load_json_file(f)
        for d in f_data:
            reason = d["human_analysis"]["reason?"]
            if reason and reason.strip():  # Skip empty or whitespace-only reasons
                file_basename = os.path.basename(f).split('.')[0]
                if reason not in reason_to_files:
                    reason_to_files[reason] = {}
                if file_basename not in reason_to_files[reason]:
                    reason_to_files[reason][file_basename] = 0
                reason_to_files[reason][file_basename] += 1

    # Create a DataFrame where reasons are columns and smell names are rows
    all_smell_names = sorted({smell for smells in reason_to_files.values() for smell in smells})
    all_reasons = sorted(reason_to_files.keys())

    table_data = []
    for smell_name in all_smell_names:
        row = []
        for reason in all_reasons:
            row.append(reason_to_files.get(reason, {}).get(smell_name, 0))
        table_data.append(row)

    reason_smell_table = pd.DataFrame(table_data, index=all_smell_names, columns=all_reasons)
    print("\nReason-Smell Table:")
    print(reason_smell_table)

    # Save the table to a CSV file
    output_csv_path = os.path.join(config.OUTPUT_PATH, "reason_unmapped_smell_table.csv")
    reason_smell_table.to_csv(output_csv_path)
    print(f"Reason-Smell Table saved to {output_csv_path}")

if __name__ == "__main__":
    survival_analysis()