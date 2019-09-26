#!/usr/bin/env python
import roslib#; roslib.load_manifest('vrep_ros_teleop')
import rospy
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

last_joy = -1e10
joy_value = None

def joy_cb(value):
    global joy_value
    joy_value = value

def talker():
    global joy_value
    rospy.init_node('tbot_teleop')
    sub = rospy.Subscriber('/joy', Joy, joy_cb)
    pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
    pub_pose = rospy.Publisher("/body_pose", Twist, queue_size=1)
    while not rospy.is_shutdown():
        if joy_value is not None:
            twist_mv = Twist()
            twist_mv.linear.x = joy_value.axes[2]
            twist_mv.angular.z = joy_value.axes[3]
            #if twist.linear.x < 0:
            #    twist.angular.z = - twist.angular.z
            pub.publish(twist_mv)
            twist_pose = Twist()
            twist_pose.angular.x = joy_value.axes[6] * 2
            twist_pose.angular.y = joy_value.axes[5] * 2
            twist_pose.angular.z = (joy_value.buttons[4] - joy_value.buttons[5]) * 2
            
            twist_pose.linear.x = joy_value.axes[1] * 2
            twist_pose.linear.y = joy_value.axes[0] * 2
            twist_pose.linear.z = (joy_value.buttons[6] - joy_value.buttons[7]) * 2
            pub_pose.publish(twist_pose)
        rospy.sleep(0.25)


if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException:
        pass
