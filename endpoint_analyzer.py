import ast
import json
import os
import re # For improved path parameter detection

def get_decorator_details(decorator):
    """Extracts method and path from a FastAPI decorator."""
    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
        method = decorator.func.attr.upper()
        if method in ["GET", "POST", "PUT", "DELETE", "PATCH", "API_ROUTE"]:
            if decorator.args:
                path_arg = decorator.args[0]
                if isinstance(path_arg, ast.Constant):
                    return method, path_arg.value
                elif isinstance(path_arg, ast.Str): # Python < 3.8
                    return method, path_arg.s
    return None, None

def get_parameter_details(arg_node, path_str, func_def_node):
    """Extracts details for a single parameter."""
    param_name = arg_node.arg
    param_type = None
    if arg_node.annotation:
        if isinstance(arg_node.annotation, ast.Name):
            param_type = arg_node.annotation.id
        elif isinstance(arg_node.annotation, ast.Subscript):
            base_type_name = ""
            slice_repr = ""
            if isinstance(arg_node.annotation.value, ast.Name):
                base_type_name = arg_node.annotation.value.id
            elif isinstance(arg_node.annotation.value, ast.Attribute):
                 if isinstance(arg_node.annotation.value.value, ast.Name):
                     base_type_name = f"{arg_node.annotation.value.value.id}.{arg_node.annotation.value.attr}"
                 else:
                     base_type_name = ast.dump(arg_node.annotation.value)

            current_slice = arg_node.annotation.slice
            if isinstance(current_slice, ast.Name): slice_repr = current_slice.id
            elif isinstance(current_slice, ast.Constant): slice_repr = str(current_slice.value)
            elif isinstance(current_slice, ast.Index):
                if isinstance(current_slice.value, ast.Name): slice_repr = current_slice.value.id
                elif isinstance(current_slice.value, ast.Constant): slice_repr = str(current_slice.value.value)
            elif isinstance(current_slice, ast.Tuple):
                slice_elts = []
                for elt in current_slice.elts:
                    if isinstance(elt, ast.Name): slice_elts.append(elt.id)
                    elif isinstance(elt, ast.Constant): slice_elts.append(str(elt.value))
                    else: slice_elts.append(ast.dump(elt))
                slice_repr = ", ".join(slice_elts)

            if base_type_name and slice_repr: param_type = f"{base_type_name}[{slice_repr}]"
            elif base_type_name: param_type = base_type_name
            else: param_type = ast.dump(arg_node.annotation)
        elif isinstance(arg_node.annotation, ast.Constant):
             param_type = arg_node.annotation.value
        elif isinstance(arg_node.annotation, ast.Attribute):
             if isinstance(arg_node.annotation.value, ast.Name):
                 param_type = f"{arg_node.annotation.value.id}.{arg_node.annotation.attr}"
             else:
                 param_type = f"{ast.dump(arg_node.annotation.value)}.{arg_node.annotation.attr}"
        else: param_type = ast.dump(arg_node.annotation)

    param_kind = "body" # Default to body
    # Improved path parameter detection: check if param_name is within {} in the path_str
    # This handles cases like {item_id} and {item_id:str}
    if re.search(r"\{" + re.escape(param_name) + r"(:[^}]+)?\}", path_str):
        param_kind = "path"
    # TODO: Add logic to check for Query, Body, Path from fastapi imports for more accurate kind

    default_value = "NOT_SET"
    arg_names = [a.arg for a in func_def_node.args.args]
    if param_name in arg_names:
        param_idx = arg_names.index(param_name)
        num_defaults = len(func_def_node.args.defaults)
        if param_idx >= (len(arg_names) - num_defaults):
            default_node = func_def_node.args.defaults[param_idx - (len(arg_names) - num_defaults)]
            if isinstance(default_node, ast.Constant): default_value = default_node.value
            elif isinstance(default_node, ast.NameConstant): default_value = default_node.value # Python < 3.8
            elif isinstance(default_node, ast.Num): default_value = default_node.n # Python < 3.8
            elif isinstance(default_node, ast.Str): default_value = default_node.s # Python < 3.8

    kwonlyarg_names = [a.arg for a in func_def_node.args.kwonlyargs]
    if param_name in kwonlyarg_names:
        param_idx = kwonlyarg_names.index(param_name)
        if func_def_node.args.kw_defaults[param_idx] is not None:
            default_node = func_def_node.args.kw_defaults[param_idx]
            if isinstance(default_node, ast.Constant): default_value = default_node.value
            elif isinstance(default_node, ast.NameConstant): default_value = default_node.value
            elif isinstance(default_node, ast.Num): default_value = default_node.n
            elif isinstance(default_node, ast.Str): default_value = default_node.s

    return {"name": param_name, "type": param_type, "kind": param_kind, "default": default_value if default_value != "NOT_SET" else None}

def analyze_file(filepath):
    endpoints = []
    router_prefixes = {}
    with open(filepath, "r") as source:
        try:
            tree = ast.parse(source.read(), filename=filepath)
        except SyntaxError as e:
            print(f"SyntaxError in {filepath}: {e}", file=sys.stderr)
            return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    router_name_candidate = target.id
                    if isinstance(node.value, ast.Call):
                        func_being_called = node.value.func
                        is_api_router_instantiation = False
                        if isinstance(func_being_called, ast.Name) and func_being_called.id == "APIRouter":
                            is_api_router_instantiation = True
                        elif isinstance(func_being_called, ast.Attribute) and func_being_called.attr == "APIRouter":
                             is_api_router_instantiation = True
                        if is_api_router_instantiation:
                            prefix = ""
                            for kw in node.value.keywords:
                                if kw.arg == "prefix":
                                    if isinstance(kw.value, ast.Constant): prefix = kw.value.value
                                    elif isinstance(kw.value, ast.Str): prefix = kw.value.s
                            router_prefixes[router_name_candidate] = prefix

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if isinstance(decorator.func.value, ast.Name):
                        router_var_name = decorator.func.value.id
                        if router_var_name in router_prefixes:
                            method, path = get_decorator_details(decorator)
                            if method and path is not None:
                                router_actual_prefix = router_prefixes[router_var_name]
                                full_path = router_actual_prefix + path
                                parameters = []
                                for arg_obj in node.args.args:
                                    if arg_obj.arg in ["self", "cls"]: continue
                                    if arg_obj.annotation and isinstance(arg_obj.annotation, ast.Name) and arg_obj.annotation.id in ["Request", "BackgroundTasks"]: continue
                                    is_dependency = False
                                    default_for_arg = None
                                    try:
                                        arg_index_in_args = [a.arg for a in node.args.args].index(arg_obj.arg)
                                        num_args_total = len(node.args.args)
                                        num_defaults = len(node.args.defaults)
                                        if arg_index_in_args >= num_args_total - num_defaults:
                                            default_for_arg = node.args.defaults[arg_index_in_args - (num_args_total - num_defaults)]
                                    except ValueError: pass
                                    if default_for_arg and isinstance(default_for_arg, ast.Call) and \
                                       isinstance(default_for_arg.func, ast.Name) and default_for_arg.func.id in ["Depends", "Security"]:
                                        is_dependency = True
                                    if not is_dependency:
                                        parameters.append(get_parameter_details(arg_obj, path, node))
                                for k_arg in node.args.kwonlyargs:
                                    if k_arg.annotation and isinstance(k_arg.annotation, ast.Name) and k_arg.annotation.id in ["Request", "BackgroundTasks"]: continue
                                    is_dependency = False
                                    kw_default_idx = node.args.kwonlyargs.index(k_arg)
                                    default_node_for_kwarg = node.args.kw_defaults[kw_default_idx]
                                    if default_node_for_kwarg and isinstance(default_node_for_kwarg, ast.Call) and \
                                       isinstance(default_node_for_kwarg.func, ast.Name) and default_node_for_kwarg.func.id in ["Depends", "Security"]:
                                        is_dependency = True
                                    if not is_dependency:
                                     parameters.append(get_parameter_details(k_arg, path, node))
                                endpoints.append({
                                    "file": os.path.basename(filepath),
                                    "router_prefix": router_actual_prefix, "path": path, "full_path": full_path,
                                    "method": method, "function_name": func_name, "parameters": parameters
                                })
                                break
    return endpoints

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python endpoint_analyzer.py <filepath1> [<filepath2> ...]", file=sys.stderr)
        sys.exit(1)
    all_results = []
    for filepath_arg in sys.argv[1:]:
        print(f"Analyzing file: {filepath_arg}", file=sys.stderr)
        try:
            results = analyze_file(filepath_arg)
            all_results.extend(results)
        except Exception as e:
            print(f"Error analyzing file {filepath_arg}: {e}", file=sys.stderr)
    print(json.dumps(all_results, indent=2))
