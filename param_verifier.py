import json
import os
import re
import ast # For safely evaluating Python dicts/lists

def load_json_file(filepath):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'.")
        return None

def extract_python_params(line_content):
    """Rudimentary extraction of params from Python code snippets."""
    passed_params = {"query": {}, "body": {}, "path_args_found": []}

    # TestClient/requests: params={...}
    query_match = re.search(r"params\s*=\s*(\{.*?\})", line_content)
    if query_match:
        try:
            params_str = query_match.group(1)
            # Handle f-strings within the dict by replacing them with placeholders
            # This is a very basic heuristic and might not cover all f-string complexities.
            params_str_eval = re.sub(r"f(['\"]).*?(\1)", "\"<f-string>\"", params_str)
            params_str_eval = re.sub(r"\{.*?\}", "\"<var>\"", params_str_eval) # General placeholder for {variables}
            passed_params["query"] = ast.literal_eval(params_str_eval)
        except (SyntaxError, ValueError):
            # Could not parse, maybe it's too complex (e.g., variables)
            # Fallback: try to get keys with regex
            for m in re.finditer(r"(['\"])(\w+)\1\s*:", params_str):
                passed_params["query"][m.group(2)] = "<unknown_value>"


    # TestClient/requests: json={...}
    body_match_json = re.search(r"json\s*=\s*(\{.*?\})", line_content)
    if body_match_json:
        try:
            body_str = body_match_json.group(1)
            body_str_eval = re.sub(r"f(['\"]).*?(\1)", "\"<f-string>\"", body_str)
            body_str_eval = re.sub(r"\{.*?\}", "\"<var>\"", body_str_eval)
            passed_params["body"] = ast.literal_eval(body_str_eval)
        except (SyntaxError, ValueError):
            for m in re.finditer(r"(['\"])(\w+)\1\s*:", body_str):
                 passed_params["body"][m.group(2)] = "<unknown_value_body>"

    # TestClient/requests: data={...} (often form data, can also be dict)
    body_match_data = re.search(r"data\s*=\s*(\{.*?\})", line_content)
    if body_match_data and not passed_params["body"]: # prioritize json if both
        try:
            data_str = body_match_data.group(1)
            data_str_eval = re.sub(r"f(['\"]).*?(\1)", "\"<f-string>\"", data_str)
            data_str_eval = re.sub(r"\{.*?\}", "\"<var>\"", data_str_eval)
            passed_params["body"] = ast.literal_eval(data_str_eval) # Treat as dict for now
        except (SyntaxError, ValueError):
            for m in re.finditer(r"(['\"])(\w+)\1\s*:", data_str):
                 passed_params["body"][m.group(2)] = "<unknown_value_data>"

    # Path parameters from f-strings or .format() - very basic
    # e.g. f"/api/item/{item_id}" or "/api/item/{}".format(item_id)
    # This just notes that path args are likely being used if {} are in the string
    if re.search(r"(\"|\')((?:[^{}]|\{\w*\})*\{.*?\}(?:[^{}]|\{\w*\})*)(\"|\')", line_content):
        passed_params["path_args_found"] = True # Placeholder, actual extraction is hard

    return passed_params

def extract_js_params(line_content, url_from_call_site):
    """Rudimentary extraction of params from JS code snippets."""
    passed_params = {"query": {}, "body": {}, "path_args_found": False}

    # Query params from URL string
    if '?' in url_from_call_site:
        query_string = url_from_call_site.split('?', 1)[1]
        # Remove template literals like ${...} before splitting
        query_string_clean = re.sub(r"\$\{[^}]+\}", "<js_var>", query_string)
        for part in query_string_clean.split('&'):
            if '=' in part:
                key, val = part.split('=', 1)
                passed_params["query"][key] = val
            elif part: # key only
                passed_params["query"][part] = ""

    # Body: JSON.stringify({...}) or options.body
    body_match = re.search(r"body\s*:\s*JSON\.stringify\s*\((.*?)\)", line_content, re.IGNORECASE)
    options_match = re.search(r"body\s*:\s*(\{.*?\})", line_content) # Simpler { body: data }

    parsed_body_successfully = False
    if body_match:
        body_str = body_match.group(1)
        # Crude attempt to parse JS object literal string by converting to JSON-like
        # Replace JS variables/expressions with placeholders for ast.literal_eval
        # This is highly heuristic.
        body_str_json_like = re.sub(r"\b\w+\b(?=\s*:)", r'"\g<0>"', body_str) # quote keys
        body_str_json_like = re.sub(r":\s*\b(\w+)\b", r':"\1<var>"', body_str_json_like) # quote bareword values
        body_str_json_like = body_str_json_like.replace("'", '"')
        try:
            passed_params["body"] = json.loads(body_str_json_like) # Try full JSON parse
            parsed_body_successfully = True
        except json.JSONDecodeError:
            try: # Fallback to ast.literal_eval if it's a simpler dict-like structure
                passed_params["body"] = ast.literal_eval(body_str_json_like)
                parsed_body_successfully = True
            except: # Final fallback: regex for keys
                 for m in re.finditer(r"(['\"])?(\w+)\1?\s*:", body_str):
                    passed_params["body"][m.group(2)] = "<unknown_js_value_body>"
    elif options_match and not parsed_body_successfully : # if `body: data` where data is an object
        body_obj_str = options_match.group(1)
        try:
            body_obj_str_eval = re.sub(r"(\w+)\s*:", r'"\1":', body_obj_str) # quote keys
            body_obj_str_eval = body_obj_str_eval.replace("'", '"')
            # Replace JS variables with string placeholders
            body_obj_str_eval = re.sub(r":\s*([a-zA-Z_]\w*)", r': "\1<var>"', body_obj_str_eval)
            passed_params["body"] = json.loads(body_obj_str_eval)
        except: # Fallback
            for m in re.finditer(r"(['\"])?(\w+)\1?\s*:", body_obj_str):
                passed_params["body"][m.group(2)] = "<unknown_js_object_body>"


    # Path parameters from template literals
    if re.search(r"`[^`]*\$\{[^}]+\}[^`]*`", url_from_call_site):
        passed_params["path_args_found"] = True

    return passed_params


def verify_parameters():
    endpoints = load_json_file("identified_endpoints.json")
    call_sites = load_json_file("endpoint_calls.json")

    if not endpoints or not call_sites:
        print("Missing endpoint definitions or call site data. Aborting.")
        return

    # Create a lookup for endpoint definitions by their full_path
    endpoint_definitions = {ep["full_path"]: ep for ep in endpoints}
    discrepancies = []

    for call_site in call_sites:
        endpoint_path = call_site["endpoint_path_matched"]
        line_content = call_site["line_content"]
        file_path = call_site["file"]

        definition = endpoint_definitions.get(endpoint_path)
        if not definition:
            discrepancies.append({
                "endpoint_path": endpoint_path, "file": file_path, "line": call_site["line_number"],
                "issue": "Definition not found for this endpoint path.", "parameter": "N/A"
            })
            continue

        # Defined parameters from endpoint_analyzer.py
        defined_params = {
            "path": [p for p in definition["parameters"] if p["kind"] == "path"],
            "query": [p for p in definition["parameters"] if p["kind"] == "query"],
            # Body params can be one Pydantic model or multiple individual params marked as 'body'
            "body_model_type": next((p["type"] for p in definition["parameters"] if p["kind"] == "body" and not p.get("is_individual_body_param")), None),
            "body_fields": [p for p in definition["parameters"] if p["kind"] == "body" and p.get("is_individual_body_param")] # if analyzer marked them so
        }
        # Extract defined path param names from the path string itself (e.g. /items/{item_id})
        defined_path_param_names_from_path = set(re.findall(r"\{(\w+)(:[^}]+)?\}", endpoint_path))
        # defined_path_param_names_from_path is a list of tuples (name, type_suffix), so take first element
        defined_path_param_names_from_path = {item[0] for item in defined_path_param_names_from_path}


        passed_params = {}
        if file_path.endswith(".py"):
            passed_params = extract_python_params(line_content)
        elif file_path.endswith(".js"):
            # JS needs the URL string which might be part of the line_content
            # Try to extract URL from common patterns like fetch(URL, ...) or axios.get(URL, ...)
            url_in_call = endpoint_path # Default to the matched path
            fetch_match = re.search(r"fetch\s*\(([^,)]+)", line_content)
            axios_match = re.search(r"axios\.(?:get|post|put|delete|patch)\s*\(([^,)]+)", line_content)
            if fetch_match:
                url_in_call = fetch_match.group(1).strip().replace("`", "").replace("'", "").replace('"', "")
            elif axios_match:
                url_in_call = axios_match.group(1).strip().replace("`", "").replace("'", "").replace('"', "")
            passed_params = extract_js_params(line_content, url_in_call)

        # --- Path Parameter Verification ---
        # Check if the number of placeholders in definition matches usage
        # This is very heuristic for path params.
        num_placeholders_in_def = len(defined_path_param_names_from_path)

        # For Python, path_args_found is boolean. For JS, it's also boolean.
        # A simple check: if definition expects path params, call should show signs of using them.
        if num_placeholders_in_def > 0 and not passed_params.get("path_args_found", False):
             discrepancies.append({
                "endpoint_path": endpoint_path, "file": file_path, "line": call_site["line_number"],
                "issue": f"Endpoint expects {num_placeholders_in_def} path parameter(s) ({', '.join(defined_path_param_names_from_path)}), but call does not appear to dynamically construct path (e.g. using f-string, template literal, or .format()).",
                "parameter": "Path construction"
            })

        # --- Query Parameter Verification ---
        passed_query_keys = {k.lower() for k in passed_params.get("query", {}).keys()}
        for q_param_def in defined_params["query"]:
            def_name_lower = q_param_def["name"].lower()
            is_required = q_param_def.get("default") is None # Approximation of required

            if is_required and def_name_lower not in passed_query_keys:
                discrepancies.append({
                    "endpoint_path": endpoint_path, "file": file_path, "line": call_site["line_number"],
                    "issue": f"Missing required query parameter.",
                    "parameter": q_param_def["name"]
                })
            # Basic type check (very heuristic)
            if def_name_lower in passed_query_keys and q_param_def.get("type", "").lower() == "int":
                # Find original case key from passed_params.query
                original_case_key = ""
                for pk in passed_params.get("query", {}).keys():
                    if pk.lower() == def_name_lower:
                        original_case_key = pk
                        break
                passed_val = passed_params.get("query", {}).get(original_case_key)
                if passed_val and isinstance(passed_val, str) and not passed_val.isdigit() and passed_val != "<unknown_value>" and passed_val != "<js_var>":
                     discrepancies.append({
                        "endpoint_path": endpoint_path, "file": file_path, "line": call_site["line_number"],
                        "issue": f"Query parameter '{q_param_def['name']}' expects an int, but passed value '{passed_val}' seems non-numeric.",
                        "parameter": q_param_def["name"]
                    })


        # --- Body Parameter Verification ---
        # This is highly limited as we don't have Pydantic field definitions.
        # We rely on parameters marked as 'body' by endpoint_analyzer.py or a body_model_type.

        # Case 1: Endpoint expects a single model body (e.g., Pydantic model)
        if defined_params["body_model_type"]:
            if not passed_params.get("body"): # No body passed at all
                discrepancies.append({
                    "endpoint_path": endpoint_path, "file": file_path, "line": call_site["line_number"],
                    "issue": f"Endpoint expects a request body of type '{defined_params['body_model_type']}', but no body seems to be passed.",
                    "parameter": "Request Body"
                })
            # Cannot validate fields of the model here due to lack of schema details.

        # Case 2: Endpoint expects individual fields as body parameters
        # (FastAPI allows this for non-Pydantic params not in path/query)
        elif defined_params["body_fields"]:
            passed_body_keys = {k.lower() for k in passed_params.get("body", {}).keys()}
            for b_param_def in defined_params["body_fields"]:
                def_name_lower = b_param_def["name"].lower()
                is_required = b_param_def.get("default") is None

                if is_required and def_name_lower not in passed_body_keys:
                    discrepancies.append({
                        "endpoint_path": endpoint_path, "file": file_path, "line": call_site["line_number"],
                        "issue": f"Request body missing required field.",
                        "parameter": b_param_def["name"]
                    })
                # Add more checks here if possible (e.g., simple type checks on known fields)

    # Save discrepancies
    with open("parameter_discrepancies.json", "w") as f_out:
        json.dump(discrepancies, f_out, indent=2)

    print(f"Analyzed {len(call_sites)} call sites.")
    print(f"Found {len(discrepancies)} potential parameter discrepancies.")
    print("Discrepancy details saved to parameter_discrepancies.json")

if __name__ == "__main__":
    verify_parameters()
