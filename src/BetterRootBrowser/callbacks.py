import logging, dash
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import os, data, json, graph
import numpy as np

text_color_classes = [
    "text-primary", "text-secondary",
    "text-success", "text-danger",
    "text-warning", "text-info", 
    "text-light", "text-dark"
]

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:  %(message)s')

def get_id_of_trigger():
    # dash.callback_context.triggered[0] looks like
    # {'prop_id': '{"id":"obj-MthvMh_deepTag_SR_pass__nominal","type":"obj-button"}.n_clicks', 'value': 1}
    trigger = dash.callback_context.triggered[0]
    trigger = trigger['prop_id'].split('}')[0]+'}'
    return json.loads(trigger)['id']

def remove_text_color_class(class_str):
    classes = class_str.split()
    out = []
    for classname in classes:
        if classname not in text_color_classes:
            out.append(classname)
    return ' '.join(out)

def NumpySerialize(obj):
    if type(obj).__module__ == np.__name__:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj.item()
    raise TypeError('Unknown type:', type(obj))

def assign(app):
    # On open button press, grab file path, set valid + invalid flags, set open message
    @app.callback(
        inputs=dict(
            click_flag=Input('file-open-button', 'n_clicks'),
            file_path=State('file-path','value'),
            file_open_msg_class=State('file-open-msg', 'className')
        ),
        output=[
            Output('file-path', 'valid'),
            Output('file-path', 'invalid'),
            Output('file-open-msg', 'children'),
            Output('file-open-msg', 'className')
        ])
    def check_for_file_on_button_click(click_flag, file_path, file_open_msg_class):
        valid, invalid, msg, msg_class = False, False, '', ''
        if click_flag == 0:
            return valid, invalid, msg, msg_class

        file_path = os.path.abspath(os.path.expanduser(file_path.strip()))
        file_title = file_path.split('/')[-1]
        if os.path.isfile(file_path):
            valid = True
            msg = f"Successfully opened {file_title}'!"
            msg_class = remove_text_color_class(file_open_msg_class)+' text-success'
        else:
            invalid = True
            msg = f"Error: Could not open {file_path}'!"
            msg_class = remove_text_color_class(file_open_msg_class)+' text-danger'
        
        return valid, invalid, msg, msg_class

    # On file-path valid, open file and display name + list of objects
    @app.callback(
        inputs=dict(
            file_valid=Input('file-path', 'valid'),
            file_path=State('file-path','value'),
        ),
        output=[Output('file-title','children'), Output('obj-list','options'), Output('root-objs', 'data')]
    )
    def load_file(file_valid, file_path):
        if file_valid:
            file_title = file_path.strip().split('/')[-1]
            file_objs = data.open_file(file_path)

            obj_names = [obj_name for obj_name in file_objs.keys()]

            logging.debug(f"Objects in file: {', '.join(obj_names)}")

            obj_button_list = [
                # dbc.ListGroupItem(
                #     obj['name'], id=obj['name'],
                #     class_name='text-secondary',
                #     action=True, active=False
                # ) for obj in file_objs
                {"label": n, 'value': n} for n in obj_names
            ]

            return file_title, obj_button_list, json.dumps(file_objs, default=NumpySerialize)

        else:
            return '', [], []

    @app.callback(
        inputs=dict(
            obj_selected = Input('obj-list', 'value'),
            root_objs = State('root-objs', 'data')
        ),
        output=Output('display-area', 'children'),
        prevent_initial_call=True
    )
    def display_obj(obj_selected, root_objs):
        numpy_data = json.loads(root_objs)[obj_selected]

        out = [
            dash.html.H5(obj_selected),
            graph.make_heatmap(numpy_data)
        ]
        return out 

    
