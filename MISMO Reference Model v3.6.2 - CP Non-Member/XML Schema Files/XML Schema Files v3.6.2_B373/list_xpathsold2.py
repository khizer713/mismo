import xmlschema
import json
from pathlib import Path

def collect_xpaths(xsd_type, parent_path="", include_attributes=True, include_namespace=True):
    """Recursively collect all element XPaths under a complex type, with optional attributes and namespace."""
    paths = []

    if hasattr(xsd_type, "content") and hasattr(xsd_type.content, "iter_elements"):
        for child in xsd_type.content.iter_elements():
            if child.name is None:
                continue

            name = child.prefixed_name if include_namespace else child.local_name
            current_path = f"{parent_path}/{name}" if parent_path else f"/{name}"
            paths.append((current_path, child.type))  # include type for enumeration lookup

            if child.type and child.type.is_complex():
                paths.extend(collect_xpaths(child.type, current_path, include_attributes, include_namespace))

            if include_attributes and child.type and hasattr(child.type, "attributes") and child.type.attributes:
                for attr_name, attr in child.type.attributes.items():
                    attr_display = attr.prefixed_name if include_namespace else attr.local_name
                    paths.append((f"{current_path}/@{attr_display}", attr.type))

    return paths

def get_enumerations(xsd_type):
    """Returns a list of enumeration values from an XSD type, if any."""
    if not xsd_type:
        return None

    # Check direct enumeration facet
    if hasattr(xsd_type, "facets") and "enumeration" in xsd_type.facets:
        return [enum.value for enum in xsd_type.facets["enumeration"]]

    # Check .enumeration attribute
    if hasattr(xsd_type, "enumeration") and xsd_type.enumeration:
        return [enum.value for enum in xsd_type.enumeration]

    # Check restriction content
    if hasattr(xsd_type, "content") and hasattr(xsd_type.content, "enumeration"):
        return [enum.value for enum in xsd_type.content.enumeration]

    return None

def format_xpaths_with_enums(xsd_path, target_type_name, include_attributes=True, include_namespace=True):
    """Generates a JSON object mapping XPath names to enumeration values (if any)."""
    schema = xmlschema.XMLSchema(xsd_path)
    target_type = schema.types.get(target_type_name)
    if target_type is None:
        raise ValueError(f"Complex type '{target_type_name}' not found in the schema!")

    xpaths = collect_xpaths(target_type, include_attributes=include_attributes, include_namespace=include_namespace)

    result = {}
    #print(f"First Xpath {xpaths[0]}")

    # for xpath, xsd_type in xpaths:
    #     enums = None
    #     #print(f"{xpath}: {enums}")
    #     if xsd_type and hasattr(xsd_type, "facets") and "enumeration" in xsd_type.facets:
    #         enums = ", ".join(enum.value for enum in xsd_type.facets["enumeration"])
    #     result[xpath] = enums
    #     #print(f"{xpath}: {enums}")

    for xpath, xsd_type in xpaths:
        enum_values = get_enumerations(xsd_type)
        result[xpath] = enum_values if enum_values else None
    
    return result
    
xsd_path = 'MISMO_3.6.2_B373.xsd'
target_type_name = "BORROWER"
output_attributes = False
output_namespaces = False
# limit_output_for_testing=True  # Set to True to limit output for testing purposes
# list_output_limit=1000  # Limit for testing

json_output = format_xpaths_with_enums(
    xsd_path,
    target_type_name,
    include_attributes=output_attributes,
    include_namespace=output_namespaces
)

# Save to file
output_file = Path(f"xpaths_enums_{target_type_name}.json")
total_xpaths_count = len(json_output)
total_xpaths_collected_count =0

# Save to file original
output_file = Path(f"xpaths_enums_{target_type_name}.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(json_output, f, indent=2)

print(f"\n✅ Done! JSON output written to '{output_file}'")


# Save to file new
# # --- Write first xx (for testing) ---
# with open(output_file, "w", encoding="utf-8") as f:
#     for i, path in enumerate(json_output):
#         f.write("/"+target_type_name + path + "\n")
#         print("/"+target_type_name + path)
#         if i >= list_output_limit and limit_output_for_testing == True:  # Limit output for testing
#             total_xpaths_collected_count = i    + 1 
#             break
#         else:    
#             total_xpaths_collected_count = i    + 1 

#print(f"\n✅ Done! Wrote first {total_xpaths_collected_count} of {total_xpaths_count} XPaths from complex type '{target_type_name}' to '{output_file}'")