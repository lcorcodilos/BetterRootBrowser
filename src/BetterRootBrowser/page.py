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
                dbc.Input(
                    value='~/CMS/temp/nano_4.root',
                    placeholder='Path to ROOT file...',
                    valid=False, invalid=False,
                    class_name='flex-grow-5', id='file-path'
                ),
                dbc.Button(
                    'Open', color='primary',
                    outline=True, n_clicks=0,
                    class_name='ms-2 flex-grow-1', 
                    id='file-open-button', type='submit'
                ), 
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
    children=sorted(file_accordion_items, key=lambda item: item.title),
    start_collapsed=True, flush=True,
    id='file-list'
)

file_accordion_item = lambda type_accordion, file_name, ifile: dbc.AccordionItem(
    children=type_accordion,
    title=file_name,
    item_id=f'file-{ifile}'
)

type_accordion = lambda type_accordion_items, ifile: dbc.Accordion(
    children=sorted(type_accordion_items, key=lambda item: item.title),
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

file_info_pane = dcc.Loading(
    html.Div(
        file_accordion([]),
        id='loaded-browser',
        className='pe-4 d-flex',
    ),
    id="file-browser-container",
    parent_className='d-flex',
    type='default',
    parent_style={'flex-flow': 'column nowrap', 'overflow': 'auto', 'min-width': '15%', 'width': 'max-content', 'max-width': '25%'}
)


#------------#
# Right pane #
#------------#
display_area = dcc.Loading(
    html.Div(
        'Open a file and select an object from the left to display something',
        id='loaded-content',
        className='d-flex pt-2 ps-4 border-start flex-grow-1',
        style={'overflow':'hidden','height': '100%', 'width': '100%', 'flex-flow': 'column nowrap'}
    ),
    id='display-area',
    type="default",
    parent_className='d-flex flex-grow-1',
    parent_style={'min-width':0, 'min-height': 0} # makes sure tables dont overflow
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
    style={'flex': 1, 'height': '100%', 'width': '100%', 'overflow': 'hidden'}
)