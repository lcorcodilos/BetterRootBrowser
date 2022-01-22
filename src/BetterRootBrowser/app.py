import numpy as np
import plotly.graph_objects as go
import dash, sys
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import page, data, graph

max_height = "100vh"
max_width = ""

if __name__ == '__main__':
    
    dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.4/dbc.min.css"
    app = dash.Dash(__name__,
        external_stylesheets=[dbc.themes.FLATLY, dbc_css],
        external_scripts=[
            'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML',
        ]
    )

    # all_figs = open_file(sys.argv[1])#('~/CMS/temp/nano_4.root',pick_objs=['Events'])
    # rows_of_figs = figs_in_table(all_figs, ncols=3, nfigs=10)
    
    app.layout = dbc.Container(
        [
            page.header,
            page.file_path_input,
            # html.Div('', style={'flex': 1}),
            page.body,

            dbc.Alert("An app made by Lucas Corcodilos", color="primary", class_name='mb-0 rounded-0'),

            # html.Div(
            #     rows_of_figs
            # ),

        ], fluid=False, class_name="dbc p-2 m-0 d-flex",
        style={"height": "100vh", "width": "100vw", "max-width": "100%", "max-height": "100vh", "flex-flow": "column nowrap"}
    )

    app.run_server(debug=True)
