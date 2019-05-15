# Q-Checker

Q-Checker can be run independantly or as a geoprocessing tool within ArcPro.  In both cases, Q-checker relies on two separate Python envionrments:

- Q-Checker environment (modified version of the arcgispro-py3 Python enviornment that comes installed with ArcPro)
- PDAL environment

Relying on two separate Python environments is perhaps unconventional, but doing so is a work-around for conflicts between PDAL and other packages in the modified arcgispro-p3y environment.

**RECOMMENDED PYTHON & ARCPRO SETUP**

**1. Create Q-Checker and PDAL Python environments**

The recommended way to create the necessary Python environments relies on the two environment files (.yml) that are included in this repository. To create each environment, run the following commands at the base Anaconda prompt, where <env_*.yml> are the full paths to the Q-Checker and PDAL environment.yml files:

*Modified arcgispro-py 3 environment*
```
(base) C:\>conda env create --prefix <env_qchecker.yml>
```

*PDAL environment*
```
(base) C:\>conda env create --prefix <env_qchecker.yml>
```

**2. Point ArcPro to Q-Checker Python environment**

In ArcPro's Python Package Manager, click the "Manage Environments" button and specify the qchecker that was generated using the conda environment.yml file.

![ArcPro Python Setup](https://github.com/forkozi/QChecker/assets/images/ArcPro_PyEnvManager.PNG?raw=true)
