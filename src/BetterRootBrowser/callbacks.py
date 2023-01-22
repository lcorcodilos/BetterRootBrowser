from collections import defaultdict
from functools import reduce
import logging, dash, copy
from re import template
import math
from dash.dependencies import Input, Output, State, ALL
import plotly.graph_objects as go
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

def get_id_of_trigger(nested=True):
    # dash.callback_context.triggered[0] looks like
    # {'prop_id': '{"id":"obj-MthvMh_deepTag_SR_pass__nominal","type":"obj-button"}.n_clicks', 'value': 1}
    if nested:
        trigger = dash.callback_context.triggered[0]
        trigger = trigger['prop_id'].split('.')[0]
        return json.loads(trigger)['id']
    else:
        trigger = dash.callback_context.triggered[0]
        return trigger['prop_id'].split('.')[0]

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

_scheme_keys = ['$PROCESS', '$REGION', '$SYSTEMATIC']

def chunk_scheme(scheme_str, variation=False):
    out = []
    to_split = scheme_str
    keys = copy.copy(_scheme_keys)
    if not variation:
        keys.pop(-1)
    
    for k in keys:
        l = to_split.split(k,1)
        if len(l) <= 1:
            raise IndexError(f'Could not find key {k}')
        if l[0] != '': out.append(l[0])
        out.append(k)
        to_split = l[1]

    out.append(to_split)
    return out

def extract_from_scheme(in_name, scheme):
    out = {}
    name = in_name.split('/')[-1]
    for ipiece, piece in enumerate(scheme):
        if not name.startswith(piece) and (piece not in _scheme_keys):
            return None
        if ipiece+1 < len(scheme):
            next_piece = scheme[ipiece+1]
        else:
            next_piece = ''
        
        if piece in _scheme_keys:
            if next_piece != '':
                out[piece] = name[:name.find(next_piece)]
                name = name[name.find(next_piece):]
            else:
                out[piece] = name
                name = ''
        else:
            name = name[len(piece):]
    
    return out

def solve_quad(low, mid, high):
    # A = [[x_1^2, x_1, 1],
    #      [x_2^2, x_2, 1],
    #      [x_3^2, x_3, 1]]
    # X = [[a],[b],[c]]
    # B = [[y_1], [y_2], [y_3]]
    if not any([low, mid, high]):
        return np.array([0,0,1])

    A = np.array([[1,-1,1],[0,0,1],[1,1,1]]) # x_1 = -1, x_2 = 0, x_3 = 1
    B = np.array([[y] for y in [low, mid, high]])

    out = [x[0] for x in np.linalg.solve(A,B)]
    if mid > 0:
        out = [v/mid for v in out]+[1] # add extra flag to indicate if this is a multiplicative factor
    else:
        out = out+[0] # or additive
    
    return np.array(out)

solve_quad_vect = np.vectorize(solve_quad, otypes=[np.ndarray])

def linear_extrap(x,y,quad_params):
    a,b,_,flag = quad_params
    slope = 2*a*x + b
    const = -1*slope*x + y
    return [slope, const, flag]

linear_extrap_vect = np.vectorize(linear_extrap, otypes=[np.ndarray])

def apply_quad(x, params):
    return params[0]**2*x + params[1]*x + params[2]
apply_quad_vect = np.vectorize(apply_quad, excluded=['x'], otypes=[float], signature='(),(i,j),(i)->()')

def apply_lin(x, params):
    return params[0]*x + params[1]
apply_lin_vect = np.vectorize(apply_lin, excluded=['x'], otypes=[float])

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
            click_flag=Input('file-open-button', 'n_clicks')
        ),
        output=[
            Output('template-open-first-msg', 'hidden'),
            Output('template-form', 'hidden')
        ]
    )
    def allow_template_util(click_flag):
        if click_flag:
            return True, False
        return False, True

    @app.callback(
        inputs=dict(
            objs = Input({'id': ALL, 'type': 'obj-radio'}, 'value'),
            file_id = State('file-list', 'active_item'),
            file_paths = State('file-paths', 'data'),
            template_btn=Input('template-form-submit', 'n_clicks'),
            nom_str=State('nominal-scheme', 'value'),
            up_str=State('up-scheme', 'value'),
            down_str=State('down-scheme', 'value'),
            hist_type=State('hist-type', 'value')
        ),
        output=[Output('display-area', 'children'), Output('template-data-map','data')],
        prevent_initial_call=True,
        # suppress_callback_exceptions=True
    )
    def load_content(objs, file_id, file_paths, template_btn, nom_str, up_str, down_str, hist_type):
        triggered = get_id_of_trigger(False)
        if triggered == 'template-form-submit':
            return display_template_util(nom_str, up_str, down_str, file_paths, hist_type)
        else:
            return just_display(objs, file_id, file_paths), {}

    def just_display(objs, file_id, file_paths):
        if not any(objs):
            return []

        file_paths = json.loads(file_paths)
        obj_selected = dash.callback_context.triggered[0]['value']
        data_to_display = data.extract_from_file(file_paths[file_id], obj_selected)

        if data_to_display['type'].startswith('TH2'):
            header = page.content_header_2D(obj_selected, data_to_display.xrange, data_to_display.yrange)
        else:
            header = dash.html.H5(obj_selected)

        out = page.just_display([
            header,
            graph.make_display(data_to_display)
        ], '')
        return out

    def display_template_util(nom_str, up_str, down_str, file_paths, hist_type):
        file_paths = json.loads(file_paths).values()
        if hist_type == 1:
            hist_type = 'TH1'
        elif hist_type == 2:
            hist_type = 'TH2'
        else:
            raise ValueError('Hist type not supported.')
        
        hist_map = {}
        for fstr in file_paths:
            hist_map[fstr] = [obj['name'] for obj in data.get_file_info(fstr).values() if hist_type in obj['type']]

        hist_paths = [f'{f}:{h}' for f in hist_map.keys() for h in hist_map[f]]
        data_map = defaultdict(lambda: defaultdict(dict))
        nom_scheme = chunk_scheme(nom_str)
        up_scheme = chunk_scheme(up_str, True)
        down_scheme = chunk_scheme(down_str, True)

        for h in hist_paths:
            hdict = extract_from_scheme(h, nom_scheme)
            if hdict is not None:
                data_map[hdict['$PROCESS']][hdict['$REGION']]['nominal'] = data.extract_from_file(*h.split(':'))
            else:
                hdict = extract_from_scheme(h, up_scheme)
                if hdict is not None:
                    data_map[hdict['$PROCESS']][hdict['$REGION']][hdict['$SYSTEMATIC']+'-up'] = data.extract_from_file(*h.split(':'))
                else:
                    hdict = extract_from_scheme(h, down_scheme)
                    if hdict is not None:
                        data_map[hdict['$PROCESS']][hdict['$REGION']][hdict['$SYSTEMATIC']+'-down'] = data.extract_from_file(*h.split(':'))

        # template_map = {}
        # for p in data_map:
        #     template_map[p] = {}
        #     for r in data_map[p]:
        #         template_map[p][r] = {}
        #         systematics = data.unique_systematics(data_map[p][r].keys())
        #         template_map[p][r]['nominal'] = data_map[p][r]['nominal']
        #         template_map[p][r]['systematics'] = systematics

        #         template_map[p][r]['interp_params'] = {syst:solve_quad_vect(
        #             data_map[p][r][f'{syst}-down']['data'][0],
        #             template_map[p][r]['nominal']['data'][0],
        #             data_map[p][r][f'{syst}-up']['data'][0]
        #         ) for syst in systematics}

        #         pp.pprint(template_map[p][r]['interp_params'])

        #         template_map[p][r]['extrap_low_params'] = {syst:linear_extrap_vect(
        #             -1, data_map[p][r][f'{syst}-down']['data'][0], template_map[p][r]['interp_params'][syst]
        #         ) for syst in systematics}

        #         template_map[p][r]['extrap_high_params'] = {syst:linear_extrap_vect(
        #             1, data_map[p][r][f'{syst}-up']['data'][0], template_map[p][r]['interp_params'][syst]
        #         ) for syst in systematics}

        return page.template_util_body(sorted(data_map.keys()), hidden=False), data_map

    @app.callback(
        Output("template-util-modal", "is_open"),
        Input("template-button", "n_clicks"),
        Input("template-form-submit", "n_clicks"),
        State("template-util-modal", "is_open"),
    )
    def open_template_util(btn, submit_btn, is_open):
        if btn or submit_btn:
            return not is_open
        return is_open

    @app.callback(
        Output('template-instructions', 'is_open'),
        Input("template-instructions-button", "n_clicks"),
        State("template-instructions", "is_open"),
    )
    def open_template_instructions(btn, is_open):
        if btn:
            return not is_open
        return is_open

    @app.callback(
        inputs=dict(
            process=Input('process-select', 'value'),
            template_map=State('template-data-map', 'data')
        ),
        output=[Output('region-select', 'options'), Output('region-select', 'value')],
        prevent_initial_call=True
    )
    def populate_template_regions(process, template_map):
        return [{'label': region, 'value': region} for region in ['']+sorted(template_map[process].keys())], ''

    @app.callback(
        inputs=dict(
            process=State('process-select', 'value'),
            region=Input('region-select', 'value'),
            template_map=State('template-data-map', 'data')
        ),
        output=[Output('template-loaded-content', 'children'), Output('template-sliders', 'children')],
        prevent_initial_call=True
    )
    def display_template(process, region, template_map):
        if region == '':
            return [], []

        nominal_obj = template_map[process][region]['nominal']
        syst_keys = data.unique_systematics(template_map[process][region].keys())
        return graph.make_display(nominal_obj), page.template_sliders_gen(syst_keys)

    @app.callback(
        inputs=dict(
            process=State('process-select', 'value'),
            region=State('region-select', 'value'),
            template_map=State('template-data-map', 'data'),
            fig=State('rendered-graph', 'figure'),
            sliders=Input({'id': ALL, 'type': 'template-slider'}, 'value')
        ),
        output=Output('rendered-graph', 'figure'),
        prevent_initial_call=True
    )
    def morph_w_sliders(process, region, template_map, fig, sliders):
        template = template_map[process][region]
        full = copy.deepcopy(template['nominal']['data'][0])
        for i,syst in enumerate(data.unique_systematics(template.keys())):
            full += morph_amount_vect(
                sliders[i], full,
                template['nominal']['data'][0],
                template[f'{syst}-up']['data'][0],
                template[f'{syst}-up']['data'][0]
            )

        return graph.update_heatmap(fig, full)

    def morph_amount(a, f, n, u, d):
        if a >= 0:
            if n > 0:
                if u > 0:
                    return f * ((u/n)**a - 1)
                else:
                    return max(-n*a + n, 0)
            else:
                if u > 0:
                    return max(u*a, 0)
                else:
                    return 0
        else:
            if n > 0:
                if d > 0:
                    return f * ((d/n)**(-1*a) - 1)
                else:
                    return max(n*a + n, 0)
            else:
                if d > 0:
                    return max(-d*a, 0)
                else:
                    return 0

    morph_amount_vect = np.vectorize(morph_amount, excluded=['a'])