# Trace Tools

A python library for parsing and working with trace files from Siemens Sinumerik CNC system.

You can parse:
* Trace files - That you configure under the "Diagnostic" meny
* Frequency measurements - From the "Setup/Optimize" meny
* Autotuning results - After finishing an autotuning, you can save the "auto-tuning result", this file contains the sugested control parameters and the frequency responses.

## Files in repo

* `TraceTools.py` Main file, import this and use the functions to parse different type of files.
* `tracetypes.py` class definitions of what the measurment files are parsed to.
* `b85.py` used for decoding their non standard implementation of ASCII 85.


