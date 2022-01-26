import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

'''Helpers'''
def edges_to_centers(x):
    return np.array([
        (x[i]+x[i+1])/2 for i in range(len(x)-1)
    ])

'''Standard plot makers'''
def make_display(obj_pkg):
    if isinstance(obj_pkg['data'], str):
        return obj_pkg['data']
    if obj_pkg['type'] == 'TTree':
        return make_table(obj_pkg)
    elif obj_pkg['type'].startswith('TH1'):
        return make_1D(obj_pkg)
    elif obj_pkg['type'].startswith('TH2'):
        return make_heatmap(obj_pkg)
    else:
        return html.Div(f'Object type {obj_pkg["type"]} is not currently supported.')

def make_heatmap(hist_pkg):
    try:
        z,x,y = hist_pkg['data']
    except Exception as e:
        print ('DEBUG: %s'%hist_pkg)
        raise e

    z = np.transpose(z)
    x = edges_to_centers(x)
    y = edges_to_centers(y)

    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.8, 0.2],
        row_heights=[0.2, 0.8],
        specs=[
            [ {"type": "bar"}, None],
            [ {"type": "heatmap"}, {"type": "bar"}]
        ],
        shared_xaxes=True, shared_yaxes=True,
        horizontal_spacing=0.01, vertical_spacing=0.01,
    )
    
    fig.add_trace(
        go.Bar(
           x=z.sum(axis=1), y=y, orientation="h",
           marker=dict(color=z.sum(axis=1), coloraxis="coloraxis2")
        ), row=2, col=2
    )

    fig.add_trace(
        go.Bar(
           x=x, y=z.sum(axis=0),
           marker=dict(color=z.sum(axis=0), coloraxis="coloraxis3")
        ), row=1, col=1
    )

    fig.add_trace(
        go.Heatmap(
            z=z, x=x, y=y,
            coloraxis="coloraxis",
            xaxis='x2'
        ), row=2, col=1
    )

    load_figure_template("bootstrap")
    fig.update_layout(
        coloraxis=dict(colorscale='thermal'),
        coloraxis2=dict(colorscale='thermal', showscale=False),
        coloraxis3=dict(colorscale='thermal', showscale=False),
        showlegend=False,
        template="bootstrap",
        autosize=True
    )

    fig.layout.xaxis2.title = dict(
        text = hist_pkg['xtitle']
    )
    fig.layout.yaxis2.title = dict(
        text = hist_pkg['ytitle']
    )

    fig.layout.xaxis2.tickfont.size = 16
    fig.layout.yaxis2.tickfont.size = 16
    fig.layout.margin.l = 40
    fig.layout.margin.r = 100
    fig.layout.margin.t = 15

    # fig.write_html("plot.html")
    return dcc.Graph(
        id=hist_pkg['name'],
        figure=fig,
        style={'width': '90%', 'height': '90%'}
    )

def make_1D(hist_pkg):
    try:
        y,x = hist_pkg['data']
    except Exception as e:
        print ('DEBUG: %s'%hist_pkg)
        raise e

    x = edges_to_centers(x)

    load_figure_template("sandstorm")
    return dcc.Graph(
        id=hist_pkg['name'],
        figure=go.Figure(go.Bar(
            x=x, y=y,
            marker=dict(color=sum(y), coloraxis="coloraxis")
        )),
        style={'width': '90%', 'height': '90%'}
    )

def make_table(array_pkg):
    df = array_pkg['data']
    df = df.iloc[:100,:4]
    column_names = df.columns.to_list()
    return dash_table.DataTable(
        id='table',
        data=df.to_dict('records'),
        columns=[{'name':name, 'id':f'col-{name}'} for name in column_names]
    )

'''Layout tools'''
def figs_in_grid(figlist, ncols=3, nfigs=None):
    if nfigs is None:
        nfigs = len(figlist)

    partitioned_figs = [figlist[i: min(i+ncols, nfigs)] for i in range(0, nfigs, ncols)]

    rows_of_figs = [
        dbc.Row(
            [dbc.Col(fig) for fig in row]
        ) for row in partitioned_figs
    ]

    return rows_of_figs