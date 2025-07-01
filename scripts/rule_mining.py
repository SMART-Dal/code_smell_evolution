import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

import os
import config

# Step 1: Load CSV
corpus_path = os.path.join(config.SMELL_REF_MAP_PATH, 'corpus_OLD.csv')
df = pd.read_csv(corpus_path, low_memory=False)

# Step 2: Hardcoded list of valid refactorings
valid_pairs = {
    'Broken Modularization': ['Move Attribute'],
    'Deficient Encapsulation': ['Change Attribute Access Modifier'],
    'Insufficient Modularization': ['Extract Method'],
    'Multifaceted Abstraction': ['Extract Method'],
    'Complex Method': ['Extract Method'],
    'Imperative Abstraction': ['Extract Method', 'Change Attribute Access Modifier'],
    'Complex Conditional': ['Extract Method', 'Extract Variable'],
    'Long Method': ['Extract Method', 'Extract and Move Method'],
    'Unexploited Encapsulation': ['Change Parameter Type', 'Change Variable Type'],
    'Long Statement': ['Change Variable Type', 'Rename Variable'],
    'Long Identifier': ['Rename Variable'],
    'Abstract Function Call From Constructor': ['Remove Class Modifier', 'Add Parameter'],
    'Empty Catch Block': ['Assert Throw'],
    'Long Parameter List': ['Remove Parameter']
}

# Step 3: Split and filter rows based on valid smell-refactoring pairs
def filter_valid_refactorings(row):
    smell = row['smell_type']
    if pd.isna(row['removal_refactorings']):
        return []
    refacs = [r.strip() for r in row['removal_refactorings'].split(';')]
    valid_refacs = valid_pairs.get(smell, [])
    return [r for r in refacs if r in valid_refacs]

df['parsed_refactorings'] = df.apply(filter_valid_refactorings, axis=1)
df_filtered = df[df['parsed_refactorings'].apply(lambda x: len(x) > 0)].copy()

# Step 4: Prepare data for Apriori
# Each transaction: smell_type + removal_refactorings
transactions = []
for _, row in df_filtered.iterrows():
    transaction = [f"S::{row['smell_type']}"] + [f"R::{r}" for r in row['parsed_refactorings']]
    transactions.append(transaction)

# Create one-hot encoded DataFrame
te = TransactionEncoder()
te_ary = te.fit(transactions).transform(transactions)
df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

# Step 5: Apply Apriori algorithm
frequent_itemsets = apriori(df_encoded, min_support=0.01, use_colnames=True)

# Step 6: Generate association rules
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
print("Total rules:", len(rules))

# Step 7: Filter rules where antecedents are only refactorings and consequents are only smells
def is_valid_rule(antecedents, consequents):
    # Check if antecedents are all refactorings and consequents are all smells
    antecedent_types = {item.split('::')[0] for item in antecedents}
    consequent_types = {item.split('::')[0] for item in consequents}
    
    return (len(antecedent_types) == 1 and 'R' in antecedent_types and
            len(consequent_types) == 1 and 'S' in consequent_types)

filtered_rules = rules[rules.apply(lambda x: is_valid_rule(x['antecedents'], x['consequents']), axis=1)]
print("Total filtered rules (before confidence filter):", len(filtered_rules))

# Step 8: Apply confidence threshold (> 0.3)
# filtered_rules = filtered_rules[filtered_rules['confidence'] > 0.3]
# print("Total filtered rules (after confidence > 0.3):", len(filtered_rules))

# Optional: Sort by confidence
filtered_rules = filtered_rules.sort_values(by="confidence", ascending=False)

# Add frequency count (absolute support count)
filtered_rules = filtered_rules.copy()
filtered_rules['frequency'] = (filtered_rules['support'] * len(df_encoded)).astype(int)

# Display
print(filtered_rules[['antecedents', 'consequents', 'support', 'confidence', 'lift', 'frequency']])

# Save to csv with columns - ID, Rules (antecedents -> consequents), support, confidence, lift, frequency
filtered_rules = filtered_rules.reset_index(drop=True)
filtered_rules['ID'] = filtered_rules.index + 1
filtered_rules['Rules'] = filtered_rules.apply(
    lambda row: f"({', '.join(sorted([str(a) for a in row['antecedents']]))} -> {', '.join(sorted([str(c) for c in row['consequents']]))})",
    axis=1
)

# Round support, confidence, lift to 5 decimal places before saving
filtered_rules['support'] = filtered_rules['support'].round(5)
filtered_rules['confidence'] = filtered_rules['confidence'].round(5)
filtered_rules['lift'] = filtered_rules['lift'].round(5)

# Reorder columns: ID, Rules, support, confidence, lift, frequency
output_columns = ['ID', 'Rules', 'support', 'confidence', 'lift', 'frequency']
output_path = os.path.join(os.path.dirname(config.SMELL_REF_MAP_PATH), "association_rules_OLD.csv")
filtered_rules[output_columns].to_csv(output_path, index=False)
print(f"Saved association rules to: {output_path}")