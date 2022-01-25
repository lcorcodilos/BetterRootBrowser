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
file_accordion = lambda file_accordion_items: dbc.Accordion(
    children=file_accordion_items,
    start_collapsed=True, flush=True,
    id='file-list'
)

file_accordion_item = lambda type_accordion, file_name, ifile: dbc.AccordionItem(
    children=type_accordion,
    title=file_name,
    item_id=f'file-{ifile}'
)

type_accordion = lambda type_accordion_items, ifile: dbc.Accordion(
    children=type_accordion_items,
    start_collapsed=True, flush=True,
    id=f'file-{ifile}-type-list'
)

type_accordion_item = lambda obj_radio, obj_type, ifile: dbc.AccordionItem(
    title=obj_type,
    item_id=f'file-{ifile}-type-{obj_type}',
    children=obj_radio
)

obj_radio_template = lambda index, opts: dbc.RadioItems(
    id={'id': index, 'type': 'obj-radio'},
    style={'display': 'flex', 'flex-flow': 'column nowrap', 'width': 'max-content'},
    class_name='btn-group',

    input_class_name='btn-check',
    input_style={},

    label_class_name='btn btn-outline-primary border-0 border-top rounded-0',
    label_style={'text-align': 'left', 'width': 'inherit'},

    label_checked_class_name='active',
    options=opts,
    value=None
)

file_info_pane = html.Div(
    file_accordion([]),
    id='file-list-container',
    className='pe-4 d-flex',
    style={'flex-flow': 'column nowrap', 'overflow': 'auto', 'width': '30%'}
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