import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash, uproot, sys
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from data import open_file
from graph import figs_in_table


if __name__ == '__main__':
    
    dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css"
    app = dash.Dash(__name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css],
        external_scripts=[
            'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML',
        ]
    )

    all_figs = open_file(sys.argv[1])#('~/CMS/temp/nano_4.root',pick_objs=['Events'])
    rows_of_figs = figs_in_table(all_figs, ncols=3, max_figs=10)
    

    app.layout = dbc.Container(
        [
            html.H1(
                'BRowser (Better ROOT Browser)',
            ),

            html.Div(
                'Dash: A web application framework for your data.',
            ),

            html.Div(
                rows_of_figs
            ),

        ], fluid=True, className="dbc"
    )

    app.run_server(debug=True)
