import some_sums as ss


def get_functions(module_name, as_string=False):
    "Returns a list of functions, optionally as string function names"
    if module_name == 'all':
        funcs = []
        funcs_in_dict = func_dict()
        for key in funcs_in_dict:
            for func in funcs_in_dict[key]:
                funcs.append(func)
    else:
        funcs = func_dict()[module_name]
    if as_string:
        funcs = [f.__name__ for f in funcs]
    return funcs


def func_dict():
    d = {}
    d['reduce'] = [
                   ss.sum00,
                   ss.sum01,
                   ss.sum02,
                   ]
    return d
