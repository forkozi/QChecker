Installation
============

Installing Q-Checker consists of three steps:

- Download Q-Checker GitHub repository 
- Create Python environment
- Configure .bat file
   
1.  Download Q-Checker GitHub repository
----------------------------------------

Download the code repository from https://github.com/noaa-rsd/Q-Checker.github.io to the desired location on your local machine.  


2.  Create Python environment
---------------------------------------

The recommended way to create the necessary Python environment is to create a conda environment by running the following command at an :ref:`conda-label`:

::

    conda env create --prefix <env_qchecker.yml>

where <env_qchecker.yml> is the full path to the Q-Checker environment file, located in the root level of the repository.

3.  Configure .bat file
-----------------------    

Modify the .bat file in the root level of the repository to reflect the location of the Python environment and *qchecker_gui.py* file.

::

    call %UserProfile%\AppData\Local\Continuum\anaconda3\condabin\conda.bat activate qchecker
    %UserProfile%\AppData\Local\Continuum\anaconda3\envs\qchecker\python.exe 
    <path to qchecker_gui.py>
    pause
