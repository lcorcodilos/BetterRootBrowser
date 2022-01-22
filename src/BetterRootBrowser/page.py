from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

header = html.Div(
    [
        html.H1(
            "Better ROOT Browser", className="float-start"
        ),

        html.Div([
            html.H5("A Dash app for"),
            html.H5("inspecting ROOT files.")], className="float-end"
        ),
    ], className="d-flex justify-content-between align-items-center bg-light p-4 mb-3"
)

file_path_input = html.Div([
    html.Div(
        [
            dbc.Input(placeholder="Path to ROOT file...", valid=False, invalid=False, class_name="flex-grow-5"),
            dbc.Button('Open', color='primary', outline=True, n_clicks=0, class_name='ms-2 flex-grow-1'),
        ], className="d-flex mb-1"
    ),
    html.P('Test warning', id='file-open-error', className='ms-2 mb-0 text-danger') #'ERROR: Could not open file.'
])

obj_list = dbc.ListGroup(
    [
        dbc.ListGroupItem(f"Obj{i}", id=f"obj{i}-button", class_name="text-secondary", action=True, active=False) for i in range(100)
    ],
    class_name='', flush=True, style={"overflow-x": "scroll"}
)

file_info_pane = html.Div(
    [
        html.P('Filename.root', id='file-title'),
        obj_list
    ],
    className='pe-4 w-25 pt-2 d-flex',
    style={"flex-flow": "column nowrap", "overflow": "hidden"}
)

display_area = html.Div(
    ['This is the main content area'],
    className='pt-2 ps-4 border-start'
)

body = html.Div(
    [
        file_info_pane,
        display_area
    ],
    className='d-flex border-top mt-1 pb-2',
    style={"flex": 1, "max-height": "100%", "overflow": "hidden"}
)