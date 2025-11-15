import xmlschema
from pathlib import Path

# Path to your MISMO XSD file
xsd_path = 'MISMO_3.6.2_B373.xsd'  # Change this to your actual file name

# The complex type name you want to extract XPaths for
target_type_name = "DEAL"  # <-- change to desired type

# Output file
output_file = Path(f"xpaths_{target_type_name}.txt")
output_attributes=False  # Set to True to include attributes in the output
output_namespaces=False  # Set to True to include namespaces in the output
limit_output_for_testing=True  # Set to True to limit output for testing purposes
list_output_limit=1000  # Limit for testing

# Load schema
schema = xmlschema.XMLSchema(xsd_path)


def collect_xpaths(xsd_type, parent_path="", include_attributes=output_attributes, include_namespace=output_namespaces):
    """Recursively collect all element XPaths under a complex type, with optional attributes and namespace."""
    paths = []

    if hasattr(xsd_type, "content") and hasattr(xsd_type.content, "iter_elements"):
        for child in xsd_type.content.iter_elements():
            if child.name is None:
                continue  # skip unnamed elements

            # Format element name with or without namespace
            name = child.prefixed_name if include_namespace else child.local_name
            current_path = f"{parent_path}/{name}" if parent_path else f"/{name}"
            paths.append(current_path)

            # Recurse into complex children
            if child.type and child.type.is_complex():
                paths.extend(collect_xpaths(child.type, current_path, include_attributes, include_namespace))

            # Optionally include attributes
            if include_attributes and child.type and hasattr(child.type, "attributes") and child.type.attributes:
                for attr_name, attr in child.type.attributes.items():
                    attr_display = attr.prefixed_name if include_namespace else attr.local_name
                    paths.append(f"{current_path}/@{attr_display}")

    return paths


# --- Find the complex type ---
target_type = schema.types.get(target_type_name)
if target_type is None:
    raise ValueError(f"Complex type '{target_type_name}' not found in the schema!")

# --- Collect all XPaths under that complex type ---
xpaths = collect_xpaths(target_type, include_attributes=output_attributes, include_namespace=output_namespaces)

total_xpaths_count = len(xpaths)
total_xpaths_collected_count =0

# --- Write first xx (for testing) ---
with open(output_file, "w", encoding="utf-8") as f:
    for i, path in enumerate(xpaths):
        f.write("/"+target_type_name + path + "\n")
        print("/"+target_type_name + path)
        if i >= list_output_limit and limit_output_for_testing == True:  # Limit output for testing
            total_xpaths_collected_count = i    + 1 
            break
        else:    
            total_xpaths_collected_count = i    + 1 

print(f"\n✅ Done! Wrote first {total_xpaths_collected_count} of {total_xpaths_count} XPaths from complex type '{target_type_name}' to '{output_file}'")

def list_enumerations(xsd_type):
    """
    Lists enumeration values for a given XSD type if available.
    
    Args:
        xsd_type: xmlschema.XsdType object
    
    Returns:
        Dict[str, List[str]]: Mapping of element/attribute names to their enumerated values
    """
    enums = {}

    if hasattr(xsd_type, "content") and hasattr(xsd_type.content, "iter_elements"):
        for child in xsd_type.content.iter_elements():
            if child.name is None or child.type is None:
                continue

            # Check for enumeration facets
            if hasattr(child.type, "facets") and "enumeration" in child.type.facets:
                enums[child.name] = [enum.value for enum in child.type.facets["enumeration"]]

    return enums
