import os
import json
import zipfile
import numpy as np
import pickle
from collections import OrderedDict, Counter
import pandas as pd

def load_jsonl_as_dict(filename, encoding="utf-8"):
    edge_desc = {}
    with open(filename, 'r', encoding=encoding) as f:
        for line in f:
            line_data = json.loads(line)
            edge_desc.update(line_data)
    return edge_desc

def l2_normalize_np_array(np_array, eps=1e-5):
    """np_array: np.ndarray, (*, D), where the last dim will be normalized"""
    return np_array / (np.linalg.norm(np_array, axis=-1, keepdims=True) + eps)

def load_pickle(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)

def save_pickle(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

def load_json(filename, encoding='utf-8'):
    with open(filename, "r", encoding=encoding) as f:
        return json.load(f)

def save_json(data, filename,encoding="utf-8", save_pretty=False, sort_keys=False):
    with open(filename, "w",encoding=encoding) as f:
        if save_pretty:
            f.write(json.dumps(data, indent=4, sort_keys=sort_keys, ensure_ascii=False))
        else:
            json.dump(data, f, ensure_ascii=False)

def load_jsonl(filename,encoding="utf-8"):
    with open(filename, "r",encoding=encoding) as f:
        return [json.loads(l.strip("\n")) for l in f.readlines()]

def save_jsonl(data, filename,encoding="utf-8"):
    """data is a list"""
    with open(filename, "w",encoding=encoding) as f:
        f.write("\n".join([json.dumps(e, ensure_ascii=False) for e in data]))

def save_lines(list_of_str, filepath):
    with open(filepath, "w") as f:
        f.write("\n".join(list_of_str))

def read_lines(filepath):
    with open(filepath, "r") as f:
        return [e.strip("\n") for e in f.readlines()]

def mkdirp(p):
    if not os.path.exists(p):
        os.makedirs(p)

def find_last_loop(lst):
    # Iterate from the end of the list backwards
    for loop_length in range(2, len(lst) // 2 + 1, 2):
        # Check if the last segment repeats in the list
        possible_loop = lst[-loop_length:]  # Get a potential loop segment
        start_idx = len(lst) - 2 * loop_length

        # Check if this segment appears before in the list, indicating a loop
        if lst[start_idx:start_idx + loop_length] == possible_loop:
            # Return the starting index and the sub-list of the loop
            return start_idx, possible_loop

    # If no loop is found, return None
    return None, []
