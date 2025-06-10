#!/usr/bin/env python

## \file su2_py_wrapper.py
#  \brief Python wrapper generator for SU2 configuration files
#  \version 1.0.0
#
# SU2 Project Website: https://su2code.github.io
#
# The SU2 Project is maintained by the SU2 Foundation
# (http://su2foundation.org )
#
# Copyright 2012-2025, SU2 Contributors (cf. AUTHORS.md)
#
# SU2 is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# SU2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with SU2. If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import json
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__ ).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from core.su2_json import *
from core.logger import log

BASE = Path(__file__).parent.parent

def generate_python_wrapper(json_data, filename_py_export, variables=None, derived_parameters=None):
    """
    Generate a Python wrapper script from SU2 JSON configuration data.
    
    Parameters:
    -----------
    json_data : dict
        The SU2 configuration data in JSON format
    filename_py_export : str
        The filename for the generated Python wrapper script
    variables : dict, optional
        Dictionary of variables to be used in the script (e.g., {"__WIDTH__": 0.055})
    derived_parameters : dict, optional
        Dictionary of derived parameters and their definitions
    """
    if variables is None:
        variables = {}
    
    if derived_parameters is None:
        derived_parameters = {}
    
    log("info", "Generating Python wrapper script")
    log("info", f"Output file: {filename_py_export}")
    
    # Create the output directory if it doesn\\'t exist
    output_dir = BASE / "user" / state.case_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / filename_py_export, 'w') as f:
        # Write file header
        f.write("""#!/usr/bin/env python

## \\\\file run_su2.py
#  \\\\brief Python wrapper for SU2 configuration
#  \\\\version 1.0.0
#
# SU2 Project Website: https://su2code.github.io
#
# The SU2 Project is maintained by the SU2 Foundation
# (http://su2foundation.org )
#
# Copyright 2012-2025, SU2 Contributors (cf. AUTHORS.md)
#
# SU2 is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# SU2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with SU2. If not, see <http://www.gnu.org/licenses/>.

import pysu2
import numpy as np
from mpi4py import MPI
import math
import os
import sys

""" )

        # Write variables section
        if variables:
            f.write("# Variables\\n")
            for var_name, var_value in variables.items():
                f.write(f"{var_name} = {var_value}\\n")
            f.write("\\n")

        # Write derived parameters section
        if derived_parameters:
            f.write("# Derived parameters\\n")
            for param_name, param_def in derived_parameters.items():
                f.write(f"def calculate_{param_name}(driver):\\n")
                f.write(f'    """{param_def}"""\n')
                f.write(f"    # TODO: Implement calculation for {param_name}\\n")
                f.write(f"    return 0.0\\n\\n")

        # Write configuration string
        f.write("# Configuration settings\\n")
        f.write("config_settings = \"\"\"\n")
        
        # Convert JSON data to configuration string
        for attribute, value in json_data.items():
            # Skip None values
            if value is None or (isinstance(value, str) and value.lower() == 'none'):
                continue
                
            # Convert boolean values
            if isinstance(value, bool):
                value = "YES" if value else "NO"
                
            # Handle lists and lists of lists
            elif isinstance(value, list):
                flat_list = []
                for sublist in value:
                    if isinstance(sublist, list):
                        for item in sublist:
                            flat_list.append(item)
                    else:
                        flat_list.append(sublist)
                
                # Replace variable placeholders if they exist
                flat_list_str = []
                for item in flat_list:
                    item_str = str(item)
                    for var_name, var_value in variables.items():
                        if var_name in item_str:
                            item_str = item_str.replace(var_name, str(var_value))
                flat_list_str.append(item_str)
                
                flatlist = ', '.join(flat_list_str)
                value = "(" + flatlist + ")"
            
            # Replace variable placeholders in string values
            elif isinstance(value, str):
                for var_name, var_value in variables.items():
                    if var_name in value:
                        value = value.replace(var_name, str(var_value))
            
            # Write the configuration option
            f.write(f"{attribute}= {value}\\n")
        
        f.write('"""\n\n')

        # Write main function
        f.write("""def main():
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    
    # Write configuration to file
    if rank == 0:
        with open(\'config.cfg\', \'w\') as f:
            f.write(config_settings)
    comm.Barrier()
    
    # Initialize the SU2 driver
    try:
        driver = pysu2.CSinglezoneDriver(\'config.cfg\', 1, comm)
    except TypeError as exception:
        print(\'A TypeError occurred in pysu2.CSinglezoneDriver:\', exception)
        raise
    
    # Run the solver
    driver.StartSolver()
    
    # Process results
    # TODO: Add custom result processing here
    
    # Finalize the solver and exit cleanly
    driver.Finalize()
    
    print("\\\\n------------------------------ Solver Completed -----------------------------\\\\n")

if __name__ == \'__main__\':
    main()
""")
    
    log("info", f"Python wrapper script generated: {output_dir / filename_py_export}")
    return output_dir / filename_py_export

def save_json_cfg_py_file(filename_json_export, filename_cfg_export, filename_py_export, variables=None, derived_parameters=None):
    """
    Export the configuration as JSON, CFG, and Python wrapper files.
    
    This extends the existing save_json_cfg_file function to also generate a Python wrapper.
    
    Parameters:
    -----------
    filename_json_export : str
        The filename for the JSON export
    filename_cfg_export : str
        The filename for the CFG export
    filename_py_export : str
        The filename for the Python wrapper export
    variables : dict, optional
        Dictionary of variables to be used in the script
    derived_parameters : dict, optional
        Dictionary of derived parameters and their definitions
    """
    if state.case_name == None or state.case_name == "":
        log("info", "Case name is not defined, did not export the configuration file")
        return
    
    log("info", "Exporting files")
    log("info", f"Write config file: {filename_json_export}")
    log("info", f"Write config file: {filename_cfg_export}")
    log("info", f"Write Python wrapper: {filename_py_export}")
    
    state.counter = state.counter + 1
    log("info", f"Counter: {state.counter}")
    
    # Construct the boundaries using BCDictList
    createjsonMarkers()
    
    # Save the JSON file
    with open(BASE / "user" / state.case_name / filename_json_export, 'w') as jsonOutputFile:
        json.dump(state.jsonData, jsonOutputFile, sort_keys=True, indent=4, ensure_ascii=False)
    
    # Convert JSON to CFG file and save
    with open(BASE / "user" / state.case_name / filename_cfg_export, 'w') as f:
        f.write(f"{state.config_desc}\n")
        for attribute, value in state.jsonData.items():
            # Convert boolean values
            if isinstance(value, bool):
                value = "YES" if value else "NO"
            
            # Handle lists and lists of lists
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
            
            # Skip None values
            if value is None or (isinstance(value, str) and value.lower() == 'none'):
                continue
            
            filestring = str(attribute) + "= " + str(value) + "\n"
            f.write(filestring)
    
    # Generate the Python wrapper
    generate_python_wrapper(state.jsonData, filename_py_export, variables, derived_parameters)
