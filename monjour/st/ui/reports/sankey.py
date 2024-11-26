import plotly.graph_objects as go
import streamlit as st
import pandas as pd

# Separate income and expenses
income = df[df['category'].str.startswith('Income')].copy()
expenses = df[df['category'].str.startswith('Expenses')].copy()

# Make amounts positive for easier flow calculation
income['amount'] = income['amount'].abs()
expenses['amount'] = expenses['amount'].abs()

# Normalize income flows to distribute proportionally across expenses
total_income = income['amount'].sum()
total_expenses = expenses['amount'].sum()
income['proportion'] = income['amount'] / total_income
expenses['proportion'] = expenses['amount'] / total_expenses

# Create all source-target pairs with proportional flows
links = []
for _, inc_row in income.iterrows():
    for _, exp_row in expenses.iterrows():
        links.append({
            'source': inc_row['category'],
            'target': exp_row['category'],
            'value': inc_row['proportion'] * exp_row['amount']
        })

# Convert links to DataFrame
links_df = pd.DataFrame(links)

# Create unique nodes for the Sankey diagram
all_nodes = list(pd.concat([links_df['source'], links_df['target']]).unique())
node_indices = {node: i for i, node in enumerate(all_nodes)}
links_df['source_index'] = links_df['source'].map(node_indices)
links_df['target_index'] = links_df['target'].map(node_indices)

# Create the Sankey diagram
fig = go.Figure(go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=all_nodes
    ),
    link=dict(
        source=links_df['source_index'],
        target=links_df['target_index'],
        value=links_df['value']
    )
))

# Update layout
fig.update_layout(
    title_text="Income to Expenses Flow (Sankey Diagram)",
    font_size=10
)

st.plotly_chart(fig, use_container_width=True)