#!/usr/bin/env python

import sys
import rospy
from std_msgs.msg import String, Float32, Bool
from geometry_msgs.msg import Twist


class LineFollower():
    
    def __init__(self):
        self.delta = 0.
        self.theta = 0.
        self.speed = 2.5
        self.smoothing_coef = 0.75  # good at v=1.5
        self.delta_sub = rospy.Subscriber("/plannar_cam/delta", Float32, self.delta_callback)
        self.theta_sub = rospy.Subscriber("/plannar_cam/theta", Float32, self.theta_callback)
        # self.start_sub = rospy.Subscriber("/pause", Bool, self.start_callback)
        self.delta_coef = -0.03
        self.theta_coef = 0.15

    def theta_callback(self, msg):
        self.theta = (1-self.smoothing_coef) * self.theta + self.smoothing_coef * msg.data

    def delta_callback(self, msg):
        self.delta = (1- self.smoothing_coef) * self.delta + self.smoothing_coef * msg.data

    # def start_callback(self, msg):
    #     self.speed = 1. if msg.data else 0.


def main(args):
    rospy.init_node('line_follower', anonymous=False)
    vel_pub = rospy.Publisher("/nav_vel", Twist, queue_size=1)
    controller = LineFollower()
    # vel_pub.publish(Twist())
    rate = rospy.Rate(3)
    # rospy.sleep(5)
    while not rospy.is_shutdown():
        try:
            msg = Twist()
            msg.linear.x = controller.speed
            desired = controller.delta_coef * controller.delta +\
                      controller.theta_coef * controller.theta
            msg.angular.z = min(1., max(-1., desired))
            print("delta: %f" % controller.delta)
            print(msg)
            vel_pub.publish(msg)
            rate.sleep()
            # vel_pub.publish(Twist())
            # rate.sleep()
        except KeyboardInterrupt:
            vel_pub.publish(Twist())


if __name__ == '__main__':
    main(sys.argv)
