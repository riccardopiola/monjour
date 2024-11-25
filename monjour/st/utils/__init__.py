import pandas as pd

from monjour.st.utils.page import use_state

GLOBAL_COUNTER = 0
bases = {}

def key_seq(base: str|None = None):
    if base is not None:
        if base in bases:
            bases[base] += 1
        else:
            bases[base] = 0
        return f"{base}::{bases[base]}"
    else:
        global GLOBAL_COUNTER
        GLOBAL_COUNTER += 1
        return f"{base}::{GLOBAL_COUNTER}"

key_combine = lambda base, key: f"{base}::{key}"