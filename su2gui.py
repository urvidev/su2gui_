r"""
The SU2 Graphical User Interface.
"""

import os, copy, io

import pandas as pd
import argparse

from trame.app import get_server
from trame.app.file_upload import ClientFile
from trame.widgets import markdown

from trame.ui.vuetify import SinglePageWithDrawerLayout
#from trame.ui.vuetify import SinglePageLayout
from trame.widgets import vuetify, vtk as vtk_widgets
from trame.widgets import trame

#import itertools
from datetime import date

# Import json setup for writing the config file in json and cfg file format.
from su2_json import *
# Export su2 mesh file.
from su2_io import save_su2mesh, save_json_cfg_file
#
from vtk_helper import *
# 
from output_files import update_download_dialog_card, download_diagol_card
#
# Definition of ui_card and the server.
from uicard import ui_card, server

import vtk
# vtm reader
#from paraview.vtk.vtkIOXML import vtkXMLMultiBlockDataReader
#from vtkmodules.web.utils import mesh as vtk_mesh
from vtkmodules.vtkCommonDataModel import vtkDataObject
#from vtkmodules.vtkFiltersCore import vtkContourFilter #noqa
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkRenderingAnnotation import vtkCubeAxesActor, vtkScalarBarActor
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget, vtkScalarBarWidget
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from vtkmodules.vtkCommonDataModel import (
    VTK_HEXAHEDRON,
    VTK_LINE,
    VTK_POLYGON,
    VTK_QUAD,
    VTK_TETRA,
    VTK_TRIANGLE,
    VTK_PYRAMID,
    VTK_WEDGE,
    VTK_TRIANGLE_STRIP,
    VTK_VERTEX,
    vtkUnstructuredGrid)

# Required for interactor initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa

# Required for rendering initialization, not necessary for
# local rendering, but doesn't hurt to include it
import vtkmodules.vtkRenderingOpenGL2  # noqa




#############################################################################
# Gittree menu                                                              #
# We have defined each of the tabs in its own module and we import it here. #
# We then call the card in the SinglePageWithDrawerLayout() function.       #
#############################################################################
# gittree menu : import mesh tab                                            #
from mesh import *
# gittree menu : import physics tab                                         #
from physics import *
# gittree menu : import materials tab                                       #
from materials import *
# gittree menu : import numerics tab                                        #
from numerics import *
# gittree menu : import boundaries tab                                      #
from boundaries import *
# gittree menu : import solver tab                                          #
from solver import *
# gittree menu : import initialization tab                                  #
from initialization import *
# gittree menu : import file I/O tab                                        #
from fileio import *
#############################################################################


# -----------------------------------------------------------------------------
# Trame setup
# -----------------------------------------------------------------------------
state, ctrl = server.state, server.controller

from pipeline import PipelineManager
from pathlib import Path
BASE = Path(__file__).parent

from trame.assets.local import LocalFileManager

print("****************************************")
print("* Base path = ", BASE                    )
print("****************************************")

state.filename_cfg_export = "config_new.cfg"
state.filename_json_export = "config_new.json"

# for server side, we need to use a file manager
local_file_manager = LocalFileManager(__file__)
local_file_manager.url("collapsed", BASE / "icons/chevron-up.svg")
local_file_manager.url("collapsible", BASE / "icons/chevron-down.svg")
local_file_manager.url("su2logo", BASE / "img/logoSU2small.png")

print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print("local_file_manager=",local_file_manager)
print("local_file_manager=",type(local_file_manager))
print("local_file_manager=",type(local_file_manager.assets))
print("local_file_manager=",dir(local_file_manager.assets.items()))
print("local_file_manager=",local_file_manager.assets.keys())
print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")


# matplotlib history
state.show_dialog = False

# TODO FIXME update from user input / cfg file
state.history_filename = 'history.csv'
state.restart_filename = 'restart.csv'

state.monitorLinesVisibility = []
state.monitorLinesNames = []
state.monitorLinesRange = []

# -----------------------------------------------------------------------------

# keep updating the graph (real-time update with asynchronous io)
state.keep_updating = True
state.countdown = True

# -----------------------------------------------------------------------------
# SU2 setup
# -----------------------------------------------------------------------------

# global iteration number while running a case
#state.global_iter = -1

state.initialize=-1
# number of dimensions of the mesh (2 or 3)
state.nDim = 2

# which boundary is selected?
state.selectedBoundaryName="none"
state.selectedBoundaryIndex = 0

# Boundary Condition Dictionary List
# This is the internal list of dictionaries for the boundary conditions
# This will be converted and written as MARKER info to .json and .cfg files.
state.BCDictList = [{"bcName": "main_wall",
                     "bcType":"Wall",
                     "bc_subtype":"Temperature",
                     "json":"MARKER_ISOTHERMAL",
                     "bc_velocity_magnitude":0.0,
                     "bc_temperature":300.0,
                     "bc_pressure":0,
                     "bc_density":0.0,
                     "bc_massflow":1.0,
                     "bc_velocity_normal":[1,0,0],
                     "bc_heatflux":0.0,
                     "bc_heattransfer":[1000.0,300.0],
                     }]
# disable the export file button
state.export_disabled=True

# (solver.py) disable the solve button
state.su2_solve_disabled=False

# solver settings
# current solver icon
state.solver_icon = "mdi-play-circle"
# current running state
state.solver_running = False

# the imported mesh block and boundary blocks
# must be state or else it cannot be an argument to click
state.su2_meshfile="mesh_out.su2"

# list of all the mesh actors (boundaries)
state.selectedBoundary = 0
mesh_actor_list = [{"id":0,"name":"internal","mesh":mesh_actor}]

# vtk named colors
colors = vtkNamedColors()


mesh_actor.SetMapper(mesh_mapper)
mesh_actor.SetObjectName("initial_square")

# Mesh: Setup default representation to surface
mesh_actor.GetProperty().SetRepresentationToSurface()
mesh_actor.GetProperty().SetPointSize(1)
# show the edges
mesh_actor.GetProperty().EdgeVisibilityOn()
# color is based on field values
renderer.AddActor(mesh_actor)




###################################
# ##### gradient background ##### #
###################################
# bottom: white
renderer.SetBackground(1., 1., 1.)
# top: light blue
renderer.SetBackground2(0.6, 0.8, 1.0)
# activate gradient background
renderer.GradientBackgroundOn()
###################################


# Extract Array/Field information
datasetArrays = []
name = "Solid"
ArrayObject = vtk.vtkFloatArray()
ArrayObject.SetName(name)
# all components are scalars, no vectors for velocity
ArrayObject.SetNumberOfComponents(1)
# how many elements do we have?
nElems = 1
ArrayObject.SetNumberOfValues(nElems)
nPoints = 4
ArrayObject.SetNumberOfTuples(4)


# Nijso: TODO FIXME very slow!
# this is the color of the initial square
#for i in range(nElems):
for i in range(nPoints):
  #ArrayObject.SetValue(i,1.0)
  ArrayObject.SetValue(i,1.0)

grid.GetPointData().AddArray(ArrayObject)
# as soon as we add the array, it is being used for coloring.

datasetArrays.append(
    {
        "text": name,
        "value": 0,
        "range": [1.0,1.0],
        "type": vtkDataObject.FIELD_ASSOCIATION_POINTS,
    }
)
default_array = datasetArrays[0]
default_min, default_max = default_array.get("range")
state.dataset_arrays= datasetArrays
print("dataset_arrays = ",state.dataset_arrays)

mesh_mapper.SetInputData(grid)
mesh_mapper.SelectColorArray(default_array.get("text"))
mesh_mapper.GetLookupTable().SetRange(default_min, default_max)
mesh_mapper.SetScalarModeToUsePointFieldData()
mesh_mapper.SetScalarVisibility(True)
mesh_mapper.SetUseLookupTableScalarRange(True)

# cube axes (bounded with length scales)
cube_axes = MakeCubeAxesActor()
renderer.AddActor(cube_axes)

# scalar bar
scalar_bar = MakeScalarBarActor()
scalar_bar_widget =MakeScalarBarWidget(scalar_bar)

# coordinate axes
axes1 = MakeAxesActor()
coord_axes = MakeOrientationMarkerWidget(axes1)


renderer.ResetCamera()





# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

pipeline = PipelineManager(state, "git_tree")

# main menu, note that only these are collapsible
# These are head nodes. boundary for instance are all subnodes sharing one head node
# note that subui points to a submenu. We can set it to an existing submenu, or point to "none"
# 1
id_root       = pipeline.add_node(                      name="Mesh",
                                  subui="none", visible=1, color="#9C27B0", actions=["collapsible"])
# 2
id_physics    = pipeline.add_node(parent=id_root,       name="Physics",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 3
id_materials  = pipeline.add_node(parent=id_physics,    name="Materials",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 4
id_numerics   = pipeline.add_node(parent=id_materials,  name="Numerics",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 5
id_boundaries = pipeline.add_node(parent=id_numerics,   name="Boundaries",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 6
id_initial    = pipeline.add_node(parent=id_boundaries, name="Initialization",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 7
id_monitor    = pipeline.add_node(parent=id_initial,    name="Monitor",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 8
id_fileio     = pipeline.add_node(parent=id_monitor,    name="File I/O",
                                  subui="none", visible=1, color="#42A5F5", actions=["collapsible"])
# 9
id_solver     = pipeline.add_node(parent=id_fileio,    name="Solver",
                                  subui="none", visible=1, color="#00ACC1", actions=["collapsible"])

# first node is active initially
state.selection=["1"]
# important for the interactive ui
state.setdefault("active_ui", "Mesh")
# for submesh
state.setdefault("active_subui", "submesh_none")
state.setdefault("active_parent_ui", "submesh_none")
state.setdefault("active_head_ui", "submesh_none")

pipeline.update()

# which node in the gittree is active
state.active_id=1
# which sub ui menu is active
state.active_sub_ui = "none"

# this counter is used for the gittree items that are added and removed to/from the gittree
state.counter = 0

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------


def actives_change(ids):
    print("actives_change::ids = ",ids)
    _id = ids[0]

    state.active_id = _id

    #state.boundaryText=_id
    print("actives_change::active id = ",state.active_id)
    # get boundary name belonging to ID
    _name = pipeline.get_node(_id)
    # get the headnode of this node
    _headnode = _name['headnode']
    print("headnode=",_headnode)
    print("active name =",_name['name'])


    # if the headnode = active_name, then we have selected the head node
    # if active_name != headnode, then we are a child of the headnode.
    if _headnode == _name['name']:
       print("   headnode =", _headnode)
       # we are at a headnode, so we do not have a parent id
       state.active_parent_ui = "none"
       state.active_head_ui = _headnode
    else:
       print("   we are at child node")
       state.active_parent_ui = _headnode
       # so headnode is none
       state.active_head_ui = "none"


    # check if we need to show a submenu
    _subui = _name['subui']
    # whatever the value, we update the pipeline with it
    state.active_sub_ui = _subui
    print("subnode=",_subui)

    print("children:",pipeline._children_map)

    _name = _name['name']
    print("active name =",_name)
    selectedBoundary = next((item for item in mesh_actor_list if item["name"] == _name), None)
    print("mesh_actor_list = ",mesh_actor_list)
    if not selectedBoundary==None:
      state.selectedBoundaryName = selectedBoundary["name"]
    else:
      # for 2D, show internal as default when we have not selected anything
      if state.nDim == 2:
        state.selectedBoundaryName = "internal"
      else:
        state.selectedBoundaryName = "None"

    print("selected boundary name = ",state.selectedBoundaryName)

    state.dirty('selectedBoundaryName')

    # nijso: hardcode internal as selected mesh
    #state.selectedBoundaryName = "internal"

    # get list of all actors, loop and color the selected actor
    actorlist = vtk.vtkActorCollection()
    actorlist = renderer.GetActors()
    actorlist.InitTraversal()

    # only if we have selected a boundary
    if _headnode!="Boundaries":
      print("************* headnode is not a boundary")
      for a in range(0, actorlist.GetNumberOfItems()):
        actor = actorlist.GetNextActor()
        print("actor name=",actor.GetObjectName())

        # ignore everything that is not a boundary, so CoordAxes and CubeAxes
        if ("Axes" in actor.GetObjectName()):
          continue

        # for 3D, no visualization of internal points
        if (state.nDim==3 and actor.GetObjectName()=="internal"):
          actor.VisibilityOff()
        else:
          # visualize everything
          # the color of the geometry when we are outside of the boundary gittree
          actor.VisibilityOn()
          actor.GetProperty().SetLineWidth(2)
          actor.GetProperty().RenderLinesAsTubesOn()
          actor.GetProperty().SetColor(colors.GetColor3d('floralwhite'))
    else:


      internal=False
      if state.selectedBoundaryName=="internal":
        print("internal selected")
        internal=True

      # ##### show/highlight the actor based on selection ##### #
      # we loop over all actors and switch it on or off
      for a in range(0, actorlist.GetNumberOfItems()):
        actor = actorlist.GetNextActor()
        print("actor name=",actor.GetObjectName())

        if ("Axes" in actor.GetObjectName()):
           continue

        actor.GetProperty().SetRoughness(0.5)
        actor.GetProperty().SetDiffuse(0.5)
        actor.GetProperty().SetAmbient(0.5)
        actor.GetProperty().SetSpecular(0.1)
        actor.GetProperty().SetSpecularPower(10)
        #print("getnextactor: name =",actor.GetObjectName())
        #print("ambient=",actor.GetProperty().GetAmbient())
        #print("diffuse=",actor.GetProperty().GetDiffuse())
        #print("specular=",actor.GetProperty().GetSpecular())
        #print("roughness=",actor.GetProperty().GetRoughness())


        if (state.nDim==3 and actor.GetObjectName()=="internal"):
          actor.VisibilityOff()
        elif actor.GetObjectName() == state.selectedBoundaryName:
            # current actor is selected, we highlight it
            actor.VisibilityOn()
            actor.GetProperty().SetLineWidth(4)
            actor.GetProperty().RenderLinesAsTubesOn()
            actor.GetProperty().SetColor(colors.GetColor3d('yellow'))
        else:
            actor.VisibilityOn()
            if (state.nDim==3 and internal==True):
              actor.GetProperty().SetLineWidth(2)
              actor.GetProperty().RenderLinesAsTubesOn()
              actor.GetProperty().SetColor(colors.GetColor3d('yellow'))
            else:
              actor.GetProperty().SetLineWidth(2)
              actor.GetProperty().RenderLinesAsTubesOn()
              actor.GetProperty().SetColor(colors.GetColor3d('floralwhite'))



    ctrl.view_update()

    print("state=",_id)

    # active ui is the head node of the gittree
    state.active_ui = _headnode

    # check if we need to show a subui

###############################################################
# PIPELINE CARD : BOUNDARY
###############################################################
state.meshText="meshtext"
#state.boundaryText="boundtext"
#state.selectedBoundaryName = "internal"






# export su2 file (save on the server)
def save_file_su2(su2_filename):
    print("********** save .su2 **********\n")
      # add the filename to the json database
    state.jsonData['MESH_FILENAME'] = su2_filename
    global root
    save_su2mesh(root,su2_filename)

@ctrl.trigger("download_file_su2")
def download_file_su2():
    print("********** download .su2 **********\n")
    su2_filename = state.jsonData['MESH_FILENAME']
    global root
    save_su2mesh(root,su2_filename)
    with open(BASE / "user" / su2_filename, 'r') as f:
      #su2_content = f.readlines()
      su2_content = f.read()
    return su2_content

@ctrl.trigger("download_file_cfg")
def download_file_cfg():
    print("********** download .cfg **********\n")
    with open(BASE / "user" / state.filename_cfg_export, 'r') as f:
      #cfg_content = f.readlines()
      cfg_content = f.read()
    return cfg_content


# Color By Callbacks
def color_by_array(actor, array):
    print("change color by array")

    _min, _max = array.get("range")
    mesh_mapper = actor.GetMapper()
    mesh_mapper.SelectColorArray(array.get("text"))
    mesh_mapper.GetLookupTable().SetRange(_min, _max)

    if array.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
        mesh_mapper.SetScalarModeToUsePointFieldData()
    else:
        mesh_mapper.SetScalarModeToUseCellFieldData()
    mesh_mapper.SetScalarVisibility(True)
    mesh_mapper.SetUseLookupTableScalarRange(True)

    lut = get_diverging_lut()
    lut.SetTableRange(_min,_max)
    mesh_mapper.SetLookupTable(lut)
    mesh_mapper.GetLookupTable().SetRange(_min, _max)
    actor.SetMapper(mesh_mapper)

    global scalar_bar
    global scalar_bar_widget
    scalar_bar = MakeScalarBarActor()
    scalar_bar_widget =MakeScalarBarWidget(scalar_bar)
    print("scalarbarwidget=",scalar_bar_widget)

@state.change("mesh_color_array_idx")
def update_mesh_color_by_name(mesh_color_array_idx, **kwargs):
    print("change mesh color by array")
    array =  {'text': 'Solid', 'value': 0, 'range': [1.0, 1.0], 'type': 0}
    if mesh_color_array_idx in state.dataset_arrays:
        array = state.dataset_arrays[mesh_color_array_idx]  
    print("array = ",array)
    print("mesh actor=",mesh_actor)
    print("mesh actor list=",mesh_actor_list)
    if state.nDim == 2:
      # color the internal
      #color_by_array(mesh_actor, array)
      if(len(mesh_actor_list)> 0 ):
        actor = get_entry_from_name('internal','name',mesh_actor_list)
      else:
        actor = get_entry_from_name('internal','name',[{"id":0,"name":"internal","mesh":mesh_actor}])
      print("start::actor=",actor['mesh'])
      color_by_array(actor['mesh'], array)
      print("end::actor=",actor['mesh'])
    else:
      # color all boundaries (all mesh actors that are not internal)
      for actor in mesh_actor_list:
        print("3D actor=",actor)
        print("3D actor=",actor['mesh'])
        if actor['name'] != 'internal':
          print("passing actor")
          color_by_array(actor['mesh'], array)

    ctrl.view_update()

# every time we change the main gittree ("ui"), we end up here
# we need to update the ui because it might have changed due to changes
# in other git nodes
#
@state.change("active_ui")
def update_active_ui(active_ui, **kwargs):
    print("update_active_ui:: ",active_ui)

    if not(state.active_id == 0):
      # get boundary name belonging to ID
      _name = pipeline.get_node(state.active_id)['name']
      print("update_active_ui::name=",_name)

      if (_name=="Physics"):
        print("update node physics")
        #pipeline.update_node_value("Physics","subui",active_ui)
      elif (_name=="Initialization"):
        print("update node Initialization")
        # force update of initial_option_idx so we get the submenu
        state.dirty('initial_option_idx')
        #pipeline.update_node_value("Initialization","subui",active_ui)
        # update because it might be changed elsewhere
        #initialization_card()

      ctrl.view_update()

@state.change("active_parent_ui")
def update_active_ui(active_ui, **kwargs):
    print("update_active_ui:: ",active_ui)
    if not(state.active_id == 0):
      # get boundary name belonging to ID
      #_name = pipeline.get_node(state.active_id)['name']
      #print("update_active_ui::name=",_name)

      #if (_name=="Physics"):
      #  print("update node physics")
      #elif (_name=="Initialization"):
      #  print("update node Initialization")
      #  # update because it might be changed elsewhere
      #  initialization_card()

      ctrl.view_update()

@state.change("active_head_ui")
def update_active_ui(active_ui, **kwargs):
    print("update_active_ui:: ",active_ui)
    if not(state.active_id == 0):
      # get boundary name belonging to ID
      _name = pipeline.get_node(state.active_id)['name']
      #print("update_active_ui::name=",_name)

      if (_name=="Physics"):
        print("*********** update ui: physics ************************")
        # call to update physics submenu visibility
        # this is important when setting all options from the config file
        state.dirty('physics_turb_idx')

      #elif (_name=="Initialization"):
      #  print("update node Initialization")
      #  # update because it might be changed elsewhere
      #  initialization_card()

      ctrl.view_update()


#
# every time we change the main gittree ("ui"), we end up here
# we have to set the correct "subui" again from the last visit.
@state.change("active_sub_ui")
def update_active_sub_ui(active_sub_ui, **kwargs):
    print("update_active_sub_ui:: ",active_sub_ui)

    if not(state.active_id == 0):
      _name = pipeline.get_node(state.active_id)['name']
      print("update_active_sub_ui::parent name=",_name)

    print("choice = ",state.initial_option_idx)

    if not(state.active_id == 0):
      # get boundary name belonging to ID
      _name = pipeline.get_node(state.active_id)['name']
      print("update_active_sub_ui::name=",_name)
      if (_name=="Physics"):
        print("update node physics")
        pipeline.update_node_value("Physics","subui",active_sub_ui)

      elif (_name=="Initialization"):
        print("update node Initialization")
        pipeline.update_node_value("Initialization","subui",active_sub_ui)
        # necessary?
        #initialization_subcard()

      ctrl.view_update()


# some default options

state.submodeltext = "none"


# initial value for the materials-fluidmodel list
state.LMaterialsFluid = LMaterialsFluidComp
state.LMaterialsViscosity = LMaterialsViscosityComp
state.LMaterialsConductivity = LMaterialsConductivityComp
state.LMaterialsHeatCapacity = LMaterialsHeatCapacityConst




###############################################################
# FILES
###############################################################

# load cofiguration .cfg file
@state.change("cfg_file_upload")
def load_cfg_file(cfg_file_upload, **kwargs):

    if cfg_file_upload is None:
        return

    # assigning filecontent for args
    filecontent = cfg_file_upload

    # checking if the file is sent by GUI
    if "args" not in kwargs:
        file = ClientFile(cfg_file_upload)
        filecontent = file.content.decode('utf-8')

    # reading each line of configuration file
    f = filecontent.splitlines()
    cfglist = []
    f = [element for element in f if not (element.strip().startswith("%")) and len(element.strip())]
    for item in f:
       item = item.strip()
       if(item[0] == "%" or len(item)<1):
          continue   
       if(len(cfglist) and cfglist[-1][-1]=='\\'):
          cfglist[-1] = cfglist[-1][:-1]
          cfglist[-1] += item
       else:
          cfglist.append(item)
    
    cfg_dict = {}
    for item in cfglist:
        key, value = item.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # Convert value to appropriate type
        if value.startswith('(') and value.endswith(')'):
            # Remove parentheses and split by comma
            value = value[1:-1].split(',')
            # Convert each item to an appropriate type
            value = [v.strip() for v in value]
            value = [int(v) if v.isdigit() else v for v in value]
        elif value.isdigit():
            value = int(value)
        else:
            try:
                value = float(value)
            except ValueError:
                pass # Keep as string if it cannot be converted to int or float
        
        cfg_dict[key] = value


    # checking if the value of state.jsonData['OUTPUT_WRT_FREQ'] is int
    # if yes set it to a list of 2 elements with same value for proper working
    if isinstance(cfg_dict['OUTPUT_WRT_FREQ'], int):
      cfg_dict['OUTPUT_WRT_FREQ']= [cfg_dict['OUTPUT_WRT_FREQ']] * 2
      
    # checking if the value of state.jsonData['OUTPUT_WRT_FREQ'] is str
    # if yes set it to a list of elements with same value for proper working
    if isinstance(cfg_dict['OUTPUT_WRT_FREQ'], str):
      cfg_dict['OUTPUT_WRT_FREQ']= [int(x) for x in cfg_dict['OUTPUT_WRT_FREQ'].split(",")]

    # Write the dictionary to a JSON file
    # with open(BASE / "user" / state.filename_json_export, 'w') as f:
    #     json.dump(cfg_dict, f, indent=4)
    
    # assigning new values to jsonData
    state.jsonData = cfg_dict
    state.dirty('jsonData')
      
    # save the cfg file
    save_json_cfg_file(state.filename_json_export,state.filename_cfg_export)


# load SU2 .su2 mesh file #
# currently loads a 2D or 3D .su2 file
@state.change("su2_file_upload")
def load_file_su2(su2_file_upload, **kwargs):

    global pipeline
    # remove the added boundary conditions in the pipeline
    pipeline.remove_right_subnode("Boundaries")

    del mesh_actor_list[:]

    if su2_file_upload is None:
        return

    # print("name = ",su2_file_upload.get("name"))
    # print("last modified = ",su2_file_upload.get("lastModified"))
    # print("size = ",su2_file_upload.get("size"))
    # print("type = ",su2_file_upload.get("type"))

    # remove all actors
    renderer.RemoveAllViewProps()

    grid.Reset()


    # ### setup of the internal data structure ###
    branch_interior = vtkMultiBlockDataSet()
    branch_boundary = vtkMultiBlockDataSet()

    global root
    root.SetBlock(0, branch_interior)
    root.GetMetaData(0).Set(vtk.vtkCompositeDataSet.NAME(), 'Interior')
    root.SetBlock(1, branch_boundary)
    root.GetMetaData(1).Set(vtk.vtkCompositeDataSet.NAME(), 'Boundary')
    pts = vtk.vtkPoints()
    # ### ### #

    # mesh file format specific

    # assigning filecontent for args
    filecontent = su2_file_upload

    # checking if the file is sent by GUI
    if "args" not in kwargs:
        file = ClientFile(su2_file_upload)
        filecontent = file.content.decode('utf-8')

    f = filecontent.splitlines()

    index = [idx for idx, s in enumerate(f) if 'NDIME' in s][0]
    NDIME = int(f[index].split('=')[1])
    # number of dimensions of the su2 mesh (2D or 3D)
    state.nDim = NDIME
    # for the mesh info display
    #state.meshText += "Mesh Dimensions: " + str(NDIME) + "D \n"

    index = [idx for idx, s in enumerate(f) if 'NPOIN' in s][0]
    numPoints = int(f[index].split('=')[1])
    #state.meshText += "Number of points: " + str(numPoints) + "\n"

    # get all the points
    for point in range(numPoints):
           x = float()
           y = float()
           z = float()
           line = f[index+point+1].split(" ")
           x = float(line[0])
           y = float(line[1])

           if (NDIME==2):
             # 2D is always x-y plane (z=0)
             z = float(0.0)
           else:
             z = float(line[2])
           pts.InsertNextPoint(x,y,z)

    grid.SetPoints(pts)

    # get the number of elements/cells
    index = [idx for idx, s in enumerate(f) if 'NELEM' in s][0]
    numCells = int(f[index].split('=')[1])
    state.mesh= ["Number of cells: " + str(numCells) + "\n"]

    for cell in range(numCells):
            data = f[index+cell+1].split(" ")
            CellType = int(data[0])
            # quadrilaterals
            if(CellType==9):
              quaddata = [int(data[1]),int(data[2]),int(data[3]),int(data[4])]
              grid.InsertNextCell(VTK_QUAD,4,quaddata)
            # triangles
            elif(CellType==5):
              tridata = [int(data[1]),int(data[2]),int(data[3])]
              grid.InsertNextCell(VTK_TRIANGLE,3,tridata)
            # hexahedral
            elif(CellType==12):
              hexdata = [int(data[1]),int(data[2]),int(data[3]),int(data[4]),int(data[5]),int(data[6]),int(data[7]),int(data[8])]
              grid.InsertNextCell(VTK_HEXAHEDRON,8,hexdata)
            # tetrahedral (4 faces)
            elif(CellType==10):
              tetdata = [int(data[1]),int(data[2]),int(data[3]),int(data[4])]
              grid.InsertNextCell(VTK_TETRA,4,tetdata)
            # wedge
            elif(CellType==13):
              wedgedata = [int(data[1]),int(data[2]),int(data[3]),int(data[4]),int(data[5]),int(data[6])]
              grid.InsertNextCell(VTK_WEDGE,6,wedgedata)
            # pyramid
            elif(CellType==14):
              pyramiddata = [int(data[1]),int(data[2]),int(data[3]),int(data[4]),int(data[5])]
              grid.InsertNextCell(VTK_PYRAMID,5,pyramiddata)
            else:
              print("ERROR: cell type not suppported")


    branch_interior.SetBlock(0, grid)
    branch_interior.GetMetaData(0).Set(vtk.vtkCompositeDataSet.NAME(), 'Fluid-Zone-1')
    del branch_interior

    # ### read the markers ### #
    boundaryNames = []

    markerNames=[]
    index = [idx for idx, s in enumerate(f) if 'NMARK' in s][0]
    numMarkers = int(f[index].split('=')[1])

    global markergrid
    markergrid = [vtkUnstructuredGrid() for i in range(numMarkers)]

    # now loop over the markers
    counter=0
    for iMarker in range(numMarkers):
          # grid for the marker
          #markergrid = vtkUnstructuredGrid()
          # copy all the points into the markergrid (inefficient)
          markergrid[iMarker].SetPoints(pts)
          # next line: marker tag, marker_elem
          counter += 1
          # this is the name (string) of the boundary
          markertag = f[index+counter].split("=")[1].strip()

          # add name to the boundaryNames list of dicts
          boundaryNames.append(
            {
                "text": markertag,
                "value": iMarker,
            }
          )
          markerNames.append(markertag)
          # next line: marker tag, marker_elem
          counter+=1
          line = f[index+counter].split("=")
          numCells = int(line[1])
          #print("number of cells = ",numCells)

          # loop over all cells
          for cell in range(numCells):
            counter+=1
            data = f[index+counter].split(" ")
            #print("data = ",data)
            CellType = int(data[0])
            # line
            if(CellType==3):
              linedata = [int(data[1]),int(data[2])]
              markergrid[iMarker].InsertNextCell(VTK_LINE,2,linedata)
            # triangles
            elif(CellType==5):
              tridata = [int(data[1]),int(data[2]),int(data[3])]
              markergrid[iMarker].InsertNextCell(VTK_TRIANGLE,3,tridata)
            # quadrilaterals
            elif(CellType==9):
              quaddata = [int(data[1]),int(data[2]),int(data[3]),int(data[4])]
              markergrid[iMarker].InsertNextCell(VTK_QUAD,4,quaddata)
            else:
              print("ERROR: marker cell type not suppported")
          # put boundary in multiblock structure
          branch_boundary.SetBlock(iMarker, markergrid[iMarker])
          branch_boundary.GetMetaData(iMarker).Set(vtk.vtkCompositeDataSet.NAME(), markertag)


    # end loop over lines

    #del markergrid
    #del pts

    # boundary meshes as unstructured grids
    ds_b = []
    for i in range(branch_boundary.GetNumberOfBlocks()):
        ds_b.append(vtk.vtkUnstructuredGrid.SafeDownCast(branch_boundary.GetBlock(i)))
    del branch_boundary

    # we also clear the arrays, if any
    for array in state.dataset_arrays:
        arrayName = array.get("text")
        print("removing array ",arrayName)
        grid.GetPointData().RemoveArray(arrayName)
        # nijso TODO BUG does not contain data yet
        #for iMarker in range(numMarkers):
        #  markergrid[iMarker].GetPointData().RemoveArray(arrayName)
       
    # and we only use the default array
    state.dataset_arrays = []

    # show the internal mesh in 2D
    if (NDIME==2):
      mesh_actor.VisibilityOn()
      mesh_actor.GetProperty().EdgeVisibilityOn()
    else:
      mesh_actor.VisibilityOff()
    # initial color of the geometry
    mesh_actor.GetProperty().SetColor(colors.GetColor3d('floralwhite'))
    # Mesh - add mesh to the renderer
    mesh_mapper.SetInputData(grid)

    mesh_actor.SetMapper(mesh_mapper)
    mesh_actor.SetObjectName("internal")

    renderer.AddActor(mesh_actor)

    # boundary actors
    boundary_id = 101
    i = 0
    print("length of ds_b=",len(ds_b))
    for bcName in boundaryNames:
        print("bc name=",bcName)
        mesh_mapper_b1 = vtkDataSetMapper()
        mesh_mapper_b1.ScalarVisibilityOff()
        mesh_actor_b1 = vtkActor()
        # in 2D, we show the interior (2D surface) and in 3D, we show all boundaries
        if (NDIME==2):
          mesh_actor_b1.VisibilityOff()
        else:
          mesh_actor_b1.VisibilityOn()
          mesh_actor_b1.GetProperty().EdgeVisibilityOn()


        mesh_actor_b1.GetProperty().SetColor(colors.GetColor3d('Peacock'))

        mesh_mapper_b1.SetInputData(ds_b[i])
        i += 1
        mesh_actor_b1.SetMapper(mesh_mapper_b1)
        mesh_actor_b1.SetObjectName(bcName.get("text"))

        renderer.AddActor(mesh_actor_b1)

        mesh_actor_list.append({"id":boundary_id,"name":bcName.get("text"), "mesh":mesh_actor_b1})
        boundary_id += 1

    # add internal mesh as well.
    mesh_actor_list.append({"id":boundary_id,"name":"internal", "mesh":mesh_actor})
    # internal block is also a 'boundary'
    boundaryNames.append(
                            {
                        "text": "internal",
                        "value": numMarkers,
                    }
    )

    # now construct the actual boundary list for the GUI
    for bcName in boundaryNames:
       print("boundary name=",bcName.get("text"))
       # add the boundaries to the right tree and not the left tree
       id_aa = pipeline.append_node(parent_name="Boundaries", name=bcName.get("text"), left=False, subui="none", visible=1, color="#2962FF")

    state.BCDictList = []
    # fill the boundary conditions with initial boundary condition type
    for bcName in boundaryNames:
      print("*************** BCNAME **********",bcName)
      # do not add internal boundaries to bcdictlist
      if bcName.get("text") != "internal":
        state.BCDictList.append({"bcName":bcName.get("text"),
                                 "bcType":"Wall",
                                 "bc_subtype":"Temperature",
                                 "json":"MARKER_ISOTHERMAL",
                                 "bc_velocity_magnitude":1.0,
                                 "bc_temperature":300.0,
                                 "bc_pressure":0.0,
                                 "bc_density":1.2,
                                 "bc_massflow":0.0,
                                 "bc_velocity_normal":[1.0, 0.0, 0.0],
                                 "bc_heatflux":0.0,
                                 "bc_heattransfer":[0.0, 300.0],
                                 },
                                 )
      else:
        state.BCDictList.append({"bcName":bcName.get("text"),
                                 "bcType":"Internal",
                                 "bc_subtype":"None",
                                 "json":"NONE",
                                 "bc_velocity_magnitude":0.0,
                                 "bc_temperature":0.0,
                                 "bc_pressure":0.0,
                                 "bc_density":0.0,
                                 "bc_massflow":0.0,
                                 "bc_velocity_normal":[0.0, 0.0, 0.0],
                                 "bc_heatflux":0.0,
                                 "bc_heattransfer":[0.0, 0.0],
                                 },
                                 )


    # We have loaded a mesh, so enable the exporting of files
    state.export_disabled = False

    # we have deleted all actors, so add the non-boundary actors again
    #  TODO: only delete the mesh related actors
    global cube_axes
    cube_axes = MakeCubeAxesActor()
    renderer.AddActor(cube_axes)

    global scalar_bar
    global scalar_bar_widget
    scalar_bar = MakeScalarBarActor()
    scalar_bar_widget =MakeScalarBarWidget(scalar_bar)

    #coordinate axes to show orientation
    global coord_axes
    axes1 = MakeAxesActor()
    coord_axes = MakeOrientationMarkerWidget(axes1)

    renderer.ResetCamera()
    ctrl.view_update()

# -----------------------------------------------------------------------------
# GUI elements
# -----------------------------------------------------------------------------

# collapse or expand the gittree
def on_action(event):
    #print("on_action", event)
    _id = event.get("id")
    _action = event.get("action")
    if _action.startswith("collap"):
        print(pipeline.toggle_collapsed(_id))

def on_event(event):
    print(event)



# git tree in the left drawer
def pipeline_widget():
    trame.GitTree(
        sources = ("git_tree", pipeline),
        ### collabsable gittree: ###
        action_map=("icons", local_file_manager.assets),
        # size of the icon
        action_size=25,
        width=350,
        action=(on_action, "[$event]"),
        # default active is first node
        actives = ("selection",state.selection),
        actives_change=(actives_change, "[$event]"),
    )

###############################################################
# checnge edge visibility
###############################################################
@state.change("vtkEdgeVisibility")
def changevtkEdgeVisibility(vtkEdgeVisibility, **kwargs):

    print("edge: ",vtkEdgeVisibility)
    # can only be activated/deactivated for incompressible
    #state.energy = bool(state.physics_energy_idx)
    # get list of all actors, loop and color the selected actor
    actorlist = vtk.vtkActorCollection()
    actorlist = renderer.GetActors()
    actorlist.InitTraversal()
    for a in range(0, actorlist.GetNumberOfItems()):
        actor = actorlist.GetNextActor()
        if vtkEdgeVisibility==True:
          actor.GetProperty().EdgeVisibilityOn()
        else:
          actor.GetProperty().EdgeVisibilityOff()

    ctrl.view_update()

# visibility if the cube axes (bounding box) is on
@state.change("cube_axes_visibility")
def update_cube_axes_visibility(cube_axes_visibility, **kwargs):
    print("change axes visibility")
    cube_axes.SetVisibility(cube_axes_visibility)
    ctrl.view_update()

# visibility if the coordinate axes is on
@state.change("coord_axes_visibility")
def update_coord_axes_visibility(coord_axes_visibility, **kwargs):
    print("change coord axes visibility")
    coord_axes.SetEnabled(coord_axes_visibility)
    ctrl.view_update()

# visibility if the color bar is on
@state.change("color_bar_visibility")
def update_color_bar_visibility(color_bar_visibility, **kwargs):
    print("change color bar visibility")
    scalar_bar_widget.SetEnabled(color_bar_visibility)
    ctrl.view_update()

# buttons in the top header
def standard_buttons():

    # su2path = BASE / "user" / state.filename_json_export
    # Save the .su2 file
    with vuetify.VBtn("Outputs",click=(update_download_dialog_card)):
       vuetify.VIcon("mdi-download-box-outline")

    # # download button such that the .su2 file ends up in "downloads"
    # with vuetify.VBtn(
    #                  ".su2",
    #                  click=f"utils.download('{su2path}', trigger('download_file_su2'))",
    #                  ):
    #    vuetify.VIcon("mdi-download-box-outline")

    # with vuetify.VBtn(".cfg", click=(save_json_cfg_file,"[filename_json_export,filename_cfg_export]"), disabled=("export_disabled",True)):
    #     vuetify.VIcon("mdi-download")

    # # download button such that the .cfg file ends up in "downloads"
    # with vuetify.VBtn(
    #                  ".cfg",
    #                  click="utils.download(filename_cfg_export, trigger('download_file_cfg'), 'text/plain')",
    #                  ):
    #    vuetify.VIcon("mdi-download-box-outline")



# -----------------------------------------------------------------------------
# Web App setup
# -----------------------------------------------------------------------------

state.trame__title = "SU2 GUI"

with SinglePageWithDrawerLayout(server) as layout:

    # text inside the toolbar
    layout.title.set_text(" ")

    # matplotlib monitor: read the initial history file
    [state.x,state.ylist] = readHistory(BASE / "user" / state.history_filename)
    print("x=",state.x)
    print("y=",state.ylist)

    with layout.toolbar:

        #vuetify.VSpacer()
        with vuetify.VBtn():
          vuetify.VImg(
            src=local_file_manager.assets['su2logo'],
            contain=True,
            height=50,
            width=50,
          )

        # vertical spacer inside the toolbar
        vuetify.VSpacer()

        # vertical divider inside the toolbar (solid line)
        vuetify.VDivider(vertical=True, classes="mx-2")
        standard_buttons()
        vuetify.VDivider(vertical=True, classes="mx-2")

        ######################################################
        # scalar selection field inside the top toolbar
        vuetify.VSelect(
            # Color By
            label="Color by",
            v_model=("mesh_color_array_idx", 0),
            #items=("array_list", datasetArrays),
            items=("Object.values(dataset_arrays)",),
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1",
            #v_model=("field", "solid"),
            #items=("Object.values(fields)",),
            #style="max-width: 200px;",
            #classes="mr-4",
        )
        ######################################################

        # file input inside the top toolbar
        # input .su2 file
        vuetify.VFileInput(
            # read more than one file
            multiple=False,
            background_color="white",
            # the icon in front of the file input
            prepend_icon="mdi-file",
            show_size=True,
            small_chips=True,
            truncate_length=25,
            v_model=("su2_file_upload", None),
            label="Load .SU2 Mesh File",
            dense=True,
            hide_details=True,
            style="max-width: 300px;",
            # only accepts paraview .vtm files
            accept=".su2",
            __properties=["accept"],
        )

        # input .cfg file
        vuetify.VFileInput(
            # read more than one file
            multiple=False,
            background_color="white",
            # the icon in front of the file input
            prepend_icon="mdi-file",
            show_size=True,
            small_chips=True,
            truncate_length=25,
            v_model=("cfg_file_upload", None),
            label="Load .CFG File (optional)",
            dense=True,
            hide_details=True,
            style="max-width: 300px;",
            accept=".cfg",
            __properties=["accept"],
        )


        # progress inside the toolbar
        vuetify.VProgressLinear(
            indeterminate=True, absolute=True, bottom=True, active=("trame__busy",)
        )


    # left side menu
    with layout.drawer as drawer:
        # drawer components
        drawer.width = 400
        # git pipeline widget (defined below)
        pipeline_widget()
        # simple divider
        vuetify.VDivider(classes="mb-2")
        #
        print("initialize boundary card")
        # main head/parent node
        boundaries_card_parent()
        # children nodes (the actual boundaries)
        boundaries_card_children()
        #
        print("initialize physics card")
        physics_card()
        physics_subcard()
        #
        print("initialize materials card")
        materials_card()
        #materials_subcard()
        #
        print("initialize numerics card")
        numerics_card()
        #
        print("initialize initialization card")
        initialization_card()
        initialization_patch_subcard()
        initialization_file_subcard()
        initialization_uniform_subcard()
        #
        print("initialize mesh card")
        mesh_card()
        mesh_subcard()
        #
        print("initialize fileio card")
        fileio_card()
        #

        print("initialize solver card")
        solver_card()
        #

        # dialog cards - these are predefined 'popup windows'
        # Output dialog
        download_diagol_card()
        # material dialogs
        materials_dialog_card_fluid()
        materials_dialog_card_viscosity()
        materials_dialog_card_cp()
        materials_dialog_card_conductivity()
        # boundaries dialogs
        boundaries_dialog_card_inlet()
        boundaries_dialog_card_outlet()
        boundaries_dialog_card_wall()
        boundaries_dialog_card_farfield()

        solver_dialog_card_convergence()
        # set all physics states from the json file
        # this is reading the config file (done by read_json_data) and filling it into the GUI menu's
        set_json_physics()
        set_json_materials()
        set_json_initialization()
        set_json_fileio()
        set_json_numerics()
        set_json_solver()
        #this necessary here?
        #state.dirty('jsonData')

    print("setting up layout content")
    with layout.content:

      # create the tabs
      with vuetify.VTabs(v_model=("active_tab", 0), right=True):
        vuetify.VTab("Geometry")
        vuetify.VTab("History")

      with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
            style="position: relative;"
      ):
        # create the tabs
        with vuetify.VTabsItems(
            value=("active_tab",), style="width: 100%; height: 100%;"
        ):
            # first tab
            with vuetify.VTabItem(
                value=(0,), style="width: 100%; height: 100%;"
            ):
              # row containing everything
              with vuetify.VRow(dense=True, style="height: 100%;", classes="pa-0 ma-0"):
                # First column containing renderview buttons
                with vuetify.VCol(cols="1",classes="pa-0 ma-0"):

                  with vuetify.VRow(dense=True,classes="pa-0 ma-0"):
                    # reset the view
                    with vuetify.VBtn(icon=True, click="$refs.view.resetCamera()"):
                      vuetify.VIcon("mdi-crop-free")

                  with vuetify.VRow(dense=True,classes="pa-0 ma-0"):
                    # switch on/off edge visibility in the mesh
                    vuetify.VCheckbox(
                      v_model=("vtkEdgeVisibility", True),
                      on_icon="mdi-grid",
                      off_icon="mdi-grid-off",
                      #true_value="gridOff",
                      #false_value="gridOn",
                      classes="mx-1",
                      hide_details=True,
                      dense=True,
                    )

                  with vuetify.VRow(dense=True,classes="pa-0 ma-0"):
                    # switch on/off the bounding box visualisation
                    vuetify.VCheckbox(
                      v_model=("cube_axes_visibility", False),
                      on_icon="mdi-cube-outline",
                      off_icon="mdi-cube-off-outline",
                      classes="mx-1",
                      hide_details=True,
                      dense=True,
                  )
                  with vuetify.VRow(dense=True,classes="pa-0 ma-0"):
                    # switch on/off the coordinate axes visualisation
                    vuetify.VCheckbox(
                      v_model=("coord_axes_visibility", True),
                      on_icon="mdi-axis-arrow",
                      off_icon="mdi-square-outline",
                      classes="mx-1",
                      hide_details=True,
                      dense=True,
                  )
                  with vuetify.VRow(dense=True,classes="pa-0 ma-0"):
                    # switch on/off the coordinate axes visualisation
                    vuetify.VCheckbox(
                      v_model=("color_bar_visibility", True),
                      on_icon="mdi-water",
                      off_icon="mdi-water-off",
                      classes="mx-1",
                      hide_details=True,
                      dense=True,
                  )
                # second column containing the renderview (move window left by 12)
                with vuetify.VCol(cols="11", classes="pa-0 ml-n12 mr-0 my-0"):
                  view = vtk_widgets.VtkRemoteView(renderWindow)
                  ctrl.view_update = view.update
                  ctrl.view_reset_camera = view.reset_camera
                  ctrl.on_server_ready.add(view.update)

            # second tab
            with vuetify.VTabItem(
               value=(1,), style="width: 100%; height: 100%;"
            ):
             with vuetify.VRow(dense=True, style="height: 100%;", classes="pa-0 ma-0"):
                with vuetify.VBtn(classes="ml-2 mr-0 mt-16 mb-0 pa-0", elevation=1,variant="text",color="white",click=update_dialog, icon="mdi-dots-vertical"):
                  vuetify.VIcon("mdi-dots-vertical",density="compact",color="red")
                with vuetify.VCol(
                    classes="pa-0 ma-0",
                    #style="border-right: 1px solid #ccc; position: relative;",
                ):
                  with trame.SizeObserver("figure_size"):
                    html_figure = tramematplotlib.Figure(style="position: absolute")
                    ctrl.update_figure = html_figure.update

    print("finalizing drawer layout")

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main():
    
    # Defining arguments while calling su2gui
    # for starting it with different files 
    parser = argparse.ArgumentParser(description='Start the SU2 GUI application.')
    parser.add_argument('--mesh', type=str, help='Path to the SU2 mesh file in .su2 format.')
    parser.add_argument('--config', type=str, help='Path to the configuration file.')
    parser.add_argument('--restart', type=str, help='Path to the restart file in .csv format.')
    
    args = parser.parse_args()
    
    mesh_path = args.mesh
    config_path = args.config
    restart_path = args.restart

    if mesh_path and not os.path.exists(mesh_path):
        print(f"Error: The SU2 mesh file {mesh_path} does not exist.")
        exit(1)

    if mesh_path:
        print(f"Using SU2 mesh file {mesh_path}")
        with open(mesh_path, 'r') as f:
           content = f.read()
           load_file_su2(su2_file_upload=  content, args= True)
           

    if config_path and not os.path.exists(config_path):
        print(f"Error: The configuration file {config_path} does not exist.")
        exit(1)

    if config_path:
        print(f"Using configuration file {config_path}")
        with open(config_path, 'r') as f:
           content = f.read()
           load_cfg_file(cfg_file_upload=  content, args= True)

    if restart_path and not os.path.exists(restart_path):
        print(f"Error: The restart file {restart_path} does not exist.")
        exit(1)

    if restart_path:
        if not mesh_path:
           print("Error: Can not load restart file without SU2 mesh file ")
           exit(1)
        print(f"Using restart file {restart_path}")
        with open(restart_path, 'r') as f:
           content = f.read()
           uploadRestart(restartFile=  content, args= True)


    server.start()
    print("su2gui server ended...")


if __name__=="__main__":
    main()