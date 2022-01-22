import uproot
from typing import Dict, List, Union
import numpy as np
from numpy.typing import NDArray
import pandas as pd
import copy

uprootfile = uproot.reading.ReadOnlyDirectory

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:  %(message)s')

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

def set_n_subentries(array_of_entries: NDArray, n_subentries: int) -> NDArray:
    '''Create a numpy array of zeros of the size of the input.
    Fill in indices for which there is a value, leaving out 
    any values that are out of index range.

    Args:
        array_of_entries (NDArray): [description]
        n_subentries (int): [description]

    Returns:
        NDArray: [description]
    '''
    out = np.zeros(
        (len(array_of_entries), n_subentries)
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
    # where the sub arrays are of variable length
    tree_dict = tree.arrays(library='np')

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
                    columns = ['{branch_name}_{i}' for i in range(n_subentries)]
                )
            )

    df = pd.concat(all_columns, axis=1)

    return df

def supported_obj_keys(file: uprootfile, pick_objs: List[str]) -> List[str]:
    # NOTE: Currently only supporting histograms
    unsupported = []
    out = []
    for obj_name in [k.split(';')[0] for k in file.keys()]:
        class_match = [file.classname_of(obj_name).startswith(classname) for classname in ['TH','TTree']]

        if obj_name not in pick_objs:
            continue
        elif any(class_match):
            out.append(obj_name)
        else:
            unsupported.append(file.classname_of(obj_name))
            continue            

    if len(unsupported) > 0:
        logging.warning(f'Only histograms and TTrees are currently supported. Objects of other types will be skipped (found {unsupported}).')

    return out 

def extract(filepath: str, pick_objs: List[str] = []) -> List[ObjPackage]:
    file = uproot.open(filepath)
    objs = []

    for obj_name in supported_obj_keys(file, pick_objs):
        pkg = ObjPackage(
            name   = obj_name.split(';')[0],
            type   = file.classname_of(obj_name)
        )
        
        if pkg['type'].startswith('TH'):
            pkg['data']   = file[obj_name].to_numpy()
            pkg['xtitle'] = file[obj_name].member('fXaxis').member('fTitle')
            pkg['ytitle'] = file[obj_name].member('fYaxis').member('fTitle')

        elif pkg['type'].startswith('TTree'):
            pkg['data']   = get_flat_df(file[obj_name])

        objs.append(pkg)

    file.close()
    return objs

def open_file(filepath: str, pick_objs: List[str] = []) -> List[ObjPackage]:
    obj_pkgs = extract(filepath, pick_objs)
    return obj_pkgs

if __name__ == '__main__':
    pkgs = open_file('~/CMS/temp/nano_4.root',pick_objs=['Events'])
    #~/CMS/BoostedTH/rootfiles/THselection_QCD_16.root
    for p in pkgs:
        print (p)