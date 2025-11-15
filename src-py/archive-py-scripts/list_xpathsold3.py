import xmlschema
import json
from pathlib import Path

# === Configuration ===
xsd_path = 'MISMO_3.6.2_B373.xsd'  # Path to your XSD file
target_type_name = "BORROWER"      # Complex type to extract from
output_attributes = False          # Include attributes in XPath output
output_namespaces = False          # Include namespaces in XPath output
output_file = Path(f"xpaths_enums_{target_type_name}.json")


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

    result = {}
    for xpath, xsd_type in xpaths:
        enum_values = get_enumerations(xsd_type)
        result[xpath] = enum_values if enum_values else None

    # with open(output_file, "w", encoding="utf-8") as f:
    #     json.dump(result, f, indent=2)

    # Write to file manually as plain text
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("{\n")
        for i, (xpath, xsd_type) in enumerate(xpaths):
            enum_values = get_enumerations(xsd_type)
            if enum_values:
                enum_str = "[" + ", ".join(f'"{val}"' for val in enum_values) + "]"
            else:
                enum_str = "null"

            # Add comma except for last item
            comma = "," if i < len(xpaths) - 1 else ""
            f.write(f'  "{xpath}": {enum_str}{comma}\n')
        f.write("}\n")

    print(f"\n✅ Done! JSON output written to '{output_file}'")


if __name__ == "__main__":
    main()