vcs2svg
=======

A crude vcd-file renderer.
Depends on:

 * docopt
 * Verilog_VCD
 * svgwrite

 ```  
Usage: ./vcd2svg.py VCDFILE OUTPUT [--sigwidth=<px>] [--sigheight=<px>] SIGNAL [SIGNALS ...]

Options:
--sigwidth	width of signal traces [default: 1000]
--sigheight	height of signal traces	[default: 40]

SIGNAL can be "all", "top" or one or more names of signals.
```
