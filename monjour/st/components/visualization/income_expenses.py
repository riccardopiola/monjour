import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def income_expense(df: pd.DataFrame, week_month: str = 'week'):

    amount_data = df.groupby([week_month, 'expense'], as_index=False).agg({'amount_abs': 'sum'})

    income_data = amount_data[amount_data['expense'] == False]
    expense_data = amount_data[amount_data['expense'] == True]

    # Initialize figure
    fig = go.Figure()

    # Add bar chart for income
    fig.add_trace(go.Bar(
        x=income_data[week_month],
        y=income_data['amount_abs'],
        name="Income",
        marker_color='green'
    ))

    # Add bar chart for expenses
    fig.add_trace(go.Bar(
        x=expense_data[week_month],
        y=expense_data['amount_abs'],
        name="Expenses",
        marker_color='red'
    ))

    # Customize layout
    label = "Week" if week_month == 'week' else "Month"
    fig.update_layout(
        title=f"Income vs Expenses by " + label,
        xaxis_title=label,
        yaxis_title="Total Amount",
        barmode='group',  # Group bars side-by-side
        template="plotly_white",
        yaxis=dict(tickformat="$,.2f")  # Format y-axis for currency
    )

    return fig

def income_expense_cumulative(df: pd.DataFrame):
    df = df.copy()
    cumulative_income = (
        df[df['expense'] == False]
        .groupby('date', as_index=False)
        .agg({'amount': 'sum'})
        .rename(columns={'amount': 'cumulative_income'})
    )
    cumulative_income['cumulative_income'] = cumulative_income['cumulative_income'].cumsum()

    cumulative_expenses = (
        df[df['expense'] == True]
        .groupby('date', as_index=False)
        .agg({'amount': 'sum'})
        .rename(columns={'amount': 'cumulative_expenses'})
    )
    cumulative_expenses['cumulative_expenses'] = cumulative_expenses['cumulative_expenses'].cumsum()

    # Merge cumulative data back into a single DataFrame
    cumulative_df = pd.merge(cumulative_income, cumulative_expenses, on='date', how='outer').ffill().fillna(0)
    # cumulative_df = pd.merge(cumulative_income, cumulative_expenses, on='date', how='outer').fillna(0)

    # Reshape the DataFrame to long format for Plotly
    long_format = pd.melt(
        cumulative_df,
        id_vars=['date'],
        value_vars=['cumulative_income', 'cumulative_expenses'],
        var_name='type',
        value_name='amount'
    )

    # Clean type labels for better readability
    long_format['type'] = long_format['type'].replace({
        'cumulative_income': 'Income',
        'cumulative_expenses': 'Expenses'
    })

    # Create a line chart
    fig = px.line(
        long_format,
        x='date',
        y='amount',
        color='type',
        labels={'amount': 'Cumulative Amount', 'type': 'Type', 'date': 'Date'},
        title='Cumulative Income vs Expenses Over Time',
    )

    # Customize the chart layout
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Cumulative Amount",
        template="plotly_white",
        yaxis=dict(tickformat="$,.2f"),  # Format y-axis for currency
        legend_title="Type",
    )

    return fig

def balance(df: pd.DataFrame, week_month: str = 'week'):
    amount_data = df.groupby([week_month], as_index=False).agg({'amount': 'sum'})
    amount_data['color'] = amount_data['amount'].apply(lambda x: 'green' if x > 0 else 'red')

    label = 'Week' if week_month == 'week' else 'Month'

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=amount_data[week_month],
        y=amount_data['amount'],
        mode='lines+markers',
        name='Balance Line',
        line=dict(color='yellow', width=2)
    ))

    # Add histogram as bars
    fig.add_trace(go.Bar(
        x=amount_data[week_month],
        y=amount_data['amount'],
        name='Balance Histogram',
        marker=dict(color=amount_data['color']),
        opacity=0.4
    ))

    fig.update_layout(
        title='Account Balance by ' + label,
        xaxis_title=label,
        yaxis_title='Total Amount',
        barmode='overlay',  # Overlay bars under the line
        template='plotly_white',
        yaxis=dict(tickformat="$,.2f"),
        legend_title='Type'
    )

    return fig

def balance_cum(df: pd.DataFrame):
    df = df.copy()
    df['cumulative_amount'] = df['amount'].cumsum()
    df['color'] = df['cumulative_amount'].apply(lambda x: 'green' if x > 0 else 'red')

    # Create figure
    fig = go.Figure()

    # Add cumulative histogram bars with conditional colors
    fig.add_trace(go.Bar(
        x=df['week'],
        y=df['cumulative_amount'],
        name='Cumulative Balance Bars',
        marker=dict(color=df['color']),  # Use the color column for conditional coloring
        opacity=0.6
    ))

    # Update layout
    fig.update_layout(
        title='Cumulative Income vs Expenses',
        xaxis_title='Week or Month',
        yaxis_title='Cumulative Total Amount',
        barmode='overlay',  # Overlay bars under the line
        template='plotly_white',
        yaxis=dict(tickformat="$,.2f"),
        legend_title='Type'
    )

    return fig

def expense_by_day_of_the_week(df: pd.DataFrame):
    df = df[df['expense'] == True]
    df = df.copy()
    df['day_of_week'] = df['date'].dt.day_name()
    agg_data = df.groupby('day_of_week', as_index=False).agg({'amount_abs': 'sum'})

    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    agg_data['day_of_week'] = pd.Categorical(agg_data['day_of_week'], categories=days_order, ordered=True)
    agg_data = agg_data.sort_values('day_of_week')

    # Create a bar chart
    fig = px.bar(
        agg_data,
        x='day_of_week',
        y='amount_abs',
        title='Total Expenses by Day of the Week',
        labels={'amount_abs': 'Total Expenses', 'day_of_week': 'Day of the Week'},
        template='plotly_white'
    )

    return fig