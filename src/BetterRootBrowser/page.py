from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

header = html.Div(
    [
        html.H1(
            'Better ROOT Browser', className='float-start'
        ),

        html.Div([
            html.H5('A Dash app for'),
            html.H5('inspecting ROOT files.')], className='float-end'
        ),
    ], id='header', className='d-flex justify-content-between align-items-center bg-light p-4 mb-3'
)

footer = dbc.Alert(
    'An app made by Lucas Corcodilos',
    color='primary', class_name='mb-0 rounded-0',
    id='footer'
)

##############
# File input #
##############
file_path_input = html.Div([
        html.Div(
            [
                dbc.Input(value='~/CMS/BoostedTH/rootfiles/THselection_QCD_16.root',placeholder='Path to ROOT file...', valid=False, invalid=False, class_name='flex-grow-5', id='file-path'),
                dbc.Button('Open', color='primary', outline=True, n_clicks=0, class_name='ms-2 flex-grow-1', id='file-open-button', type='submit'),
            ], className='d-flex mb-1'
        ),
        html.P('', id='file-open-msg', className='ms-2 mb-0')
    ], id='file-path-div'
)

########
# Body #
########
#-----------#
# Left pane #
#-----------#
obj_list = dbc.RadioItems(
    id='obj-list',
    style={'display': 'flex', 'flex-flow': 'column nowrap', 'width': 'max-content'},
    class_name='btn-group',

    input_class_name='btn-check',
    input_style={},

    label_class_name='btn btn-outline-primary border-0 border-top rounded-0',
    label_style={'text-align': 'left', 'width': 'inherit'},

    label_checked_class_name='active',
    options=[],
    value=None
)

file_info_pane = html.Div(
    [
        html.P('', id='file-title'),
        html.Div(obj_list, style={'overflow': 'auto'})
    ],
    id='file-info-pane',
    className='pe-4 pt-2 d-flex',
    style={'flex-flow': 'column nowrap', 'overflow': 'hidden', 'width': '30%'}
)

#------------#
# Right pane #
#------------#
display_area = html.Div(
    ['Open a file and select an object from the left to display something'],
    className='pt-2 ps-4 border-start w-100 h-100',
    id='display-area'
)

#-----------#
# Content body #
#-----------#
content_body = html.Div(
    [
        file_info_pane,
        display_area
    ],
    className='d-flex border-top mt-1 pb-2',
    id='content-body',
    style={'flex': 1, 'height': '100%', 'overflow': 'hidden'}
)