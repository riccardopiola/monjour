import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from monjour.st import StApp

def income_expense_by_category(df: pd.DataFrame):
    agg_data = df.groupby(['account_id', 'category'], as_index=False).agg({'amount': 'sum'})

    fig = px.bar(
        agg_data,
        x="account_id",
        y="amount",
        color="category",
        title="Expense vs. Income by Account",
        labels={"amount": "Total Amount", "account_id": "Account"},
        barmode="relative",
        text="amount"  # Add labels for amounts
    )

    # Customize the chart layout
    fig.update_layout(
        xaxis_title="Account",
        yaxis_title="Total Amount",
        legend_title="Category",
        # template="plotly_white",
        yaxis=dict(tickformat="$,.2f")  # Format y-axis for currency
    )

def line_income_expense(df: pd.DataFrame, week_month: str = 'week'):

    amount_data = df.groupby([week_month, 'type'], as_index=False).agg({'amount': 'sum'})

    income_data = amount_data[amount_data['type'] == 'Income']
    expense_data = amount_data[amount_data['type'] == 'Expenses']

    # Initialize figure
    fig = go.Figure()

    # Add bar chart for income
    fig.add_trace(go.Bar(
        x=income_data[week_month],
        y=income_data['amount'],
        name="Income",
        marker_color='green'
    ))

    # Add bar chart for expenses
    fig.add_trace(go.Bar(
        x=expense_data[week_month],
        y=expense_data['amount'],
        name="Expenses",
        marker_color='red'
    ))

    # Customize layout
    label = "Week" if week_month == 'week' else "Month"
    fig.update_layout(
        title=f"{label} Income vs Expenses",
        xaxis_title=label,
        yaxis_title="Total Amount",
        barmode='group',  # Group bars side-by-side
        template="plotly_white",
        yaxis=dict(tickformat="$,.2f")  # Format y-axis for currency
    )

    return fig
