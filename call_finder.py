import json
import os
import re

PY_CLIENT_PATTERNS = [
    r"requests\.(get|post|put|delete|patch|head|options)",
    r"client\.(get|post|put|delete|patch|head|options)",
    r"TestClient\(\s*\)\.(get|post|put|delete|patch|head|options)",
    r"httpx\.(get|post|put|delete|patch|head|options)",
    r"aiohttp\.ClientSession\(\s*\)\.(get|post|put|delete|patch|head|options)",
    r"urllib\.request\.urlopen",
]

JS_CLIENT_PATTERNS = [
    r"fetch\s*\(",
    r"axios\.(get|post|put|delete|patch|head|options)",
    r"\$\.ajax", r"\$\.(get|post)",
    r"apiClient\.(get|post|put|delete|patch|head|options)",
    r"window\.fetch\s*\(",
]

def is_potential_api_call(line_content, endpoint_path_to_check, lang_patterns):
    """Checks if a line contains common API client call patterns AND the specific endpoint path."""
    # First, check if the endpoint path is in the line
    # For paths like "/", ensure it's an exact argument like get("/") or fetch("/")
    path_present_correctly = False
    if endpoint_path_to_check == "/":
        # Regex to find "/" as an exact argument: (client.get("/", ...) or fetch("/?..."))
        # It should be enclosed in quotes and be a distinct argument.
        # This regex looks for (some_method_call_ending_with_paren_or_comma) "endpoint_path" (optional_comma_or_closing_paren)
        if re.search(r"(\(|,\s*)(\"|\'|\`)"+ re.escape(endpoint_path_to_check) + r"(\"|\'|\`)(\s*,|\s*\))", line_content):
            path_present_correctly = True
    elif endpoint_path_to_check in line_content: # For other paths, simple substring match
        path_present_correctly = True

    if not path_present_correctly:
        return False

    # If path is present, then check for API client patterns
    for pattern in lang_patterns:
        if re.search(pattern, line_content, re.IGNORECASE):
            return True
    return False

def find_call_locations(endpoints_file="identified_endpoints.json"):
    try:
        with open(endpoints_file, "r") as f:
            endpoints_data = json.load(f) # This is a list of endpoint dicts
    except FileNotFoundError:
        print(f"Error: Endpoints file '{endpoints_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{endpoints_file}'.")
        return

    search_config = {
        "directories": ["app/", "frontend/js/", "Tests/"],
        "extensions": {".py": PY_CLIENT_PATTERNS, ".js": JS_CLIENT_PATTERNS}
    }

    call_sites = []

    # Get unique full_paths, sorted longest first to ensure more specific paths are matched first.
    unique_endpoint_paths = sorted(list(set(ep["full_path"] for ep in endpoints_data if ep["full_path"])), key=len, reverse=True)

    num_unique_endpoint_paths = len(unique_endpoint_paths)

    for root_dir in search_config["directories"]:
        for dirname, _, files in os.walk(root_dir):
            for filename in files:
                file_ext = os.path.splitext(filename)[1]
                if file_ext in search_config["extensions"]:
                    filepath = os.path.join(dirname, filename)
                    relevant_patterns = search_config["extensions"][file_ext]
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f_content:
                            lines = f_content.readlines()
                            for i, line_content in enumerate(lines):
                                for endpoint_path_to_search in unique_endpoint_paths:
                                    # The combined check is now in is_potential_api_call
                                    if is_potential_api_call(line_content, endpoint_path_to_search, relevant_patterns):
                                        call_sites.append({
                                            "endpoint_path_matched": endpoint_path_to_search,
                                            "file": filepath,
                                            "line_number": i + 1,
                                            "line_content": line_content.strip()
                                        })
                                        # Optimization: if a line matches a longer path, break from inner path loop
                                        break
                    except Exception as e:
                        print(f"Error processing file {filepath}: {e}")

    with open("endpoint_calls.json", "w") as f_out:
        json.dump(call_sites, f_out, indent=2)

    print(f"Identified {num_unique_endpoint_paths} unique endpoint paths for searching.")
    print(f"Found {len(call_sites)} potential call sites.")
    print("Call site details saved to endpoint_calls.json")

if __name__ == "__main__":
    find_call_locations()
