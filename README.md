# SU2_GUI

**SU2_GUI** is a Graphical User Interface (GUI) for the SU2 open-source CFD software. It facilitates easier execution of SU2 tasks and provides visualization capabilities for the results.
Please note that SU2_GUI is currently under development. We welcome any feedback and contributions to improve the tool.



## Overview
Here is an overview of how SU2GUI works:
![overview_su2gui](./img/overview_su2gui.png)

### Getting Started
#### Prerequisites
- Python 3.10 or higher
- SU2 installed on your system. Follow the installation instructions [here](https://su2code.github.io/download.html).
#### Recommended
We recommend to install SU2_GUI in a conda virtual environment
```sh
conda create --name su2gui_env --channel conda-forge python
```
You can start the virtual environment using:
```sh
conda activate su2gui_env
```

#### Quick Start

1. Install SU2_GUI: Follow the installation instructions above.
2. Launch SU2_GUI: Use the command S2_GUI to open the application.
3. Load Your Case: Use the interface to load your SU2 mesh files.
4. Run Simulation: Set up and run your simulation through the GUI.
5. Visualize Results: View and analyze the simulation results using the integrated visualization tools.



## Installation

You can install SU2_GUI via pip. We recommend to install it in a virtual environment as instructed above. Then simply install using:

```sh
pip install su2gui
```
### Usage
To launch the GUI, run the following command in your terminal:
```sh
SU2_GUI
```

#### More Information
For more details about SU2, please visit the official SU2 documentation [here](https://su2code.github.io/docs_v7/home/).
