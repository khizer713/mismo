import json
import os
import csv


# === Load JSON ===
with open("xpaths_MESSAGE_recursive.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# === Configuration ===
search_mode = "container"  # Options: "datapoint", "enumeration", or "container"

output_format = "csv"      # Options: "json" or "csv"

target_endpoints = ["BorrowerResidencyType", "ContactPointEmailValue", "LoanPurposeType"]
target_containers = ["FOREIGN_OBJECTS"]
output_dir = "search_exports"
os.makedirs(output_dir, exist_ok=True)

# === Filter Matches Based on Search Mode ===
matches_by_key = {}

for entry in data.get("mismo_xpaths", []):
    if search_mode in ["datapoint", "enumeration"]:
        if (
            entry.get("endpoint_type") in ["DataPoint", "Enumeration"]
            and entry.get("endpoint") in target_endpoints
        ):
            key = entry.get("endpoint")
            matches_by_key.setdefault(key, []).append(entry)

    elif search_mode == "container":
        if entry.get("endpoint") in target_containers:
            key = entry.get("endpoint")
            matches_by_key.setdefault(key, []).append(entry)

# === Export Results ===
for key, matches in matches_by_key.items():
    filename = f"{search_mode}_{key}.{output_format}"
    filepath = os.path.join(output_dir, filename)

    if output_format == "json":
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "search_mode": search_mode,
                "key": key,
                "count": len(matches),
                "matches": matches
            }, f, indent=2)

    elif output_format == "csv":
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=matches[0].keys())
            writer.writeheader()
            writer.writerows(matches)

print(f"\n✅ Exported {len(matches_by_key)} files to '{output_dir}/' as {output_format.upper()} using mode '{search_mode}'")
