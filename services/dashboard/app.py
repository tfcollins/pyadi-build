from dash import Dash, html, dcc, callback, Output, Input, dash_table, _dash_renderer
import dash_bootstrap_components as dbc

import plotly.express as px
import pandas as pd
import datetime
import json

# df = pd.read_csv(
#     "https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv"
# )
# Import json
filename = "hdl_metadata.json"
with open(filename, "r") as f:
    data = json.load(f)

# print(data.keys())

## Flatten json data
data_filtered = []
for key, value in data.items():
    builds_per_date: dict = value
    dates = list(builds_per_date.keys())
    if len(dates) == 0:
        continue
    print(builds_per_date[dates[0]])
    commit = builds_per_date[dates[0]]["git_sha"][0]

    data_filtered.append({"board": key, "commit": commit, "date": dates[0]})

data = data_filtered



filter_base = [1, 2, 3]

table = data

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = [
    html.H1(children="Title of Dash App", style={"textAlign": "center"}),
    # dcc.Dropdown(df.country.unique(), 'Canada', id='dropdown-selection'),
    html.Div(
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    [
                        dcc.Dropdown(filter_base, "1", id="dropdown-selection"),
                    ]
                ),
            ]
        ),
    ),
    html.Div(
        id="table",
        children=dash_table.DataTable(
            id="table-content",
            columns=[{"name": i, "id": i} for i in table[0].keys()],
            data=data,
        ),
    ),
]


@callback(
    # Output('graph-content', 'figure'),
    Output("table-content", "data"),
    Input("dropdown-selection", "value"),
)
def update_graph(value):
    # dff = df[df.country==value]
    # return px.line(dff, x='year', y='pop')
    print(value)

    # if value == None:
    return table

    value = int(value)

    filtered_table = []
    # filter out the table data if not a multiple of the selected value
    for i in range(10):
        if i % value == 0:
            filtered_table.append({"index": i, "square": i**2, "cube": i**3})

    return filtered_table


if __name__ == "__main__":
    app.run(debug=True, port=8055, host="0.0.0.0")
