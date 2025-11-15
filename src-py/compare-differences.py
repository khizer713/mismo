import json
import sys
from deepdiff import DeepDiff
import json

# Example file paths to compare    
# ..\node-occurrences-search-results\container_PARTY340.json
# ..\node-occurrences-search-results\container_PARTY362.json
# ..\compare-differences\diff_PARTY.json
# python compare-differences.py ..\node-occurrences-search-results\container_PARTY340.json ..\node-occurrences-search-results\container_PARTY362.json ..\compare-differences\diff_PARTY.txt
# python compare-differences.py ../node-occurrences-search-results/container_PARTY340.json ../node-occurrences-search-results/container_PARTY362.json ../compare-differences/diff_PARTY.txt

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_xpaths(data):
    return set(item.get("xpath") for item in data.get("matches", []) if "xpath" in item)

def compare_xpaths(file1, file2, output_file):
    json1 = load_json(file1)
    json2 = load_json(file2)

    xpaths1 = extract_xpaths(json1)
    xpaths2 = extract_xpaths(json2)

    added = sorted(xpaths2 - xpaths1)
    removed = sorted(xpaths1 - xpaths2)
    # Excluding common elements from the human-readable diff for brevity
    #common = sorted(xpaths1 & xpaths2)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== XPath Comparison Report ===\n\n")
        f.write(f"File 1: {file1}\n")
        f.write(f"File 2: {file2}\n\n")

        f.write(">> Added XPaths (in File 2 but not in File 1):\n")
        for xpath in added:
            f.write(f"  + {xpath}\n")

        f.write("\n>> Removed XPaths (in File 1 but not in File 2):\n")
        for xpath in removed:
            f.write(f"  - {xpath}\n")

        # f.write("\n>> Common XPaths (present in both files):\n")
        # for xpath in common:
        #     f.write(f"  = {xpath}\n")

    print(f"Human-readable diff written to {output_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python xpath_diff.py <file1.json> <file2.json> <output.txt>")
    else:
        compare_xpaths(sys.argv[1], sys.argv[2], sys.argv[3])