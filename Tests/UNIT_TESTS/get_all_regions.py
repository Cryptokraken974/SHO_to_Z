import json
from pathlib import Path


def get_all_regions(base_dir: str = "input"):
    """Return list of regions discovered in the input directory.

    Each region corresponds to a LAZ/LAS file. If a metadata_*.txt file is
    present in the same directory and contains a `# Center:` line it is used to
    extract coordinates.
    """
    base = Path(base_dir)
    regions = []
    for laz in base.rglob("*.laz"):
        region = {
            "name": laz.stem,
            "file_path": str(laz.relative_to(base)),
            "center_lat": None,
            "center_lng": None,
        }
        for meta in laz.parent.glob("metadata_*.txt"):
            try:
                content = meta.read_text().splitlines()
                for line in content:
                    if line.startswith("# Center:"):
                        coords = line.split("# Center:")[1].strip().split(",")
                        if len(coords) == 2:
                            region["center_lat"] = float(coords[0])
                            region["center_lng"] = float(coords[1])
                        break
            except Exception:
                pass
        regions.append(region)
    return regions


if __name__ == "__main__":
    data = get_all_regions()
    print(json.dumps(data, indent=2))
    output_path = Path(__file__).with_name("UNIT_TESTS_OUTPUTS") / "get_all_regions.json"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2))
