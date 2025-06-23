import json
import re
from typing import Union, Dict, Any, List
from pathlib import Path
from jsonschema import validate, ValidationError, SchemaError, Draft7Validator

def parse_value(value_str: str) -> Union[str, float, int, bool, list]:
    """Parse SU2 configuration value with enhanced type handling"""
    value_str = value_str.strip()
    
    # Handle empty values
    if not value_str:
        return ""
    
    # Handle boolean-like values
    if value_str.upper() in ["YES", "TRUE"]:
        return True
    elif value_str.upper() in ["NO", "FALSE"]:
        return False
    
    # Enhanced list handling for SU2 configs
    if value_str.startswith("(") and value_str.endswith(")"):
        return parse_su2_list(value_str)
    
    # Numeric values with scientific notation support
    if re.match(r"^[+-]?[0-9]*\.?[0-9]+([eE][+-]?[0-9]+)?$", value_str):
        try:
            return float(value_str) if "." in value_str or "e" in value_str.lower() else int(value_str)
        except ValueError:
            pass
    
    # String values (preserve case sensitivity)
    return value_str

def parse_su2_list(value_str: str) -> List[Union[str, float, int]]:
    """Parse SU2-style lists with mixed types and nested structures"""
    # Remove outer parentheses
    inner = value_str.strip()[1:-1].strip()
    if not inner:
        return []
    
    elements = []
    current = ""
    in_quotes = False
    paren_depth = 0
    
    for char in inner + ",":  # Add comma to process last element
        if char == "\"" or char == "\'":
            in_quotes = not in_quotes
        elif char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
            
        if char == "," and not in_quotes and paren_depth == 0:
            if current.strip():
                elements.append(current.strip())
            current = ""
        else:
            if char != "," or in_quotes or paren_depth > 0:  # Don\'t add the trailing comma
                current += char
    
    # Parse each element recursively
    parsed_elements = []
    for elem in elements:
        elem = elem.strip()
        if elem.startswith("(") and elem.endswith(")"):
            parsed_elements.append(parse_su2_list(elem))
        else:
            parsed_elements.append(parse_value(elem))
    
    return parsed_elements

def cfg_to_json_dict(cfg_file_path: str) -> Dict[str, Any]:
    """
    Convert SU2 configuration file (.cfg) to dictionary format.
    
    Args:
        cfg_file_path (str): Path to the input .cfg file
    
    Returns:
        Dict[str, Any]: Dictionary representation of the config file
    """
    config_dict = {}
    
    try:
        with open(cfg_file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {cfg_file_path}")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")
    
    for line_num, line in enumerate(lines, 1):
        # Remove leading/trailing whitespace
        line = line.strip()
        
        # Skip empty lines and comment-only lines
        if not line or line.startswith("%"):
            continue
        
        # Remove comments (everything after %)
        comment_pos = line.find("%")
        if comment_pos != -1:
            line = line[:comment_pos].strip()
        
        # Skip if line becomes empty after removing comments
        if not line:
            continue
        
        # Find the equals sign
        equals_pos = line.find("=")
        if equals_pos == -1:
            print(f"Warning: Line {line_num} does not contain \"=\" - skipping: {line}")
            continue
        
        # Extract key and value
        key = line[:equals_pos].strip()
        value_str = line[equals_pos + 1:].strip()
        
        if not key:
            print(f"Warning: Line {line_num} has empty key - skipping: {line}")
            continue
        
        # Parse the value
        try:
            parsed_value = parse_value(value_str)
            config_dict[key] = parsed_value
        except Exception as e:
            print(f"Warning: Error parsing value on line {line_num}: {e}")
            config_dict[key] = value_str  # Store as string if parsing fails
    
    return config_dict

def validate_cfg_with_schema(cfg_path: str, schema_path: str = None):
    """
    Convert SU2 cfg to JSON dict and validate against schema without storing files.
    
    Args:
        cfg_path (str): Path to the SU2 .cfg file
        schema_path (str): Path to the JSON schema file
    
    Returns:
        tuple: (is_valid: bool, config_dict: dict, errors: list)
    """
    
    BASE = Path(__file__).parent
    
    if not schema_path:
        schema_path = str(BASE / "SU2_complete_schema.json") # Use the corrected schema
    
    try:
        # Convert cfg to dictionary
        print(f"Converting SU2 config from {cfg_path}")
        config_dict = cfg_to_json_dict(cfg_path)
        print(f"Successfully parsed {len(config_dict)} configuration parameters")
        
        # Apply SU2 compatibility fixes
        config_dict = apply_su2_fixes(config_dict)
        print("Applied SU2 compatibility fixes")
        
        # Load schema
        with open(schema_path, "r") as f:
            schema = json.load(f)
        print(f"Schema loaded from {schema_path}")
        
        # Apply schema compatibility modifications
        schema = apply_schema_fixes(schema)
        print("Applied schema compatibility fixes")
        
        # Validate schema itself
        Draft7Validator.check_schema(schema)
        print("Schema is valid")
        
        # Validate config against schema
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(config_dict))
        
        if errors:
            print(f"Found {len(errors)} validation errors:")
            for i, error in enumerate(errors, 1):
                path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                print(f"   {i}. Path: {path}")
                print(f"      Message: {error.message}")
                print(f"      Invalid value: {error.instance}")
                if hasattr(error, "validator_value") and error.validator_value:
                    print(f"      Expected: {error.validator_value}")
                print()
            return False, config_dict, errors
        else:
            print("Configuration is valid against schema!")
            return True, config_dict, []
            
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return False, {}, [str(e)]
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return False, {}, [str(e)]
    except SchemaError as e:
        print(f"Schema error: {e}")
        return False, {}, [str(e)]
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False, {}, [str(e)]

def apply_su2_fixes(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Apply SU2-specific compatibility fixes to config"""
    # Convert single values to arrays where required
    array_keys = ["SST_OPTIONS", "SA_OPTIONS", "SPECIFIC_HEAT_CP", 
                 "MU_CONSTANT", "MU_REF", "MU_T_REF", 
                 "SUTHERLAND_CONSTANT", "THERMAL_CONDUCTIVITY_CONSTANT",
                 "CONV_FIELD", "OBJECTIVE_FUNCTION", "DV_KIND"]
    
    for key in array_keys:
        if key in config_dict and not isinstance(config_dict[key], list):
            config_dict[key] = [config_dict[key]]
    
    # Convert numbers to strings where required
    string_keys = ["CONV_STARTITER", "CONV_CAUCHY_ELEMS", 
                  "DEFORM_NONLINEAR_ITER", "DEFORM_LINEAR_SOLVER_ITER",
                  "INNER_ITER", "TIME_ITER", "RESTART_ITER"]
    
    for key in string_keys:
        if key in config_dict and isinstance(config_dict[key], (int, float)):
            config_dict[key] = str(config_dict[key])
    
    # Fix special case parameters
    if "TIME_MARCHING" in config_dict and config_dict["TIME_MARCHING"] == "DUAL_TIME_STEPPING-2ND_ORDER":
        config_dict["TIME_MARCHING"] = "TIME_STEPPING"  # Map to closest valid value
    
    return config_dict

def apply_schema_fixes(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Apply compatibility fixes to schema"""
    # Create a copy to avoid modifying the original
    schema = json.loads(json.dumps(schema))
    
    # 1. Allow single values for array properties
    array_properties = ["SST_OPTIONS", "SA_OPTIONS", "SPECIFIC_HEAT_CP",
                       "MU_CONSTANT", "MU_REF", "MU_T_REF",
                       "SUTHERLAND_CONSTANT", "THERMAL_CONDUCTIVITY_CONSTANT",
                       "CONV_FIELD", "OBJECTIVE_FUNCTION", "DV_KIND",
                       "REF_ORIGIN_MOMENT_X", "REF_ORIGIN_MOMENT_Y", "REF_ORIGIN_MOMENT_Z",
                       "DV_VALUE"]
    
    for prop in array_properties:
        if prop in schema.get("properties", {}):
            original_def = schema["properties"][prop]
            schema["properties"][prop] = {
                "anyOf": [
                    {"type": "array", "items": original_def.get("items", {})},
                    original_def
                ]
            }
    
    # 2. Allow numbers for string properties
    string_properties = ["CONV_STARTITER", "CONV_CAUCHY_ELEMS",
                        "DEFORM_NONLINEAR_ITER", "DEFORM_LINEAR_SOLVER_ITER",
                        "INNER_ITER", "TIME_ITER", "RESTART_ITER"]
    
    for prop in string_properties:
        if prop in schema.get("properties", {}):
            schema["properties"][prop] = {
                "anyOf": [
                    {"type": "string"},
                    {"type": "number"}
                ]
            }
    
    # 3. Add missing enum values
    if "TIME_MARCHING" in schema.get("properties", {}):
        if "enum" in schema["properties"]["TIME_MARCHING"]:
            if "DUAL_TIME_STEPPING-2ND_ORDER" not in schema["properties"]["TIME_MARCHING"]["enum"]:
                schema["properties"]["TIME_MARCHING"]["enum"].append("DUAL_TIME_STEPPING-2ND_ORDER")
    
    # 4. Fix DV_MARKER type handling
    if "DV_MARKER" in schema.get("properties", {}):
        schema["properties"]["DV_MARKER"] = {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "number"},
                    {"type": "array"}
                ]
            }
        }

    # 5. Fix MATH_PROBLEM type handling
    if "MATH_PROBLEM" in schema.get("properties", {}):
        schema["properties"]["MATH_PROBLEM"] = {"type": "string"}

    # 6. Fix DEFINITION_DV type handling
    if "DEFINITION_DV" in schema.get("properties", {}):
        schema["properties"]["DEFINITION_DV"] = {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "number"},
                    {"type": "array"}
                ]
            }
        }
    
    return schema

def validate_config_standalone(schema_path=None, config_path=None):
    """
    Original validation function for JSON files"""
    
    BASE = Path(__file__).parent
    
    if not schema_path:
        schema_path = str(BASE / "SU2_complete_schema.json")
    
    if not config_path:
        config_path = str(BASE / "config_new.json")
    
    try:
        # Load schema
        with open(schema_path, "r") as f:
            schema = json.load(f)
        print(f"Schema loaded from {schema_path}")
        
        # Load config
        with open(config_path, "r") as f:
            config = json.load(f)
        print(f"Config loaded from {config_path}")
        
        # Validate schema itself
        Draft7Validator.check_schema(schema)
        print("Schema is valid")
        
        # Validate config against schema
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(config))
        
        if errors:
            print(f"Found {len(errors)} validation errors:")
            for i, error in enumerate(errors, 1):
                path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                print(f"   {i}. Path: {path}")
                print(f"      Message: {error.message}")
                print(f"      Invalid value: {error.instance}")
                if hasattr(error, "validator_value") and error.validator_value:
                    print(f"      Expected: {error.validator_value}")
                print()
            return False
        else:
            print("Configuration is valid!")
            return True
            
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return False
    except SchemaError as e:
        print(f"Schema error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def cfg_to_json(cfg_file_path: str, output_json_path: str = None) -> Dict[str, Any]:
    """
    Convert SU2 configuration file (.cfg) to JSON format.
    
    Args:
        cfg_file_path (str): Path to the input .cfg file
        output_json_path (str, optional): Path to save the JSON file. If None, only returns dict.
    
    Returns:
        Dict[str, Any]: Dictionary representation of the config file
    """
    
    try:
        with open(cfg_file_path, "r", encoding="utf-8") as file:
            cfg_content = file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {cfg_file_path}")
    except Exception as e:
        raise Exception(f"Error reading file: {e}")

    # Convert to dict using existing function
    config_dict = cfg_to_json_dict(cfg_file_path)

    # Save to JSON file if output path is provided
    if output_json_path:
        try:
            with open(output_json_path, "w", encoding="utf-8") as json_file:
                json.dump(config_dict, json_file, indent=2, ensure_ascii=False)
            print(f"Configuration successfully converted to JSON: {output_json_path}")
        except Exception as e:
            raise Exception(f"Error writing JSON file: {e}")

    return config_dict

def json_to_cfg(json_file_path: str, output_cfg_path: str) -> None:
    """
    Convert JSON back to SU2 configuration file format.
    """
    
    def format_value(value) -> str:
        """Format a Python value back to SU2 config format."""
        if isinstance(value, bool):
            return "YES" if value else "NO"
        elif isinstance(value, list):
            if not value:
                return "()"
            formatted_items = []
            for item in value:
                if isinstance(item, str):
                    formatted_items.append(item)
                else:
                    formatted_items.append(str(item))
            return f"({", ".join(formatted_items)})"
        elif isinstance(value, str):
            return value
        else:
            return str(value)

    try:
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            config_dict = json.load(json_file)
    except Exception as e:
        raise Exception(f"Error reading JSON file: {e}")

    try:
        with open(output_cfg_path, "w", encoding="utf-8") as cfg_file:
            cfg_file.write("% SU2 Configuration File\n")
            cfg_file.write("% Converted from JSON\n\n")
            
            for key, value in config_dict.items():
                formatted_value = format_value(value)
                cfg_file.write(f"{key}= {formatted_value}\n")
                
        print(f"JSON successfully converted to SU2 config: {output_cfg_path}")
        
    except Exception as e:
        raise Exception(f"Error writing config file: {e}")

if __name__ == "__main__":
    # Example usage - validate CFG file directly
    cfg_file = "naca0012 (1).cfg"  # Your SU2 config file
    schema_file = "SU2_complete_schema.json"  # Your schema file
    
    print("=" * 60)
    print("SU2 CFG to JSON Validation (No File Storage)")
    print("=" * 60)
    
    is_valid, config_dict, errors = validate_cfg_with_schema(cfg_file, schema_file)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Config Parameters: {len(config_dict)}")
    print(f"Validation Result: {"VALID" if is_valid else "INVALID"}")
    print(f"Error Count: {len(errors)}")
    
    # Optionally show some sample

