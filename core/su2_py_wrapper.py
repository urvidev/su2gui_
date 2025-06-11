import sys
import os
import json
from pathlib import Path

parent_dir = str(Path(__file__ ).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from core.su2_json import *
from core.logger import log

BASE = Path(__file__).parent.parent

def generate_python_wrapper(json_data, filename_py_export, variables=None, derived_parameters=None):
    if variables is None:
        variables = {}
    
    if derived_parameters is None:
        derived_parameters = {}
    
    log("info", "Generating Python wrapper script")
    log("info", f"Output file: {filename_py_export}")
    
    output_dir = BASE / "user" / state.case_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / filename_py_export, 'w') as f:
        f.write("""#!/usr/bin/env python

import pysu2
import numpy as np
from mpi4py import MPI
import math
import os
import sys

""" )

        if variables:
            f.write("# Variables\n")
            for var_name, var_value in variables.items():
                f.write(f"{var_name} = {var_value}\n")
            f.write("\n")

        if derived_parameters:
            f.write("# Derived parameters\n")
            for param_name, param_def in derived_parameters.items():
                f.write(f"def calculate_{param_name}(driver):\n")
                f.write(f'    """{param_def}"""\n')
                f.write(f"    # TODO: Implement calculation for {param_name}\n")
                f.write(f"    return 0.0\n\n")

        f.write("# Configuration settings\n")
        f.write("config_settings = \"\"\"\n")
        
        for attribute, value in json_data.items():
            if value is None or (isinstance(value, str) and value.lower() == 'none'):
                continue
                
            if isinstance(value, bool):
                value = "YES" if value else "NO"
                
            elif isinstance(value, list):
                flat_list = []
                for sublist in value:
                    if isinstance(sublist, list):
                        for item in sublist:
                            flat_list.append(item)
                    else:
                        flat_list.append(sublist)
                
                flat_list_str = []
                for item in flat_list:
                    item_str = str(item)
                    for var_name, var_value in variables.items():
                        if var_name in item_str:
                            item_str = item_str.replace(var_name, str(var_value))
                    flat_list_str.append(item_str)
                
                flatlist = ', '.join(flat_list_str)
                value = "(" + flatlist + ")"
            
            elif isinstance(value, str):
                for var_name, var_value in variables.items():
                    if var_name in value:
                        value = value.replace(var_name, str(var_value))
            
            f.write(f"{attribute}= {value}\n")
        
        f.write('"""\n\n')

        f.write(
            
        )
    
    log("info", f"Python wrapper script generated: {output_dir / filename_py_export}")
    return output_dir / filename_py_export

def save_json_cfg_py_file(filename_json_export, filename_cfg_export, filename_py_export, variables=None, derived_parameters=None):
    if state.case_name == None or state.case_name == "":
        log("info", "Case name is not defined, did not export the configuration file")
        return
    
    log("info", "Exporting files")
    log("info", f"Write config file: {filename_json_export}")
    log("info", f"Write config file: {filename_cfg_export}")
    log("info", f"Write Python wrapper: {filename_py_export}")
    
    state.counter = state.counter + 1
    log("info", f"Counter: {state.counter}")
    
    createjsonMarkers()
    
    with open(BASE / "user" / state.case_name / filename_json_export, 'w') as jsonOutputFile:
        json.dump(state.jsonData, jsonOutputFile, sort_keys=True, indent=4, ensure_ascii=False)
    
    with open(BASE / "user" / state.case_name / filename_cfg_export, 'w') as f:
        f.write(f"{state.config_desc}\n")
        for attribute, value in state.jsonData.items():
            if isinstance(value, bool):
                value = "YES" if value else "NO"
            
            elif isinstance(value, list):
                flat_list = []
                for sublist in value:
                    if isinstance(sublist, list):
                        for item in sublist:
                            flat_list.append(item)
                    else:
                        flat_list.append(sublist)
                
                flatlist = ', '.join(str(e) for e in flat_list)
                value = "(" + flatlist + ")"
            
            if value is None or (isinstance(value, str) and value.lower() == 'none'):
                continue
            
            filestring = str(attribute) + "= " + str(value) + "\n"
            f.write(filestring)
    
    generate_python_wrapper(state.jsonData, filename_py_export, variables, derived_parameters)
