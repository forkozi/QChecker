Output
******

Q-Checker has 4 main outputs:

- QA/QC results shapefile
- QA/QC results dashboard
- DEM
- DZ surface

QA/QC results shapefile
-----------------------

The QA/QC results shapefile contains a polygon for each input LAS tile, along with the associated check results in the shapefile attribute table.  In the image below, the tiles are colored according to whether or not they passed the version test.

QAQC Las Tile Polygons

.. image:: ../../assets/images/RESULTS_shapefile.PNG

Attribute Table

.. image:: ../../assets/images/RESULTS_shapefile_attribute_table.PNG

QA/QC results dashboard
-----------------------

The QA/QC results dashboard is an HTML page that contains project-wide summary visualizations of the QA/QC results (see image below).

Check Results

.. image:: ../../assets/images/RESULTS_dashboard_checks.PNG

Class-Count Results

.. image:: ../../assets/images/RESULTS_dashboard_class_counts.PNG

DEM
---

Q-Checker creates a true DEM (with elevation values) which can be displayed with any number of colormaps.  A hillshaded surface can then be created using, for example, the ArcPro shaded relief raster function.

Original DEM   
 
.. image:: ../../assets/images/RESULTS_DEM_hillshade1.PNG

Hillshaded Surface

.. image:: ../../assets/images/RESULTS_DEM_hillshade2.PNG

DZ Surface
----------

Q-Checker creates a DZ surface, which shows the maximum difference in per-flight-line mean elevation.  The DZ surface can be visualized using conventional discrete colormaps or continuous colormaps.

.. note::

    The DZ surfaces for each tile are created in 2 steps:
    
    - create a mean-Z surface for each individual flight line (using PDAL's writers.gdal GTiff driver)
    - calculate, per cell, the difference between the max and min mean-z values
    
    Once all individual DZ surfaces are created, they are all merged into a single file
    
.. image:: ../../assets/images/RESULTS_DZ_surface.PNG
