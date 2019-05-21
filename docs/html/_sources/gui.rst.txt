Q-Checker User Interface
************************

The Q-Checker graphical user interface (GUI) has three main parts:

- Settings
- Checks
- Surfaces

.. image:: ../../assets/images/gui.PNG

Settings
--------


Checks
------

The user can run a series of checks to verify that certain expected information is contained in the submitted LAS files.

.. image:: ../../assets/images/checks.PNG

.. csv-table:: Available Checks
    :header: Check, Description
    :widths: 10, 30
    
    Naming Convention, checks that las files are named according to the *yyyy_[easting]e_[northing]n_las* naming convention
    Version, checks that the las files are the version specified in the corresponding dropdown menu
    Point Data Record Format, checks the Las files contain the propoer PDRF corresponding to the specified version
    GPS Time Type, checks that 'GPS Time Type' in the Las header is 'Satellite Adjusted Time' (not GPS week seconds)
    Horizontal Datum, checks that Las header contains the specified horizontal spatial reference
    Vertical Datum, checks that Las header contains the specified vertical spatial reference
    Point Source IDs, checks that Las file contains > 1 unique point source id (flight line number)
    Expected Classes, checks that Las file contains classes other than the specified expected classes

Surfaces
--------

The user has the option to generate the following surfaces:

.. image:: ../../assets/images/surfaces.PNG

.. csv-table:: Available Checks
    :header: Surface, Description
    :widths: 10, 30
    
    Dz, shows the maximum difference in the z values (i.e. dz values) of points from overlapping las files
    Hillshade, an 8-bit gridded representation of the lidar point cloud based on an illumination azimuth/altitude of 315°/45°
    Dz Mosaic, all of the individual tile Dz surfaces combined into a single surface
    Hillshade Mosaic, all of the individual tile hillshade surfaces combined into a single surface
