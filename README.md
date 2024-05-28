Version: Python 3.11.3
# Overview:
  * Program to generate accurate-ish ground stop times for the vATCSCC on the VATSIM network.
  * Code Author: [Zack B)](https://github.com/zbfromztl)
    * with support from: Simon Heck [(Simon-Heck)](https://github.com/Simon-Heck)

# In Progress:
 - [ ] Determine what aircraft are subject to the stop
 - [ ] Determine length of each aircraft's delay (fix this math lol)
 - [ ] Add more comments and documentation

# To do:
 - [ ] Publish ground stop advisories (with advisory number, automatically)

# Features:
  * Yo mama

# How to Run:
  * Aquire the following modules:
```
pip install zpl
pip install zebra
pip install requests
```
Run python on [main.py](src/main.py). For example:
```
python main.py
```
<sub>Note that the program may overwrite settings that are already on your printer... 
so you may want to save those before running it. Additionally, you need to define
the font of the flight strips to be used in main.py. You can send open communication
with the printer and send ```^XA^WDE:*.TTF^XZ``` to show the name of all available fonts. </sub>

# Commands:
 * Memoryaids - Prints several memory aids, including STOP and NO LUAW.
 * Times - Prints the current taxi times & associated callsigns.
 * Purge - Clears queue count for delay reporting
 * DROP (Callsign) - Removes cid from queue counter.
 * Align - Prints blank strip with singular line. Align line with mouth of printer to achieve serenity.
 * FRC (ACID) or SR (ACID) - Prints strip with all flight plan info.
 * GI (message) - Prints a strip of inputted text.

# ARMT commands (ATL only)
 * countproposals - Counts all the aircraft on the ground and organizes it based on filed departure gate.
 * ALL north/center/south - Amends the departure split.
 * {departure} OR {gate} north/center/south - Amends the departure split (to determine queue count).
 * worst queue or queue count - Generates length of line for departure if all aircraft on the ground were holding short of their runway, according to the departure split.
 * FTD - enables/disables runway 10/28
 * display or current - shows the current split