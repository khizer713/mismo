import xmlschema
import json
from pathlib import Path
import csv
from pathlib import Path


# === Configuration ===
xsd_path = '../XML Schema Files v3.6.2_B373/MISMO_3.6.2_B373.xsd'  # Path to your XSD file
target_type_name = "BORROWER"      # Complex type to extract from
recursive_traversal = True  # Set to False to only collect directly defined children
excluded_children = ["xxx"]  # Local names only
output_attributes = False          # Include attributes in XPath output
output_namespaces = False          # Include namespaces in XPath output
include_type_names = True          # Set to False to omit type names
include_enumeration_values = False          # Set to False to omit enumerations for type names
include_cardinality = False          # Set to False to omit cardinality
include_container = True          # Set to False to omit container name
include_endpoint = True          # Set to False to omit endpoint name
include_endpoint_type = True          # Set to False to omit endpoint type (Attribute, DataPoint, Enumeration, Container)
output_file_type = "json"          # Options: "json", "csv"
limit_output_for_testing = False   # Set to True to limit output for testing purposes
list_output_limit = 10000         # Limit for testing
output_folder = Path("xpaths-search-results")  # Folder to save output files
""" 
# === Configuration used by list_node_occurrences.py ===
xsd_path = 'MISMO_3.6.2_B373.xsd'  # Path to your XSD file
target_type_name = "MESSAGE"      # Complex type to extract from
recursive_traversal = True  # Set to False to only collect directly defined children
excluded_children = ["xxx"]  # Local names only
output_attributes = False          # Include attributes in XPath output
output_namespaces = False          # Include namespaces in XPath output
include_type_names = True          # Set to False to omit type names
include_enumeration_values = False          # Set to False to omit enumerations for type names
include_cardinality = False          # Set to False to omit cardinality
include_container = True          # Set to False to omit container name
include_endpoint = True          # Set to False to omit endpoint name
include_endpoint_type = True          # Set to False to omit endpoint type (Attribute, DataPoint, Enumeration, Container)
output_file_type = "json"          # Options: "json", "txt"
limit_output_for_testing = False   # Set to True to limit output for testing purposes
list_output_limit = 10000         # Limit for testing

 """
# === XPath Collection ===
def collect_xpaths(xsd_type, parent_path="", include_attributes=True, include_namespace=True, recursive=True, excluded_children=None):
    """Collect XPaths from a complex type. If recursive=False, only include directly defined children.
       If excluded_children is set, skip recursion into those child element names."""
    paths = []
    excluded_children = excluded_children or []

    if hasattr(xsd_type, "content") and hasattr(xsd_type.content, "iter_elements"):
        for child in xsd_type.content.iter_elements():
            if child.name is None:
                continue

            name = child.prefixed_name if include_namespace else child.local_name
            current_path = f"{parent_path}/{name}" if parent_path else f"/{name}"
            paths.append((current_path, child.type, child))  # include element object

            # Skip recursion if excluded
            if recursive and child.type and child.type.is_complex() and child.local_name not in excluded_children:
                paths.extend(collect_xpaths(child.type, current_path, include_attributes, include_namespace, recursive, excluded_children))

            if include_attributes and child.type and hasattr(child.type, "attributes") and child.type.attributes:
                for attr_name, attr in child.type.attributes.items():
                    attr_display = attr.prefixed_name if include_namespace else attr.local_name
                    paths.append((f"{current_path}/@{attr_display}", attr.type, attr))  # include attribute object

    return paths
# def collect_xpaths(xsd_type, parent_path="", include_attributes=True, include_namespace=True, recursive=True):
#     """Collect XPaths from a complex type. If recursive=False, only include directly defined children."""
#     paths = []

#     if hasattr(xsd_type, "content") and hasattr(xsd_type.content, "iter_elements"):
#         for child in xsd_type.content.iter_elements():
#             if child.name is None:
#                 continue

#             name = child.prefixed_name if include_namespace else child.local_name
#             current_path = f"{parent_path}/{name}" if parent_path else f"/{name}"
#             paths.append((current_path, child.type, child))  # include element object

#             if recursive and child.type and child.type.is_complex():
#                 paths.extend(collect_xpaths(child.type, current_path, include_attributes, include_namespace, recursive))

#             if include_attributes and child.type and hasattr(child.type, "attributes") and child.type.attributes:
#                 for attr_name, attr in child.type.attributes.items():
#                     attr_display = attr.prefixed_name if include_namespace else attr.local_name
#                     paths.append((f"{current_path}/@{attr_display}", attr.type, attr))  # include attribute object

#     return paths


# === Enumeration Extraction ===
def get_enumerations(xsd_type):
    """Returns a list of enumeration values from an XSD type, if any."""
    if not xsd_type:
        return None

    if hasattr(xsd_type, "facets") and isinstance(xsd_type.facets.get("enumeration"), list):
        return [getattr(enum, "value", enum) for enum in xsd_type.facets["enumeration"]]

    if hasattr(xsd_type, "enumeration") and isinstance(xsd_type.enumeration, list):
        return [getattr(enum, "value", enum) for enum in xsd_type.enumeration]

    if hasattr(xsd_type, "content") and hasattr(xsd_type.content, "enumeration"):
        enum_list = xsd_type.content.enumeration
        if isinstance(enum_list, list):
            return [getattr(enum, "value", enum) for enum in enum_list]

    return None

# === Cardinality Extraction ===
def get_cardinality(xsd_obj):
    """Returns cardinality string like '0..1', '1..unbounded', etc."""
    min_occurs = getattr(xsd_obj, "min_occurs", 1)
    max_occurs = getattr(xsd_obj, "max_occurs", 1)
    max_str = "unbounded" if max_occurs is None else str(max_occurs)
    return f"{min_occurs}..{max_str}"

""" # === Main Execution ===
def main():
    schema = xmlschema.XMLSchema(xsd_path)
    target_type = schema.types.get(target_type_name)
    if target_type is None:
        raise ValueError(f"Complex type '{target_type_name}' not found in the schema!")

    # xpaths = collect_xpaths(
    #     target_type,
    #     include_attributes=output_attributes,
    #     include_namespace=output_namespaces,
    #     recursive=recursive_traversal
    # )

    xpaths = collect_xpaths(
        target_type,
        include_attributes=output_attributes,
        include_namespace=output_namespaces,
        recursive=recursive_traversal,
        excluded_children=excluded_children
    )


    total_xpaths_count = len(xpaths)
    total_xpaths_collected_count = 0
    output_file_type_suffix = ""
    
    if recursive_traversal:
        output_file_type_suffix = "_recursive"
    
    output_json_file = Path(f"xpaths_{target_type_name}{output_file_type_suffix}.json")
    output_txt_file = Path(f"xpaths_{target_type_name}.txt")

    output_file = output_json_file if output_file_type == "json" else output_txt_file

    with open(output_file, "w", encoding="utf-8") as f:
        if output_file_type == "json":
            f.write('{\n  "mismo_xpaths": [\n')

        for i, (xpath, xsd_type, xsd_obj) in enumerate(xpaths):
            # include_type_names = False          # Set to False to omit type names
            # include_enumeration_values = False          # Set to False to omit enumerations for type names
            # include_cardinality = False          # Set to False to omit cardinality
            # include_container = False          # Set to False to omit container name
            # include_endpoint = False          # Set to False to omit endpoint name
            # include_endpoint_type = False          # Set to False to omit endpoint type (Attribute, DataPoint, Enumeration, Container)            
            
            enum_values = get_enumerations(xsd_type) 
            type_name = xsd_type.local_name if xsd_type and hasattr(xsd_type, "local_name") else None
            type_str = f'"{type_name}"' 
            card_str = f'"{get_cardinality(xsd_obj)}"' 

            # Extract endpoint and container names from XPath
            segments = xpath.split("/")

            endpoint_name = segments[-1].replace("@", "") 
            container_name = segments[-2].strip() if len(segments[-2].strip()) > 1 else target_type_name

            # Determine endpoint type
            if segments[-1].startswith("@"):
                endpoint_type="Attribute"
            elif container_name == "EXTENSION":
                endpoint_type="Container"
            elif type_name.startswith("MISMO"):
                endpoint_type="DataPoint"
            
            elif segments[-1].endswith("Type"):
                endpoint_type="Enumeration"
            else:
                endpoint_type="Container"
            
            if output_file_type == "json":
                entry_parts = []
                
                entry_parts.append(f'"xpath": "/{target_type_name}{xpath}"')

                if include_endpoint_type:
                    entry_parts.append(f'"endpoint_type": "{endpoint_type}"')
                if include_type_names:
                    entry_parts.append(f'"schema_defined_type": {type_str}')
                if include_container:
                    entry_parts.append(f'"container": "{container_name}"')
                if include_endpoint:
                    entry_parts.append(f'"endpoint": "{endpoint_name}"')
                if include_cardinality:
                    entry_parts.append(f'"cardinality": {card_str}')   
                    
                if enum_values and include_enumeration_values:
                    enum_str = "[" + ", ".join(f'"{val}"' for val in enum_values) + "]"
                    entry_parts.append(f'"enumerations": {enum_str}')
                
                comma = ""
                if i < len(xpaths) - 1:
                    if limit_output_for_testing and i >= list_output_limit:
                        comma = ""
                    else:
                        comma = "," 

                f.write(f'  {{ {", ".join(entry_parts)} }}{comma}\n')

            if output_file_type == "txt":
                f.write(f'/{target_type_name}{xpath}\n')

            total_xpaths_collected_count = i + 1
            if limit_output_for_testing and i >= list_output_limit:
                break

        if output_file_type == "json":
            f.write("  ]\n}")

    print(f"\n✅ Done! {total_xpaths_collected_count} of {total_xpaths_count} records written to '{output_file}'") """
import csv
from pathlib import Path

# === Main Execution ===
def main():
    schema = xmlschema.XMLSchema(xsd_path)
    target_type = schema.types.get(target_type_name)
    if target_type is None:
        raise ValueError(f"Complex type '{target_type_name}' not found in the schema!")

    xpaths = collect_xpaths(
        target_type,
        include_attributes=output_attributes,
        include_namespace=output_namespaces,
        recursive=recursive_traversal,
        excluded_children=excluded_children
    )

    total_xpaths_count = len(xpaths)
    total_xpaths_collected_count = 0
    output_file_type_suffix = "_recursive" if recursive_traversal else ""

    #output_file = Path(f"{output_folder}xpaths_{target_type_name}{output_file_type_suffix}.{output_file_type}")
    output_folder = Path(__file__).resolve().parent.parent / "xpaths-search-results"
    output_folder.mkdir(exist_ok=True)  # Ensure the folder exists

    output_file_type_suffix = "_recursive" if recursive_traversal else ""
    output_file = output_folder / f"xpaths_{target_type_name}{output_file_type_suffix}.{output_file_type}"

    # === Prepare CSV Header ===
    csv_fields = ["xpath"]
    if include_endpoint_type: csv_fields.append("endpoint_type")
    if include_type_names: csv_fields.append("schema_defined_type")
    
    if include_container: csv_fields.append("container")
    if include_endpoint: csv_fields.append("endpoint")
    if include_cardinality: csv_fields.append("cardinality")
    if include_enumeration_values: csv_fields.append("enumerations")

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        if output_file_type == "json":
            f.write('{\n  "mismo_xpaths": [\n')

        elif output_file_type == "csv":
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writeheader()

        for i, (xpath, xsd_type, xsd_obj) in enumerate(xpaths):
            enum_values = get_enumerations(xsd_type)
            type_name = xsd_type.local_name if xsd_type and hasattr(xsd_type, "local_name") else None
            card_str = get_cardinality(xsd_obj)

            segments = xpath.split("/")
            endpoint_name = segments[-1].replace("@", "")
            container_name = segments[-2].strip() if len(segments[-2].strip()) > 1 else target_type_name

            if segments[-1].startswith("@"):
                endpoint_type = "Attribute"
            elif container_name == "EXTENSION":
                endpoint_type = "Container"
            elif type_name and type_name.startswith("MISMO"):
                endpoint_type = "DataPoint"
            elif segments[-1].endswith("Type"):
                endpoint_type = "Enumeration"
            else:
                endpoint_type = "Container"

            # === Build Entry Dict ===
            entry = {"xpath": f"/{target_type_name}{xpath}"}
            if include_endpoint_type: entry["endpoint_type"] = endpoint_type
            if include_type_names: entry["schema_defined_type"] = type_name
            if include_container: entry["container"] = container_name
            if include_endpoint: entry["endpoint"] = endpoint_name
            if include_cardinality: entry["cardinality"] = card_str
            if enum_values and include_enumeration_values:
                entry["enumerations"] = ", ".join(enum_values)

            # === Write Entry ===
            if output_file_type == "json":
                entry_str = ", ".join(f'"{k}": "{v}"' for k, v in entry.items())
                comma = "," if i < len(xpaths) - 1 and not (limit_output_for_testing and i >= list_output_limit) else ""
                f.write(f'  {{ {entry_str} }}{comma}\n')

            elif output_file_type == "csv":
                writer.writerow(entry)

            total_xpaths_collected_count = i + 1
            if limit_output_for_testing and i >= list_output_limit:
                break

        if output_file_type == "json":
            f.write("  ]\n}")

    print(f"\n✅ Done! {total_xpaths_collected_count} of {total_xpaths_count} records written to '{output_file}'")

if __name__ == "__main__":
    main()