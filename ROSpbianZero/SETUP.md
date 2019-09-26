ROSpbianZero
============

This is a distribution is a modified RaspbianLite iso with ROS kinetic installed. This iso can also be configured to use the raspberry pi zero as a wifi hotspot.

The setup is split as follow:

1. raspbian stretch install
2. increase swap
3. ros compilation and install
4. wifi setup
5. setup to run nodes at boot
6. iso packing for further use

1: raspbian stretch install:
----------------------------

Go the [Raspbian website](https://www.raspberrypi.org/downloads/raspbian/) and download the the *Raspbian Lite* iso. Choose *raspbian jessie*.

Once done install it on a 16Go micro sd  ([tutorial](https://tutorials.ubuntu.com/tutorial/tutorial-create-a-usb-stick-on-ubuntu#0))

Log into the raspberry pi:
  login:pi
  pass:raspberry

change password and launch:
```
# sudo raspi-config
```
choose *expand filesystem*. You can also choose to enable ssh service (recommended). Enable camera and reboot.

Now install pigpio (usefull if you need the gpio! ):
```
# sudo apt-get update
# sudo apt-get install pigpio python-pigpio python3-pigpio
```

2: increase swap:
-----------------

Follow the [tutorial](https://wpitchoune.net/tricks/raspberry_pi3_increase_swap_size.html) and increase swap to 1024mb.

3: ROS install:
---------------

Add the repositories [step 1.2 - 1.3 of this tutorial](http://wiki.ros.org/kinetic/Installation/Ubuntu#Installation.2BAC8-Ubuntu.2BAC8-Sources.Setup_your_sources.list)

Now follow the [tutorial](http://wiki.ros.org/kinetic/Installation/Source) to install ros kinetic from sources. **ATTENTION!!** read the entire paragraph before doing the tutorial, as some changes apply:

**edit 1**
in step 2.1.1 don't choose *desktop install* as we don't have any GUI. Choose *perception* instead. See also the [list of available variants](http://www.ros.org/reps/rep-0131.html#variants)
```
$ rosinstall\_generator robot perception --rosdistro kinetic --deps --wet-only --tar > kinetic-robot-perception-wet.rosinstall
$ wstool init -j8 src kinetic-robot-perception -wet.rosinstall
```


**edit 2**
Some package won't compile as is, you must apply the following patch:

```
-find_package(Eigen3 REQUIRED)
+find_package(PkgConfig)
+pkg_search_module(Eigen3 REQUIRED eigen3)
```  

Take a nap, the compile time is veeeeeerry long. You may also want to use *screen* or *byobu* to disconnet you ssh connection without stopping the compilation.

**Note:** Once the install is done and working you can delete the compilation folder. This will allow you to free up to 2Gb. (Usefull especially when packing the final iso).

4: wifi setup:
--------------

Follow [this tutorial](https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md). The part *Using the Raspberry Pi as an access point to share an internet connection (bridge)* is optionnal.

5: setup ROS node at boot:
--------------------------

Create the file `/etc/systemd/system/bringup.service`:
```
[Unit]
Restart=on-abort
Description=ros\_bringup
After=network.target
  
[Service]
ExecStart=/bin/bash /usr/local/bin/bringup.sh

[Install]
WantedBy=default.target
```
This file will allow run `/usr/local/bin/bringup.sh` at boot.

Create now `/usr/local/bin/bringup.sh`:
```
#!/usr/bin/env bash
bash -c "source /opt/ros/kinetic/setup.bash && source /home/pi/catkin\_ws/devel/setup.bash && export ROS\_HOSTNAME=192.168.4.1 && export ROS\_MASTER\_URI=http://192.168.4.1:11311 && roslaunch bringup\_package bringup.launch > /tmp/bringup.log"
```

This command line allow to:
 - source ros executable
 - source your workspace executables
 - export variables to allow remote  ROS hosts
 - launch a launchfile

You may want to change this in order to launch an other launchfile. Without modifications this file run `bringup.launch` in the `bringup_package`.

Now adjust the acces:
```
# chmod 744 /usr/local/bin/bringup.sh
```

Then enable the service:
```
# chmod 664 /etc/systemd/system/bringup.service
# systemctl daemon-reload
# systemctl enable bringup.service
Created symlink from /etc/systemd/system/default.target.wants/bringup.service to /etc/systemd/system/bringup.service.
```

And start the service:
```
systemctl start bringup.service
```

**Note 1:** you can check the service status using `systemctl status bringup.service`

**Note 2:** The console output will be redirected in `/tmp/bringup.log`, this file is deleted at each restart.

6: pack the iso file:
---------------------

 1. poweroff the raspberry pi
 2. connect the sd card to a linux computer (ubuntu used to make this tutorial)
 3. run the `Disks` app
 4. select your sd card
 5. go into the options (top right button) and choose *create disk image*. Choose an iso name.

The obtained file is the size of the card (16Go), you can shrink it to it's minimal size (4.5Go) using [this tutorial](https://softwarebakery.com/shrinking-images-on-linux).

7: you're done!
---------------

This tutorial is intended for the raspberry pi zero, but also works on other models.
