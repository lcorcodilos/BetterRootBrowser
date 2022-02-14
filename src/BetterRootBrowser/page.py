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

#---------------#
# Template form #
#---------------#
template_form = dbc.Modal(
    html.Div([
        html.Div(className='d-flex justify-content-between align-items-center mb-3 mt-2', children=[
            html.H5('Specify a scheme for identifying template sets.'),
            dbc.Button('Click for help', id='template-instructions-button', color='info', n_clicks=0),
        ]),
        dbc.Collapse(
            [
                html.P('Use the following keys to represent the hierarchical categories of your templates'),
                html.Ul(
                    [html.Li('$PROCESS - the process name such as "signal", "QCD", "data", etc.'),
                    html.Li('$REGION - the region name such as "signal", "control", "validation", etc.'),
                    html.Li('$SYSTEMATIC - the systematic uncertainty name such as "taggingSF", "JER", etc.')]
                ),
                html.H5('Example:', className='text-info'),
                html.P('Consider the following set of files and their contents'),
                html.Ul([
                    html.Li('Ttbar_16.root'),
                    html.Ul([
                        html.Li('hist_SR_nominal'),
                        html.Li('hist_CR_nominal'),
                        html.Li('hist_SR_tagggingSF_up'),
                        html.Li('hist_SR_tagggingSF_down')
                    ]),
                    html.Li('Signal_16.root'),
                    html.Ul([
                        html.Li('hist_SR_nominal'),
                        html.Li('hist_CR_nominal'),
                        html.Li('hist_SR_JER_up'),
                        html.Li('hist_SR_JER_down')
                    ])
                ]),
                html.P('For the nominal scheme, one would provide "$PROCESS.root:hist_$REGION_nominal".'),
                html.P('For the +1 std. dev. scheme, one would provide "$PROCESS.root:hist_$REGION_$SYSTEMATIC_up".'),
                html.P('For the -1 std. dev. scheme, one would provide "$PROCESS.root:hist_$REGION_$SYSTEMATIC_down".')
            ], id='template-instructions', is_open=False
        ),

        dbc.Form(
            [
                dbc.Input(type="text", placeholder="Nominal shape scheme", id="nominal-scheme", className='mb-2'),
                dbc.Input(type="text", placeholder="+1 std. dev. shape scheme", id="up-scheme", className='mb-2'),
                dbc.Input(type="text", placeholder="-1 std. dev. shape scheme", id="down-scheme", className='mb-2'),
                dbc.Button("Create", color="info")
            ]
        )
    ], className='mt-2 ms-3 me-3 mb-2'),
    id="template-util-modal", size="lg", is_open=False, className='h-25'
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
                dbc.Button(
                    'Template Utility', color='primary',
                    outline=True, n_clicks=0,
                    class_name='ms-2', style={'min-width': 'max-content'},
                    id='template-button', type='submit'
                ),
                template_form
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
    parent_style={'flex-flow': 'column nowrap', 'overflow': 'auto', 'width': '25%'}
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

def range_select(title, text, id, valrange):
    return dbc.DropdownMenu(
        [
            html.Div(
                [
                    html.P(text, className='m-auto ms-4'),
                    dbc.Button('Apply', color='primary',
                        outline=True, n_clicks=0,
                        class_name='m-auto me-4', 
                        id=f'{id}-button', type='submit')
                ], className='d-flex justify-content-between align-items-center'
            ),
            html.Div(
                    dcc.RangeSlider(
                        marks=valrange, min=min(valrange), max=max(valrange), step=None,
                        id=f'{id}-slider', allowCross=False,
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    className='mt-2',
                    style={'width': f'{len(valrange)}em'}
                )
            ], label=title, style={'min-width': 'max-content'}, className='m-auto ms-2 me-2', color='info'
    )

content_header_2D = lambda title, xrange, yrange: html.Div(
    [
        html.H5(title, className='flex-grow-1 m-auto'),
        range_select('X projection', 'Range of Y axis bins to consider', 'x-proj', {y:str(y) for y in yrange}),
        range_select('Y projection', 'Range of X axis bins to consider', 'y-proj', {x:str(x) for x in xrange})
    ], className='d-flex justify-content-between align-items-center mb-2'
)

