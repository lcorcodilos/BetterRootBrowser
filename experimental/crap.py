class BrowserPaneAIO(dash.html.Div):

    class ids:
        button = lambda aio_id: {
            'component': 'BrowserPaneAIO',
            'subcomponent': 'button',
            'aio_id': aio_id
        }

        file_name = lambda aio_id: {
            'component': 'BrowserPaneAIO',
            'subcomponent': 'file_name',
            'aio_id': aio_id
        }

    ids = ids

    def __init__(self, file_title: str = '', obj_names: List[str] = [], button_props: Dict={}, aio_id: Union[str, None] = None):
        if aio_id is None:
            aio_id = str(uuid.uuid4())

        b_props = dict(
            color="primary", className="m-1 border-0", outline=True
        )
        b_props.update(button_props)

        super().__init__(
            [dash.html.P(file_title, id='file-title')]+[
                dbc.Button(
                    children=n, id='obj-'+n,
                    n_clicks=0, active=False, **b_props
                ) for n in obj_names
            ]
        )

    @dash.callback(
        input=dict(
            clicks=Input(ids.button(MATCH), 'n_clicks'),
            button_id=Input(ids.button(MATCH), 'aio_id')
        ),
        output=[Output(ids.buttons(ALL), 'active')]
    )
    def set_active(self, n_clicks, aio_id):
        for button in self.children:
            if 


# def contract_dict(in_d: Dict, layer: int = 0) -> Dict:
    #     out_d = {}
    #     logging.debug(f'{layer} input: {in_d}')

    #     if in_d == {}:
    #         return None
    #     elif len(in_d) == 1:
    #         d_tuple = list(in_d.items())[0]
    #         if isinstance(d_tuple[1], dict):
    #             if d_tuple[1] == {}:
    #                 return d_tuple[0]
    #             else:

    #         return '-'.join(
    #             list(in_d.items())[0]
    #         )
    #     else:
    #         for in_k, in_v in in_d.items():
    #         return contract_dict(list(v.values())[0], layer=layer+1)


    #     for in_k, in_v in in_d.items():
    #         out[d]
    #         if isinstance(v, dict):
    #             if len(v) == 0:
    #                 continue
    #             elif len(v) == 1:
    #                 if list(v.values())[0] == {}:
    #                     newval = list(v.keys())[0]
    #                 else:
    #                     newkey += list(v.keys())[0]
    #                     newval = contract_dict(list(v.values())[0], layer=layer+1)#v.values()[0]

    #         newd[newkey] = newval    

    #     logging.debug(f'{layer} output: {newd}')

    #     return newd

def dict_width(grouping: Dict) -> int:
    if isinstance(grouping, dict):
        width = sum([dict_width(v) for v in grouping.values()])
    else:
        width = 1
    return width

def dict_depth(grouping: Dict) -> int:
    if isinstance(grouping, dict):
        nested_depths = [dict_depth(v)+1 for v in grouping.values() if isinstance(v,dict)]
        if nested_depths == []:
            depth = 1
        else:
            depth = max(nested_depths)
    else:
        depth = 1
    return depth

def metric(grouping: Dict) -> int:
    return dict_depth(grouping) * dict_depth(grouping)

def token_grouper(list_of_tokens):
    def scores(lot):
        scores = []
        ncols = lot.shape[1]
        for icol in range(lot.shape[1]):
            scores.append(len( set(lot[:,icol]) ))
            
        return np.array(scores)

    def score(lot):
        return sum(list(scores(lot)))

    def entropy(lot):
        out = 0
        for icol in range(lot.shape[1]):
            counter = Counter(lot[:,icol])
            # del counter['']
            sum_counts = sum([v for v in counter.values()])
            probs = [count/sum_counts for count in counter.values()]
            out += sum(-p*math.log(p) for p in probs)
        return out/lot.shape[1]

    def keep_change(lot, prev_lot):
        logging.debug(f'{entropy(lot)} -> {entropy(prev_lot)}')
        return entropy(lot) < entropy(prev_lot)

    

    icol = 0
    for _ in range(5):
        while icol < max_tokens-1:
            change_made = False
            new_lot = list_of_tokens.copy()
            new_lot[:,icol] = [f'{a}-{b}' for a,b in zip(new_lot[:,icol], new_lot[:,icol+1])]

            new_lot = np.delete(new_lot, icol+1, 1)
            if all([elem == '' for elem in new_lot[:,-1]]):
                new_lot = np.delete(new_lot, -1, 1)

            logging.debug('-----------------Test whole column-----------------')
            logging.debug(new_lot)
            if keep_change(new_lot, list_of_tokens): # score improved
                list_of_tokens = new_lot.copy()
                max_tokens = max([len(tkns) for tkns in list_of_tokens])
                logging.debug('### Combining full column')
                logging.debug(list_of_tokens)
                change_made = True

            logging.debug('-----------------------------------------------')
            
            for itkn in range(len(list_of_tokens)):
                new_lot = list_of_tokens.copy()
                tkns = list_of_tokens[itkn].copy()
                if tkns[icol] == '':
                    continue

                tkns[icol] = tkns[icol]+tkns[icol+1]
                tkns = np.delete(tkns, icol+1, axis=0)
                tkns = np.append(tkns, [''], axis=0)

                new_lot[itkn,:] = tkns

                logging.debug('-----------------Test single cells-----------------')
                logging.debug(new_lot)
                if all([elem == '' for elem in new_lot[:,-1]]):
                    new_lot = np.delete(new_lot, -1, 1)

                if keep_change(new_lot, list_of_tokens): # score improved
                    list_of_tokens = new_lot
                    max_tokens = max([len(tkns) for tkns in list_of_tokens])
                    logging.debug('## Combining two cells')
                    logging.debug(list_of_tokens)
                
                logging.debug('---------------------------------------------')
            
            if not change_made:
                icol+=1

    print(list_of_tokens)

