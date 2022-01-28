import uproot
from typing import Dict, List, Union
import numpy as np
from numpy.typing import NDArray
import pandas as pd
from pprint import PrettyPrinter
pp = PrettyPrinter(indent=4)

uprootfile = uproot.reading.ReadOnlyDirectory

import logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s:  %(message)s')

def to_str(obj):
    lines = []

    if not isinstance(obj, dict):
        raise TypeError('Type not supported. Must inherit from dict.')

    for k,v in obj.items():
        if isinstance(v, str) and v:
            lines.append(f'{k} = {v}')
        elif isinstance(v, dict):
            lines.append(to_str(v))
        elif isinstance(v, np.ndarray):
            lines.append(f'{k} = {v[0:5,0:5]}')
        elif isinstance(v, pd.DataFrame):
            df_str = '\n\t\t'.join(v.to_string(max_rows=5, max_cols=6).split('\n'))
            lines.append(f'{k} = '+'\n\t\t'+f'{df_str}')

    return ',\n\t'.join(lines)

class ObjPackage(dict):
    def __init__(self, **kwargs):
        self._allowed_keys = ["name", "type", "data", "xtitle", "ytitle", "fig"]
        if len(kwargs) > 0:
            for k,v in kwargs.items():
                self[k] = v

    def __getitem__(self, __k: str) -> Union[str, NDArray]:
        return super().__getitem__(__k)

    def __setitem__(self, __k: str, v: Union[str, NDArray]) -> None:
        if __k not in self._allowed_keys:
            raise KeyError(f'Key "{__k}" not supported. ObjPackage can only contain keys {self._allowed_keys}.')
        return super().__setitem__(__k, v)

    def __repr__(self) -> str:
        return "ObjPackage(\n\t{}\n)".format(to_str(self))

def set_n_subentries(array_of_entries: NDArray, n_subentries: int, fillval: object=0) -> NDArray:
    '''Create a numpy array of zeros of the size of the input.
    Fill in indices for which there is a value, leaving out 
    any values that are out of index range.

    Args:
        array_of_entries (NDArray): [description]
        n_subentries (int): [description]

    Returns:
        NDArray: [description]
    '''
    out = np.full(
        (len(array_of_entries), n_subentries), fillval
    )
    for ientry, entry in enumerate(array_of_entries):
        for isubentry in range(n_subentries):
            if isubentry < entry.size:
                out[ientry][isubentry] = entry[isubentry]
    return out

def get_flat_df(tree: uproot.models.TTree, n_subentries: int = 5) -> pd.DataFrame:
    '''Efficient unpacking of TTree into dict of numpy arrays. Since the arrays are
    of dim 1, storing sub-arrays of variable length, the sub-arrays must be
    set to a static number of subentries. The resulting 2D numpy array is fed into
    pandas. 

    Performance comparison:
    - Using just `tree.arrays(library='pd', how='left')` unpacks a 22 MB file into a 2.2 GB DataFrame in memory!
    - This algorithmic unpacking returns a 70 MB DataFrame from the same 22 MB file.

    Args:
        tree (uproot.models.TTree): [description]
        n_subentries (int, optional): [description]. Defaults to 5.

    Returns:
        pd.DataFrame: [description]
    '''
    # Uproot magic - keys are branch names, values are array of arrays
    # where the sub arrays are of variable length.
    # Removes anything from edm namespace (CMSSW)
    edm_filter = lambda b: 'edm::' not in b.typename#'/^.(?!(edm\:\:))$/'

    if len(tree.keys(filter_branch=edm_filter)) == 0:
        return 'Cound not open TTree due to unsupported branches in edm namespace.'

    tree_dict = tree.arrays(library='np', filter_branch=edm_filter) 

    # Unstack TTree into Series (non-vector branches) and DataFrames (vector branches)
    all_columns = []
    for branch_name, branch_entries in tree_dict.items():
        has_many = not np.isscalar(branch_entries[0])

        if not has_many:
            all_columns.append(pd.Series(branch_entries, name=branch_name))

        else:
            all_columns.append(
                pd.DataFrame(
                    set_n_subentries(branch_entries, n_subentries),
                    columns = [f'{branch_name}_{i}' for i in range(n_subentries)]
                )
            )

    df = pd.concat(all_columns, axis=1)

    return df

def supported_obj_keys(file: uprootfile, pick_objs: List[str] = []) -> List[str]:
    # NOTE: Currently only supporting histograms
    unsupported = []
    out = []
    for obj_name in [k.split(';')[0] for k in file.keys()]:
        class_match = [file.classname_of(obj_name).startswith(classname) for classname in ['TH','TTree']]

        if (pick_objs != []) and (obj_name not in pick_objs):
            continue
        elif any(class_match):
            out.append(obj_name)
        else:
            unsupported.append(file.classname_of(obj_name))
            continue            

    if len(unsupported) > 0:
        logging.warning(f'Only histograms and TTrees are currently supported. Objects of other types will be skipped (found {unsupported}).')

    return out 

def extract_from_file(filepath: str, obj_name: List[str] = []) -> Dict[str, ObjPackage]:
    file = uproot.open(filepath)
    
    if file.classname_of(obj_name).startswith('TH'):
        pkg = ObjPackage(
            name = obj_name,
            data = file[obj_name].to_numpy(),
            xtitle = file[obj_name].member('fXaxis').member('fTitle'),
            ytitle = file[obj_name].member('fYaxis').member('fTitle'),
            type = file.classname_of(obj_name)
        )

    elif file.classname_of(obj_name).startswith('TTree'):
        pkg = ObjPackage(
            name = obj_name,
            data = get_flat_df(file[obj_name]),
            type = file.classname_of(obj_name)
        )
    
    else:
        raise RuntimeError(f'Not able to extract object {obj_name} from {filepath}')

    file.close()
    return pkg

def get_file_info(filepath: str) -> uproot.reading.ReadOnlyDirectory:
    logging.debug(f'Opening file {filepath}')
    file = uproot.open(filepath)

    supported_keys = supported_obj_keys(file)

    logging.debug(f"All keys in file: {', '.join([k for k in file.keys()])}")
    logging.debug(f"Opening supported keys: {', '.join(supported_keys)}")

    objs = {}
    for obj_name in supported_keys:
        pkg = ObjPackage(
            name   = obj_name.split(';')[0],
            type   = file.classname_of(obj_name)
        )

        objs[pkg['name']] = pkg

    file.close()
    return objs

if __name__ == '__main__':
    pass