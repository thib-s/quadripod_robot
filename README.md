
![alt text](https://github.com/thib-s/quadripod_robot/raw/master/visuals/logo/tbot-logo.png)

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

Contains the code that runs on the raspberry pi zero. The folder catkin\_ws contains the node to run locally on the robot. The folder camera\_calibration contains the files to calibrate the camera. The folder teleop\_ws contains the nodes to control the robot remotely using a joystick.
