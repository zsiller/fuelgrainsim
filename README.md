# fuel-grain-simulator

[![License BSD-3](https://img.shields.io/github/license/zsiller/fuelgrainsim?label=license&style=flat)](https://github.com/zsiller/fuelgrainsim/blob/main/LICENSE)

## Installation 

To install latest development version :

    pip install git+https://github.com/zsiller/fuelgrainsim.git

## About
fuelgrainsim is a tool for analyzing and creating regression rate and thrust curve predictions for hybrid rockets. The program accepts a DXF file depicting the cross section of the grain and the marxman regression calculation is used to calculate regression rates and thrust over time.

## Running fuelgrainsim
Before application is run be sure to download Inkscape for conversion between DXF and SVG file.

[Latest version](https://inkscape.org/release/inkscape-1.4/)

To aid in understanding how the program works and expected results a test DXF file and expected results has been provided.
```
fuelgrainsim --input DXF_path --output your_path --isp 237.4 --a .0004 --nn .37 --density 975 --flow 1.279 --length .3302 --iterations 10 --time 5.619
```

**Command line arguements:**

```
 -h, --help            show this help message and exit
  -i, --input INPUT     Provide a folder containing DXF files
  -o, --output OUTPUT   Provide a folder for simulation results
  -l, --log_level LOG_LEVEL
                        Enter logging level to be displayed
  --isp ISP             Initial specific impulse
  --a A                 Enter regression coefficient a
  --nn NN               Enter regression coefficient nn
  --density DENSITY     Enter material density
  --flow FLOW           Oxidiser flow rate
  --length LENGTH       Fuel grain length
  --iterations ITERATIONS
                        Number of iteration
  --time TIME           Fire time
```

## Tips
- Iterations is iterations per second not total iterations (try to keep total iterations under 100)
- Make sure your DXF file has a 10 mm scale bar to scale the DXF file to scale created SVG to proper size
- The last subdirectory on the output path is the folder output files will be put in (it does not need to exist yet, it will be created if it doesn't)

## License

Distributed under the terms of the [BSD-3] license, "fuelgrainsim" is free and open source software

