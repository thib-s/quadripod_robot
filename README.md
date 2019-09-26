
![alt text](https://github.com/thib-s/quadripod_robot/raw/master/visuals/logo/tbot-logo.svg)

Quadripod robot
===================

all the files to build a quadripod, including 3d model, eagle files and arduino code.

![alt text](https://github.com/thib-s/quadripod_robot/raw/master/visuals/jacob.jpg)

Disclaimer
==========

This is a personal project, this means that this quadripod was build in a single exemplary. It worked fine for me, but i cannot be held responsible if you fry somehing using my plans.

Repository organization
=======================

3D
--

Contains stl for 3d print the robot, there are the original files from hackaday: [https://hackaday.io/project/9334-kame-esp8266-based-quadruped]. It contains also the modified STL to build the same base with mg996 servos.

Quadripod\_board
-------------

Contains the eagle files for the pcb manufacturing.

code
----

Contains the code to set up and run the robot. It is splitten in two parts: the ros nodes in the ros\_node folder, the 	test\_quadri (to be renamed ) contains the code that configure and perform the gait. Test\_servo folder contain code to check if the servos are well wired and the joint correctly set.
