import dash
import pandas as pd
import numpy as np
from dash import dash_table
import logging
import plotly.graph_objs as go
import plotly.express as px
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import dash_daq as daq

# personal imports
import optimize_price
import optimize_quantity

group_colors = {"control": "light blue", "reference": "red"}

app = dash.Dash(
    __name__, meta_tags=[
        {"name": "viewport", "content": "width=device-width"}],
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

server = app.server

# Load the data
NAOS = pd.read_csv('C:/Users/FernandoGorraez/NAOS/Proyecto Automatización/Demand_Cadenas.csv')
NAOS.head(10)

#Get unique values for the dropdown filters
product_name = NAOS['NAME'].unique()
seller = NAOS['CADENA GENERAL'].unique()

# App Layout
app.layout = dbc.Container(
    [
        # Error Message
        html.Div(id="error-message"),
        
        # Top Banner
        dbc.Row(
            dbc.Col(
                html.H2("PRODUCT PRICE OPTIMIZATION", className="h2-title text-center"),
                width=12
            ),
            className="study-browser-banner"
        ),
        
        # Input Section and Recommendation
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H6("FILTER BY PRODUCT NAME"),
                        dcc.Dropdown(
                            id='product-category-filter',
                            options=[{'label': i, 'value': i} for i in product_name],
                            value=product_name[0],  # default value
                            clearable=False
                        ),
                        html.H6("FILTER BY SELLER"),
                        dcc.Dropdown(
                            id='region-filter',
                            options=[{'label': i, 'value': i} for i in seller],
                            value=seller[0],  # default value
                            clearable=False
                        ),
                        html.H6("OPTIMIZE"),
                        dcc.RadioItems(
                            id="selected-var-opt",
                            options=[
                                {"label": "Price", "value": "Price"},
                                {"label": "Quantity", "value": "Quantity"}
                            ],
                            value="Price",
                            labelStyle={
                                "display": "inline-block",
                                "padding": "12px 12px 12px 12px"
                            }
                        ),
                        html.H6("OPTIMIZATION RANGE"),
                        html.Div(id='output-container-range-slider'),
                        dcc.RangeSlider(
                            id='my-range-slider',
                            min=100,
                            max=1000,
                            step=100,
                            tooltip={"placement": "bottom", "always_visible": True},
                            value=[200, 400]
                        ),
                        html.H6("FIXED COST"),
                        daq.NumericInput(
                            id='selected-cost-opt',
                            min=0,
                            max=100,
                            value=80
                        ),
                        html.H6("RECOMMENDATION:"),
                        html.Div(id='id-insights', style={'color': 'DarkCyan', 'fontSize': 15})
                    ],
                    width=2
                ),
                
                # Graphs
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6("PRICE VS QUANTITY"),
                                        dcc.Graph(id="lineChart2")
                                    ],
                                    width=8
                                ),
                                dbc.Col(
                                    [
                                        html.H6("MAXIMIZING REVENUE"),
                                        dcc.Graph(id="lineChart1")
                                    ],
                                    width=8
                                )
                            ]
                        )
                    ],
                    width=7
                ),
                
                # Simulated Result Table
                dbc.Col(
                    [
                        html.H6("SIMULATED RESULT"),
                        dash_table.DataTable(
                            id='heatmap',
                            columns=[
                                {'name': 'Price', 'id': 'Price', 'type': 'numeric'},
                                {'name': 'Revenue', 'id': 'Revenue', 'type': 'numeric'},
                                {'name': 'Quantity', 'id': 'Quantity', 'type': 'numeric'}
                            ],
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'white'
                                },
                                {
                                    'if': {
                                        'row_index': 0,
                                        'column_id': 'Revenue'
                                    },
                                    'backgroundColor': 'dodgerblue',
                                    'color': 'black'
                                },
                                {
                                    'if': {
                                        'row_index': 0,
                                        'column_id': 'Price'
                                    },
                                    'backgroundColor': 'dodgerblue',
                                    'color': 'black'
                                },
                                {
                                    'if': {
                                        'row_index': 0,
                                        'column_id': 'Quantity'
                                    },
                                    'backgroundColor': 'dodgerblue',
                                    'color': 'black'
                                }
                            ],
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold',
                                'border': '1px solid black'
                            },
                            style_data={
                                'whiteSpace': 'normal',
                                'height': 'auto'
                            },
                            editable=True,
                            filter_action="native",
                            sort_action="native",
                            page_size=12
                        )
                    ],
                    width=3
                )
            ]
        )
    ],
    fluid=True,
    className="container-fluid"
)



@app.callback(
    dash.dependencies.Output('output-container-range-slider', 'children'),
    [dash.dependencies.Input('my-range-slider', 'value')]
)
def update_output(value):
    return f"Selected range: {value}"


@app.callback(
    [
        Output("heatmap", 'data'),
        Output("lineChart1", 'figure'),
        Output("lineChart2", 'figure'),
        Output("id-insights", 'children')
    ],
    [
        Input("product-category-filter", "value"),
        Input("region-filter", "value"),
        Input("selected-var-opt", "value"),
        Input("my-range-slider", "value"),
        Input("selected-cost-opt", "value")
    ]
)
def update_output_All(product_name, seller, var_opt, var_range, var_cost):
    try:
        # Filter the data based on the selected filters
        filtered_data = NAOS[
            (NAOS['NAME'] == product_name) &
            (NAOS['CADENA GENERAL'] == seller)
        ]
        
        if var_opt == 'Price':
            res, fig_PriceVsRevenue, fig_PriceVsQuantity, opt_Price, opt_Revenue = optimize_price.fun_optimize(
                var_opt, var_range, var_cost, filtered_data)
            res = np.round(res.sort_values('Revenue', ascending=False), decimals=2)

            if opt_Revenue > 0:
                return [
                    res.to_dict('records'), fig_PriceVsRevenue, fig_PriceVsQuantity, 
                    f'The maximum revenue of {opt_Revenue} is achieved by optimizing {var_opt} at {opt_Price}, with a fixed cost of {var_cost}. The optimization range was {var_range}.'
                ]
            else:
                return [
                    res.to_dict('records'), fig_PriceVsRevenue, fig_PriceVsQuantity, 
                    f'For the fixed cost of {var_cost} and {var_opt} range between {var_range}, you will incur a loss in revenue.'
                ]
        else:
            res, fig_QuantityVsRevenue, fig_PriceVsQuantity, opt_Quantity, opt_Revenue = optimize_quantity.fun_optimize(
                var_opt, var_range, var_cost, filtered_data)
            res = np.round(res.sort_values('Revenue', ascending=False), decimals=2)
            
            if opt_Revenue > 0:
                return [
                    res.to_dict('records'), fig_QuantityVsRevenue, fig_PriceVsQuantity, 
                    f'The maximum revenue of {opt_Revenue} is achieved by optimizing {var_opt} at {opt_Quantity}, with a fixed cost of {var_cost}. The optimization range was {var_range}.'
                ]
            else:
                return [
                    res.to_dict('records'), fig_QuantityVsRevenue, fig_PriceVsQuantity, 
                    f'For the fixed cost of {var_cost} and {var_opt} range between {var_range}, you will incur a loss in revenue.'
                ]
    except Exception as e:
        logging.exception('Something went wrong with interaction logic:')
        # Return default values in case of an exception
        return [
            [],  # Default empty list for heatmap data
            go.Figure(),  # Default empty figure for lineChart1
            go.Figure(),  # Default empty figure for lineChart2
            'An error occurred while processing the data.'  # Default message
        ]


app.run_server(debug=True)