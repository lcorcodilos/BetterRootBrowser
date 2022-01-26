import logging, dash
from tokenize import group
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import os, json
from BetterRootBrowser import data, graph, page
import numpy as np
import pandas as pd
from glob import glob
from pprint import PrettyPrinter

pp = PrettyPrinter(indent=4)

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

def unpack_file_paths(file_path_str):
    # first split by comma
    file_paths = [p.strip() for p in file_path_str.split(',')]
    found, missing = [], []
    for path in file_paths:
        abs_path = os.path.abspath(os.path.expanduser(path))
        
        if '*' not in abs_path:
            if os.path.isfile(abs_path):
                found.append(abs_path)
            else:
                missing.append(abs_path)

        else:
            globbed_paths = glob(abs_path)
            if len(globbed_paths) == 0:
                missing.append(abs_path)
            else:
                found.extend(globbed_paths)

    return found, missing

def remove_text_color_class(class_str):
    classes = class_str.split()
    out = []
    for classname in classes:
        if classname not in text_color_classes:
            out.append(classname)
    return ' '.join(out)

def NumpyPandasSerialize(obj):
    if type(obj).__module__ == np.__name__:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj.item()
    elif isinstance(obj, pd.core.frame.DataFrame):
        return obj.to_json(orient='records')

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
            Output('loaded-browser', 'children'),
            Output('file-open-msg', 'children'),
            Output('file-open-msg', 'className'),
            Output('file-paths', 'data')
        ])
    def check_for_file_on_button_click(click_flag, file_path, file_open_msg_class):
        valid, invalid, msg, msg_class = False, False, '', file_open_msg_class
        if click_flag == 0:
            return [], msg, msg_class, ''

        found_files, missing_files = unpack_file_paths(file_path)
        if len(found_files) > 0:
            valid = True
            file_titles = ', '.join(f.split('/')[-1] for f in found_files)
            success_msg = f"Successfully opened all files!"

        if len(missing_files) > 0:
            invalid = True
            file_titles = ', '.join(f.split('/')[-1] for f in missing_files)
            fail_msg = f"Error: Could not open {file_titles}!"
            print('Not able to find file paths:\n\t%s'%",\n\t".join(missing_files))

        if invalid:
            msg = fail_msg
            msg_class = remove_text_color_class(file_open_msg_class)+' text-danger'
        elif valid:
            msg = success_msg
            msg_class = remove_text_color_class(file_open_msg_class)+' text-success'
        else:
            msg = ''
            msg_class = file_open_msg_class
        
        file_accordion_items = []
        file_paths = {}
        for ifile, file_name in enumerate(found_files):
            open_file = data.get_file_info(file_name)
            grouped_names = {}
            for obj_name, obj in open_file.items():
                if obj['type'] not in grouped_names.keys():
                    grouped_names[obj['type']] = []
                grouped_names[obj['type']].append(obj_name)

            type_accordion_items = []
            for obj_type, obj_names in grouped_names.items():
                obj_radio = page.obj_radio_template(
                    f'file-{ifile}-type-{obj_type}-radio',
                    [ {'label': n, 'value':n} for n in sorted(obj_names) ]
                )

                type_accordion_items.append(
                    page.type_accordion_item(
                        obj_radio, obj_type, ifile
                    )
                )

            type_accordion = page.type_accordion(
                type_accordion_items, ifile
            )

            file_accordion_items.append(
                page.file_accordion_item(type_accordion, file_name.split('/')[-1], ifile)
            )

            file_paths[f'file-{ifile}'] = file_name

        file_accordion = page.file_accordion(file_accordion_items)

        return file_accordion, msg, msg_class, json.dumps(file_paths)#, json.dumps(data_loaded, default=NumpyPandasSerialize)

    @app.callback(
        inputs=dict(
            objs = Input({'id': ALL, 'type': 'obj-radio'}, 'value'),
            file_id = State('file-list', 'active_item'),
            file_paths = State('file-paths', 'data')
        ),
        output=Output('loaded-content', 'children'),
        prevent_initial_call=True,
        # suppress_callback_exceptions=True
    )
    def display_obj(objs, file_id, file_paths):
        if not any(objs):
            return []

        file_paths = json.loads(file_paths)
        obj_selected = dash.callback_context.triggered[0]['value']
        data_to_display = data.extract_from_file(file_paths[file_id], obj_selected)

        out = [
            dash.html.H5(obj_selected),
            graph.make_display(data_to_display)
        ]
        return out 