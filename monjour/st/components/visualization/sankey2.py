import pandas as pd
import plotly.graph_objects as go

from monjour.st import StApp, monjour_app_cache

@monjour_app_cache(key='sankey_diagram')
def sankey_diagram(st_app: StApp):
    pass

def sankey(income: pd.DataFrame, expenses: pd.DataFrame):

    total_income = income['amount_abs'].sum()
    total_expenses = expenses['amount_abs'].sum()

    # Create central total node
    central_total = min(total_income, total_expenses)

    # Prepare links for Sankey diagram
    links = []

    # From income categories to central total
    for _, row in income.iterrows():
        links.append({
            'source': row['category'],
            'target': 'Total',
            'value': row['amount_abs']
        })

    # From central total to expense categories
    for _, row in expenses.iterrows():
        links.append({
            'source': 'Total',
            'target': row['category'],
            'value': row['amount_abs']
        })

    # Combine all unique nodes (income, total, expenses)
    all_nodes = list(pd.concat([
        pd.Series(income['category']),
        pd.Series(['Total']),
        pd.Series(expenses['category'])
    ]).unique())

    # Map nodes to indices for Plotly Sankey
    node_indices = {node: i for i, node in enumerate(all_nodes)}
    for link in links:
        link['source_index'] = node_indices[link['source']]
        link['target_index'] = node_indices[link['target']]

    # Create Sankey diagram
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=all_nodes,
            color="blue"
        ),
        link=dict(
            source=[link['source_index'] for link in links],
            target=[link['target_index'] for link in links],
            value=[link['value'] for link in links],
            color="rgba(44, 160, 101, 0.6)" 
        )
    ))

    fig.update_layout(
        title_text="Sankey Diagram: Income to Expenses",
        font_size=10
    )

    return fig