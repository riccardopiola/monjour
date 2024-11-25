import pandas as pd
import plotly.graph_objects as go

from monjour.st import StApp, monjour_app_cache

@monjour_app_cache(key='sankey_diagram')
def common_df(st_app: StApp):
    df = st_app.app.df.copy()
    df['category'] = df['category'].str.replace('.', '/')
    df['expense'] = df['amount'] < 0
    df['amount_abs'] = df['amount'].abs()
    return df


def sankey_diagram(df: pd.DataFrame):
    df = df.copy()
    expenses = df[df['expense']]
    income = df[~df['expense']]

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
    draw_sankey_diagram(links_df, 'source', 'target', 'value', 'Income vs Expenses by Category')

def draw_sankey_diagram(df: pd.DataFrame, source_col: str, target_col: str, value_col: str, title: str):
    """
    Given a dataframe with source, target, and value columns, draw a Sankey diagram.

    Example:
        df = pd.DataFrame({
            "source": ["Income/Salary", "Income/Salary", "Income/Gifts", "Income/Investments"],
            "target": ["Expenses/Food", "Expenses/Housing", "Expenses/Transport", "Expenses/Food"],
            "amount": [2000, 1500, 300, 500]
        })
        draw_sankey_diagram(df, 'source', 'target', 'amount', 'Income vs Expenses by Category')
    """

    # Create unique nodes for the Sankey diagram
    all_nodes = list(pd.concat([df[source_col], df[target_col]]).unique())
    node_indices = {node: i for i, node in enumerate(all_nodes)}
    df['source_index'] = df[source_col].map(node_indices)
    df['target_index'] = df['target'].map(node_indices)

    # Create the Sankey diagram
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=all_nodes
        ),
        link=dict(
            source=df['source_index'],
            target=df['target_index'],
            value=df[value_col]
        )
    ))

    fig.update_layout(title=title)
    return fig