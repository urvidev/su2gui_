#!/usr/bin/env python

## \file variables.py
#  \brief Variable and derived parameter management for SU2 configuration
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
from pathlib import Path

# Add parent directory to path to allow importing from sibling directories
parent_dir = str(Path(__file__ ).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ui.uicard import ui_card, ui_subcard, server
from core.logger import log

state, ctrl = server.state, server.controller

# Initialize variables and derived parameters in state
if not hasattr(state, 'variables'):
    state.variables = {}

if not hasattr(state, 'derived_parameters'):
    state.derived_parameters = {}

def add_variable(name, value, description=""):
    """
    Add a variable to the state.
    
    Parameters:
    -----------
    name : str
        The name of the variable (e.g., '__WIDTH__')
    value : float or str
        The value of the variable
    description : str, optional
        A description of the variable
    """
    state.variables[name] = {
        'value': value,
        'description': description
    }
    log("info", f"Added variable: {name} = {value}")
    state.dirty('variables')

def update_variable(name, value):
    """
    Update an existing variable in the state.
    
    Parameters:
    -----------
    name : str
        The name of the variable to update
    value : float or str
        The new value of the variable
    """
    if name in state.variables:
        state.variables[name]['value'] = value
        log("info", f"Updated variable: {name} = {value}")
        state.dirty('variables')
    else:
        log("error", f"Variable {name} does not exist")

def remove_variable(name):
    """
    Remove a variable from the state.
    
    Parameters:
    -----------
    name : str
        The name of the variable to remove
    """
    if name in state.variables:
        del state.variables[name]
        log("info", f"Removed variable: {name}")
        state.dirty('variables')
    else:
        log("error", f"Variable {name} does not exist")

def add_derived_parameter(name, definition, description=""):
    """
    Add a derived parameter to the state.
    
    Parameters:
    -----------
    name : str
        The name of the derived parameter (e.g., 'p_drop')
    definition : str
        The definition of the derived parameter (e.g., 'p_out - p_in')
    description : str, optional
        A description of the derived parameter
    """
    state.derived_parameters[name] = {
        'definition': definition,
        'description': description
    }
    log("info", f"Added derived parameter: {name} = {definition}")
    state.dirty('derived_parameters')

def update_derived_parameter(name, definition):
    """
    Update an existing derived parameter in the state.
    
    Parameters:
    -----------
    name : str
        The name of the derived parameter to update
    definition : str
        The new definition of the derived parameter
    """
    if name in state.derived_parameters:
        state.derived_parameters[name]['definition'] = definition
        log("info", f"Updated derived parameter: {name} = {definition}")
        state.dirty('derived_parameters')
    else:
        log("error", f"Derived parameter {name} does not exist")

def remove_derived_parameter(name):
    """
    Remove a derived parameter from the state.
    
    Parameters:
    -----------
    name : str
        The name of the derived parameter to remove
    """
    if name in state.derived_parameters:
        del state.derived_parameters[name]
        log("info", f"Removed derived parameter: {name}")
        state.dirty('derived_parameters')
    else:
        log("error", f"Derived parameter {name} does not exist")

def get_variables_dict():
    """
    Get a dictionary of variable names and values.
    
    Returns:
    --------
    dict
        A dictionary where keys are variable names and values are variable values
    """
    return {name: var['value'] for name, var in state.variables.items()}

def get_derived_parameters_dict():
    """
    Get a dictionary of derived parameter names and definitions.
    
    Returns:
    --------
    dict
        A dictionary where keys are derived parameter names and values are definitions
    """
    return {name: param['definition'] for name, param in state.derived_parameters.items()}

def substitute_variables(text, variables=None):
    """
    Substitute variables in a text string.
    
    Parameters:
    -----------
    text : str
        The text string containing variable placeholders
    variables : dict, optional
        A dictionary of variable names and values to use for substitution.
        If None, uses the variables from state.
    
    Returns:
    --------
    str
        The text with variables substituted
    """
    if variables is None:
        variables = get_variables_dict()
    
    result = text
    for var_name, var_value in variables.items():
        result = result.replace(var_name, str(var_value))
    
    return result

# Initialize with some example variables and derived parameters
# if not state.variables:
#     add_variable('__WIDTH__', 0.055, 'Channel width')
#     add_variable('__AMPLITUDE__', 0.045, 'Deformation amplitude')

# if not state.derived_parameters:
#     add_derived_parameter('p_tot', 'PRESSURE + 0.5 * DENSITY * (pow(VELOCITY_X, 2) + pow(VELOCITY_Y, 2))', 'Total pressure')
#     add_derived_parameter('p_drop', 'p_out - p_in', 'Pressure drop')
