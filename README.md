# EXAFSfit_with_silx
GUI for EXAFS fit using Larch* and silx**

*Larch: https://xraypy.github.io/xraylarch/
*silx: http://www.silx.org/doc/silx/latest/index.html

This is a python script to enable EXAFS fittings with Larch package graphically.
You can scattering paths one by one.

#######Get started#######
(1) install Anaconda3 (recommend the latest version)
(2) install Larch with the command below
    conda install -yc GSECARS
(3) install natsort
    conda install natsort
(4) install silx
    pip install silx

######Current Problems######
* Using constraints: there will be some problems when you use constrains.
* The main graph from silx could crash if you use "option" after fittings.

#####Unknown things######
* Up to how many data can be imported.

#####Things to do######
* To make warnings
* Make manuals
