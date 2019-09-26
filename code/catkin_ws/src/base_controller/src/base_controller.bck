#!/usr/bin/env python
import rospy
import serial
import time
from geometry_msgs.msg import Twist


def callback(data):
    global ser
    linear = (data.linear.x * 0.5) + 0.5
    angular = (data.angular.z * 0.5) + 0.5
    if (linear != 0.5) or (angular != 0.5):
        print("sending:"+"move("+str(linear)+","+str(angular)+")\n")
        ser.write("move("+str(linear)+","+str(angular )+")\n")
        time.sleep(0.5)

def listener():
    global ser
    rospy.init_node('base_controller', anonymous=True)
    port = rospy.get_param('port', "/dev/ttyS0")
    baudrate = rospy.get_param('baudrate', 1200)
    ser = serial.Serial(port, baudrate)
    rospy.Subscriber("/cmd_vel", Twist, callback, queue_size=1)
    rospy.spin()

if __name__ == '__main__':
    listener()
