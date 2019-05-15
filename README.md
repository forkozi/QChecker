# Q-Checker

Q-Checker can be run independantly or as a geoprocessing tool within ArcPro.  In both cases, Q-checker relies on two separte Python envionrments:

- a modified version of the arcgispro-py3 Python enviornment that comes installed with ArcPro
- a PDAL environment

Relying on two separate Python environments is perhaps unconventional, but doing so is a work-around for conflicts between PDAL and other packages in the modified arcgispro-p4y environment.

The recommended way to create the necessary Python environments relies on the two environment files (.yml) that are included in this repository. To create each environment, run the following commands at an Anaconda prompt:

*Modified arcgispro-py 3 environment*
```
conda 
```

*PDAL environment*
```
conda 
```
