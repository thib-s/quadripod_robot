#!/usr/bin/env python

# pulse.py

import rospy
from geometry_msgs.msg import Twist
from base_controller.msg import MotionSequence
import numpy as np


class QuadripodModel():

    def __init__(self,):

        ################################################
        # static params of the gait
        ################################################

        # how much to raise the legs when walking
        self.delta = 15
        self.bound = 2.0

        self.init_angles = np.array(
            [[90, 90 + self.delta, 90, 90 - self.delta, 90, 90 - self.delta, 90, 90 + self.delta]])
        # values to correct mechanical alignment of servos
        self.corrections = np.array([-20, 40, 20, -30, 15, -20, -20, 40])

        # how to affect the values when moving the body without walking
        # body_p* refers to position
        # body_o* refers to orientation
        self.body_pz = np.array([0, 1, 0, -1, 0, -1, 0, 1])  # ok
        self.body_px = np.array([1, 0, -1, 0, 1, 0, -1, 0])  # ok
        self.body_py = np.array([-1, 0, 1, 0, 1, 0, -1, 0])  # not py but spacing
        self.body_ox = np.array([0, -1, 0, -1, 0, 1, 0, 1])  # ok
        self.body_oy = np.array([0, 1, 0, -1, 0, 1, 0, -1])  # ok
        self.body_oz = np.array([1, 0, 1, 0, 1, 0, 1, 0])  # ok
        self.gain = 10  # coefficient applied on body pose corrections

        self.body_twist = Twist()
        self.body_twist.linear.x = 0.
        self.body_twist.linear.y = 0.
        self.body_twist.linear.z = 0.
        self.body_twist.angular.x = 0.
        self.body_twist.angular.y = 0.
        self.body_twist.angular.z = 0.

    ################################################
    # functions that compute movement of the robot
    ################################################

    def walk(self, twist):
        """
        compute the legs position sequence in order to perform the walk
        :param twist: the twist msg with the movement infos: twist.linear.y for translation, and twist.angular.z for
        rotation
        :return: the sequence of the servos position as np array
        """
        linear = 0.5 * max(min(twist.linear.x, self.bound), -self.bound) + 0.5
        angular = 0.5 * max(min(twist.angular.z, self.bound), -self.bound) + 0.5
        linear_sequence = np.array([
            [70 , 90 - self.delta, 70,  90 - self.delta, 110, 90 - self.delta, 110, 90 - self.delta],
            [70,  90 + self.delta, 70,  90 + self.delta, 110, 90 + self.delta, 110, 90 + self.delta],
            [110, 90 + self.delta, 110, 90 + self.delta, 70,  90 + self.delta, 70 , 90 + self.delta],
            [110, 90 - self.delta, 110, 90 - self.delta, 70,  90 - self.delta, 70 , 90 - self.delta]
        ])
        angular_sequence = np.array([
            [110, 90 - self.delta, 70,  90 - self.delta, 70 , 90 - self.delta, 110, 90 - self.delta],
            [110, 90 + self.delta, 70,  90 + self.delta, 70 , 90 + self.delta, 110, 90 + self.delta],
            [70,  90 + self.delta, 110, 90 + self.delta, 110, 90 + self.delta, 70 , 90 + self.delta],
            [70,  90 - self.delta, 110, 90 - self.delta, 110, 90 - self.delta, 70 , 90 - self.delta]
        ])
        return 0.5 * ((linear * linear_sequence) + (1 - linear) * linear_sequence[::-1]) \
               + 0.5 * ((angular * angular_sequence) + (1 - angular) * angular_sequence[::-1])

    def compute_pose(self):
        """
        update the body pose by using the twist
        :param twist: the twist of the body pos refering to the legs
        :return: the correction to apply on the servos in order to achieve this body position
        """
        return self.corrections \
               + self.body_px * self.body_twist.linear.x * self.gain \
               + self.body_py * self.body_twist.linear.y * self.gain \
               + self.body_pz * self.body_twist.linear.z * self.gain \
               + self.body_ox * self.body_twist.angular.x * self.gain \
               + self.body_oy * self.body_twist.angular.y * self.gain \
               + self.body_oz * self.body_twist.angular.z * self.gain 

    def set_body_twist(self, twist):
        """
        Set the body twist value
        :param twist: twist info about the body position/orientation
        :return: None
        """
        print("body position updated to: %s" % twist)
        self.body_twist = Twist()
        self.body_twist.linear.x = max(min(twist.linear.x, self.bound), -self.bound)
        self.body_twist.linear.y = max(min(twist.linear.y, self.bound), -self.bound)
        self.body_twist.linear.z = max(min(twist.linear.z, self.bound), -self.bound)
        self.body_twist.angular.x = max(min(twist.angular.x, self.bound), -self.bound)
        self.body_twist.angular.y = max(min(twist.angular.y, self.bound), -self.bound)
        self.body_twist.angular.z = max(min(twist.angular.z, self.bound), -self.bound)


if __name__ == '__main__':
    rospy.init_node('gait_controller', anonymous=False)
    # controller = ServoController()
    quadripod = QuadripodModel()
    pub = rospy.Publisher(rospy.get_param("~motionsequence_topic", '/motionsequence'), MotionSequence, queue_size=1)
    default_step_delay = rospy.get_param("~default_step_delay", 0.200)
    default_serv_delay = rospy.get_param("~default_serv_delay", 0.)

    def move_callback(twist):
        rospy.loginfo("move callback called")
        msg = MotionSequence()
        rospy.loginfo("got move")
        positions = quadripod.walk(twist)
        body_pose = quadripod.compute_pose()
        if (abs(twist.linear.x) > 0.05) or (abs(twist.angular.z) > 0.05):
            # todo: replace controller.move by msg emission
            msg.positions = positions.flatten().astype(np.uint16)
            msg.correction = body_pose.astype(np.int16)
            msg.step_delay = default_step_delay
            msg.serv_delay = default_serv_delay
        else:
            rospy.loginfo("got move under threshold")
            # positions[-1, :] = quadripod.init_angles.astype(np.uint16)
            msg.positions = quadripod.init_angles.flatten().astype(np.uint8)
            msg.correction = body_pose.astype(np.int16)
            msg.step_delay = 0.
            msg.serv_delay = default_serv_delay
        pub.publish(msg)

    rospy.Subscriber(rospy.get_param("~cmd_vel_topic", "/cmd_vel"), Twist, move_callback, queue_size=1)
    rospy.Subscriber(rospy.get_param("~body_pose_topic", "/body_pose"), Twist, quadripod.set_body_twist, queue_size=1)

    # move the legs to initial position
    # controller.move(quadripod.init_angles, quadripod.corrections, 0., 0.25)
    msg = MotionSequence(
        positions=quadripod.init_angles.flatten().astype(np.uint8),
        correction=quadripod.compute_pose().astype(np.int16),
        serv_delay=0.25,
        step_delay=0.
    )
    # time.sleep(10)
    pub.publish(msg)
    rospy.spin()
