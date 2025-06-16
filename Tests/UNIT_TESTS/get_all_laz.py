import json
from pathlib import Path


def get_all_laz(input_dir: str = "input/LAZ"):
    """Return list of LAZ/LAS files in the input directory."""
    laz_dir = Path(input_dir)
    if not laz_dir.exists():
        return []
    laz_files = [f.name for f in laz_dir.iterdir()
                 if f.is_file() and f.suffix.lower() in [".laz", ".las"]]
    return sorted(laz_files)


if __name__ == "__main__":
    files = get_all_laz()
    print(json.dumps(files, indent=2))
    output_path = Path(__file__).with_name("UNIT_TESTS_OUTPUTS") / "get_all_laz.json"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(files, indent=2))
