# PyUncertShell

PyUncertShell is a Python-based uncertainty shell that will perform uncertainty analysis with Latin Hypercube sampling for any software with text inputs and outputs. This project was originally translated from Delphi (Object Pascal) and was tested and developed in Python 3.9.  This software is provided as-is with no warranties of fitness for any purpose.

## Getting Started

With 64-bit Windows, to run a test of the software, which varies Sea Level Rise (SLR) by 2100 in SLAMM 6.7 (5 iterations only), follow these steps:

1. Navigate to the "Model" directory as provided in this repository.
2. Open a Windows command prompt (SLAMM 6.7 is Windows software)
3. Execute the following command: "python ../PyUncertShell.py SY_Delim_Unc.txt"


## Files and Their Purposes

- `PyUncertShell.py`: The main Python script that serves as the PyUncertShell program. It reads the input specification, performs Latin Hypercube Sampling, and runs the target software with varied inputs.  Outputs are written to three files in the working directory: 

    1. *alldata.txt: All tracked model outputs for each uncertainty iteration
    2. *summary.txt: Data about each tracked model output Min, Mean, Max, and Std. Dev.
    3. *uncertlog.txt:  A log showing the progress of the software and uncertainty draws for each iteration

- `CalcDist.py`: various functions for generating random numbers and computing cumulative distribution functions for different probability distributions.  The following distributions types are included and can be used to represent model inputs 

    1. "Normal": Normal distribution with the following parameters-- Parm1: mean; Parm2: standard devation;  
    2. "LogNormal": LogNormal distribution with the following parameters-- Parm1: geometric mean; Parm2: geometric standard deviation; 
    3. "Triangular": Triangualr distribution with the following parameters -- Parm1: minimum; Parm2: maximum; Parm3: most likely;
    4. "Uniform": Uniform distribution with the following parameters-- Parm1: minimum, Parm2: maximum;

- `UncertDefn.py`: defines classes and functions for handling uncertainty distributions and reading input files.

- `Sample_Input.txt`: A sample input file that serves as a specification for text-based input to PyUncertShell. You can create your own input files based on this sample to customize your uncertainty analysis.

## Disclaimer

This software is provided as-is and without any warranties of fitness for any specific purpose. Use it at your own discretion and risk.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.




