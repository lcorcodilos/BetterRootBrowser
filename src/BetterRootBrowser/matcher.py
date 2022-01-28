from statistics import mean
from collections import Counter, defaultdict
import numpy as np
import re, itertools, math

import logging
logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG, format='%(levelname)s:  %(message)s')

'''-----------Base array creation and conversion----------------'''
def tokenize(items):
    split_items = [re.findall('[a-zA-Z]+|[0-9]+',item) for item in items]

    # Pad with empty strings
    max_tokens = max([len(tkns) for tkns in split_items])
    for i,tkns in enumerate(split_items):
        if len(tkns) < max_tokens:
            split_items[i].extend(['']*(max_tokens-len(tkns)))

    return np.array(split_items).astype('U256')

def to_Tokens(a):
    out = a.copy().astype('object')
    for irow, icol in itertools.product(range(a.shape[0]),range(a.shape[1])):
        out[irow][icol] = Token(irow, icol, a[irow][icol])

    out = set_token_tensions(out)

    return out

def to_array(tokens):
    return np.ndarray([[tkn.val for tkn in row] for row in tokens]).astype('U256')


'''-----------Token tensions + metrics--------------------'''
def set_token_tensions(tokens):
    for token in tokens:
        other_token_idxs = get_matching_idxs(token, to_array(tokens))
        other_tokens = tokens.take(other_token_idxs)
        distances = [distance_between(token, other) for other in other_tokens]
        # Total "spring force" of the other tokens
        raw_tension = mean(distances)
        # Net force which accounts for no room to move in direction of spring force (ie. there's a wall)
        token.tension = 0
        if raw_tension > 0 and has_room_right(token):
            token.tension = raw_tension
        elif raw_tension < 0 and has_room_left(token):
            token.tension = raw_tension
    
    return tokens

def get_matching_idxs(token, tokens):
    a = to_array(tokens)
    return [idx for idx in zip(
                *np.where(a == token.val)
        ) if idx != token.idx
    ]

def distance_between(token, other):
    return other.col - token.col

def entropy_of_col(tokens, icol):
    col = [t.val for t in tokens[:, icol]]
    counter = Counter(col)
    total = sum([v for v in counter.values()])
    probs = [count/total for count in counter.values()]
    out = sum(-p*math.log(p) for p in probs)
    return out

def total_entropy(tokens):
    return sum(entropy_of_col(tokens, icol) for icol in range(tokens.shape[1]))

'''------------------Helpers----------------------------'''
def _get_direction(direction, left, right):
    if direction == '':
        if left:
            direction = 'l'
        elif right:
            direction = 'r'
    
    if direction not in ['l','r']:
        raise ValueError('Arg direction must be either "l" or "r" or arg left or right must be set to True.')

    return direction

def get_matching_idxs(token, tokens):
    a = to_array(tokens)
    return [idx for idx in zip(
                *np.where(a == token.val)
        ) if idx != token.idx
    ]

'''----------------Array manipulations--------------------'''
def merge_next_col(tokens, icol):
    out = to_array(tokens)
    if icol+1 < out.shape[1]:
        new_row = []
        for a,b in zip(out[:, icol], out[:, icol+1]):
            if b == '':
                new_row.append(a)
            else:
                new_row.append(f'{a}-{b}')
        out[:, icol] = np.array(new_row, dtype='U256')
        out = np.delete(out, icol+1, 1)
    else:
        logging.debug(f'Next column {icol+1} does not exist in array with {a.shape[1]} columns. Will not attempt merge.')
    return to_Tokens(out)

def merge_next_cell(token, tokens):
    irow, icol = token.idx
    out = to_array(tokens)
    if icol+1 < out.shape[0]:
        if out[irow, icol+1] != '':
            out[irow, icol] = f'{out[irow,icol]}-{out[irow,icol+1]}'

        temp = np.delete(out[irow], icol+1)
        out[irow] = np.append(temp, [''])
    else:
        logging.debug(f'Next column {icol+1} does not exist in array with {a.shape[1]} columns. Will not attempt merge.')
    
    return to_Tokens(out)

def has_room_right(token, tokens):
    return has_room(token, tokens, direction='r')
def has_room_left(token, tokens):
    return has_room(token, tokens, direction='l')
def has_room(token, tokens, direction='', left=False, right=False):
    d = _get_direction(direction, left, right)
    irow, icol = token.idx
    a = to_array(tokens)
    if d == 'r':
        if (a[irow,icol+1:] == '').any():
            return True
        else:
            return False
    elif d == 'l':
        if (a[irow,:icol] == '').any():
            return True
        else:
            return False

def nearest_blank_left(token, tokens):
    return nearest_blank(token, tokens, direction='l')   
def nearest_blank_right(token, tokens):
    return nearest_blank(token, tokens, direction='r')
def nearest_blank(token, tokens, direction='', left=False, right=False):
    d = _get_direction(direction, left, right)
    irow, icol = token.idx
    a = to_array(tokens)
    if d == 'r':
        all_right_idxs = list(
            zip(
                *np.where(a[irow, icol+1:] == '')
            )
        )
        return all_right_idxs[0]
    
    elif d == 'l':
        all_left_idxs = list(
            zip(
                *np.where(a[irow, :icol] == '')
            )
        )
        return all_left_idxs[-1]

def slide_token(token, tokens, direction='', left=False, right=False):
    d = _get_direction(direction, left, right)
    irow, icol = token.idx
    out = to_array(tokens)

    next_blank_idx = nearest_blank(tokens, irow, icol, d)

    if d == 'r':
        if has_room_right(token, tokens):
            out[irow, icol+1:next_blank_idx+1] = self.a[irow, icol:next_blank_idx]
            out[irow, icol] = ''
        else:
            logging.debug(f'Cannot move right because there are no empty tokens to use. {out[irow]}')
    
    elif d == 'l':
        if has_room_left(token):
            out[irow, next_blank_idx:icol] = self.a[irow, next_blank_idx+1:icol+1]
            out[irow, icol] = ''
        else:
            logging.debug(f'Cannot move left because there are no empty tokens to use. {out[irow]}')

'''--------------------------Classes------------------------------'''
class TokenArray():
    def __init__(self, list_of_strs) -> None:
        self.raw_items = list_of_strs
        self.tokens = to_Tokens(tokenize(self.raw_items))

    @property
    def a(self):
        return to_array(self.tokens)

    def entropy_of_col(self, icol):
        return entropy_of_col(self.tokens, icol)

    def total_entropy(self):
        return total_entropy(self.tokens)

    def diff_entropy(self, new_tokens):
        # Negative if new tokens are better (entropy decreases)
        return total_entropy(new_tokens) - self.total_entropy()

    def entropy_per_merge(self):
        n_lists, n_tokens = self.tokens.shape
        entropy_gain_per_merge = np.zeros((n_lists,n_tokens-1))
        for ilist, itkn in itertools.product(range(n_lists), range(n_tokens-1)):
            new_tokens = merge_next_cell(self.tokens, ilist, itkn)
            entropy_gain_per_merge[ilist, itkn] = self.diff_entropy(new_tokens)

        return entropy_gain_per_merge

    def merge_next_cell(self, irow, icol):
        self.tokens = merge_next_cell(self.tokens, irow, icol)

    def merge_next_col(self, icol):
        self.tokens = merge_next_col(self.tokens, icol)

    def slide_token_right(self, token):
        self.tokens = self.slide_token()
            
    def slide_token_left(self, token):
        irow, icol = token.idx
        out = self.a.copy().astype('U256')
        if self.has_room_left(token):
            next_blank_idx = self.nearest_blank_left(token)
            out[irow,next_blank_idx:icol] = self.a[irow,next_blank_idx+1:icol+1].copy()
            out[irow,icol] = ''
            token.col = icol-1
        else:
            logging.debug(f'Cannot move right because there are no empty tokens to use. {out[irow]}')

    

class Token():
    def __init__(self, row, col, val) -> None:
        self.row = row
        self.col = col
        self.val = val
        self.tension = 0

    @property
    def idx(self):
        return (self.row, self.col)

if __name__ == '__main__':
    pass