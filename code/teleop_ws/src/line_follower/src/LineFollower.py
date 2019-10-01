#!/usr/bin/env python

import sys
import rospy
from std_msgs.msg import String, Float32
from geometry_msgs.msg import Twist


class LineFollower():
    
    def __init__(self):
        self.delta = 0.
        self.theta = 0.
        self.smoothing_coef = 0.25
        self.delta_sub = rospy.Subscriber("/plannar_cam/delta", Float32, self.delta_callback)
        self.theta_sub = rospy.Subscriber("/plannar_cam/theta", Float32, self.theta_callback)
        self.delta_coef = -0.05
        self.theta_coef = .25

    def theta_callback(self, msg):
        self.theta = (1-self.smoothing_coef) * self.theta + self.smoothing_coef * msg.data

    def delta_callback(self, msg):
        self.delta = (1- self.smoothing_coef) * self.delta + self.smoothing_coef * msg.data


def main(args):
    rospy.init_node('line_follower', anonymous=False)
    vel_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
    controller = LineFollower()
    vel_pub.publish(Twist())
    rate = rospy.Rate(2)
    rospy.sleep(5)
    while not rospy.is_shutdown():
        try:
            msg = Twist()
            msg.linear.x = 1.
            desired = controller.delta_coef * controller.delta +\
                      controller.theta_coef * controller.theta
            msg.angular.z = min(1., max(-1., desired))
            print("delta: %f" % controller.delta)
            print(msg)
            vel_pub.publish(msg)
            rate.sleep()
        except KeyboardInterrupt:
            vel_pub.publish(Twist())


if __name__ == '__main__':
    main(sys.argv)
