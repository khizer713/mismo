import xmlschema
import json
from pathlib import Path

# === Configuration ===
xsd_path = 'MISMO_3.6.2_B373.xsd'  # Path to your XSD file
target_type_name = "BORROWER"      # Complex type to extract from
output_attributes = False          # Include attributes in XPath output
output_namespaces = False          # Include namespaces in XPath output
include_type_names = True  # Set to False to omit type names
output_file_type = "json"  # Options: "json", "txt"
output_json_file = Path(f"xpaths_{target_type_name}.json")
output_txt_file = Path(f"xpaths_{target_type_name}.txt")
limit_output_for_testing=False  # Set to True to limit output for testing purposes
list_output_limit=1000  # Limit for testing

# === XPath Collection ===
def collect_xpaths(xsd_type, parent_path="", include_attributes=True, include_namespace=True):
    """Recursively collect all element and attribute XPaths under a complex type."""
    paths = []

    if hasattr(xsd_type, "content") and hasattr(xsd_type.content, "iter_elements"):
        for child in xsd_type.content.iter_elements():
            if child.name is None:
                continue

            name = child.prefixed_name if include_namespace else child.local_name
            current_path = f"{parent_path}/{name}" if parent_path else f"/{name}"
            paths.append((current_path, child.type))

            if child.type and child.type.is_complex():
                paths.extend(collect_xpaths(child.type, current_path, include_attributes, include_namespace))

            if include_attributes and child.type and hasattr(child.type, "attributes") and child.type.attributes:
                for attr_name, attr in child.type.attributes.items():
                    attr_display = attr.prefixed_name if include_namespace else attr.local_name
                    paths.append((f"{current_path}/@{attr_display}", attr.type))

    return paths


# === Enumeration Extraction ===
def get_enumerations(xsd_type):
    """Returns a list of enumeration values from an XSD type, if any."""
    if not xsd_type:
        return None

    # Case 1: facets["enumeration"] is a list of objects with .value
    if hasattr(xsd_type, "facets") and isinstance(xsd_type.facets.get("enumeration"), list):
        return [getattr(enum, "value", enum) for enum in xsd_type.facets["enumeration"]]

    # Case 2: xsd_type.enumeration is a list of strings or objects
    if hasattr(xsd_type, "enumeration") and isinstance(xsd_type.enumeration, list):
        return [getattr(enum, "value", enum) for enum in xsd_type.enumeration]

    # Case 3: xsd_type.content.enumeration is a list of strings or objects
    if hasattr(xsd_type, "content") and hasattr(xsd_type.content, "enumeration"):
        enum_list = xsd_type.content.enumeration
        if isinstance(enum_list, list):
            return [getattr(enum, "value", enum) for enum in enum_list]

    return None

def get_cardinality(xsd_obj):
    """Returns cardinality string like '0..1', '1..unbounded', etc."""
    min_occurs = getattr(xsd_obj, "min_occurs", 1)
    max_occurs = getattr(xsd_obj, "max_occurs", 1)

    #max_str = "unbounded" if max_occurs is None else str(max_occurs)
    return f"{min_occurs}..{max_occurs}"

# === Main Execution ===
def main():
    schema = xmlschema.XMLSchema(xsd_path)
    target_type = schema.types.get(target_type_name)
    if target_type is None:
        raise ValueError(f"Complex type '{target_type_name}' not found in the schema!")

    xpaths = collect_xpaths(
        target_type,
        include_attributes=output_attributes,
        include_namespace=output_namespaces
    )

    total_xpaths_count = len(xpaths)
    total_xpaths_collected_count =0

    # result = {}
    # for xpath, xsd_type in xpaths:
    #     enum_values = get_enumerations(xsd_type)
    #     result[xpath] = enum_values if enum_values else None

    result = {}
    for xpath, xsd_type in xpaths:
        enum_values = get_enumerations(xsd_type)
        entry = {}

        if include_type_names:
            entry["type"] = xsd_type.name if xsd_type and hasattr(xsd_type, "name") else None

        entry["enumerations"] = enum_values if enum_values else None
        result[xpath] = entry


    # with open(output_file, "w", encoding="utf-8") as f:
    #     json.dump(result, f, indent=2)

    if output_file_type in ("json"):
        output_file=output_json_file   

    if output_file_type in ("txt"):
        output_file=output_txt_file

   # Write to file manually as plain text
    with open(output_file, "w", encoding="utf-8") as f:
        if output_file_type in ("json"):
            f.write("{\n")

        for i, (xpath, xsd_type) in enumerate(xpaths):
            enum_values = get_enumerations(xsd_type)

            # Get type name without namespace
            type_name = xsd_type.local_name if xsd_type and hasattr(xsd_type, "local_name") else None
            type_str = f'"{type_name}"' if include_type_names else "null"

            # Get cardinality from the element or attribute object
            cardinality = get_cardinality(xsd_type)
            card_str = f'"{cardinality}"'

            if output_file_type in ("json"):
                entry_parts = [f'"type": {type_str}', f'"Cardinality": {card_str}']
                
                if enum_values:
                    enum_str = "[" + ", ".join(f'"{val}"' for val in enum_values) + "]"
                    entry_parts.append(f'"enumerations": {enum_str}')
                
                comma = "," if i < len(xpaths) - 1 else ""
                
                f.write(f'  "{xpath}": {{ {", ".join(entry_parts)} }}{comma}\n')

                # enum_value_str = ""
                # enum_name_string = ""
                # if enum_values:
                #     enum_name_string= ", \"enumerations\": "
                #     enum_value_str = (
                #     "[" + ", ".join(f'"{val}"' for val in enum_values) + "]"
                #     if enum_values else "null"
                #     )

                # comma = "," if i < len(xpaths) - 1 else ""
                # f.write(f'  "/{target_type_name}{xpath}": {{ "type": {type_str}, "Cardinality": {cardinality} {enum_name_string}{enum_value_str} }}{comma}\n')

            if output_file_type in ("txt"):
                f.write(f'/{target_type_name}{xpath}\n')

            total_xpaths_collected_count=i  + 1

            if i >= list_output_limit and limit_output_for_testing == True:  # Limit output for testing
                break

        if output_file_type in ("json"):
            f.write("}\n")

    print(f"\n✅ Done! {total_xpaths_collected_count} of {total_xpaths_count} records written to '{output_file}'")


if __name__ == "__main__":
    main()