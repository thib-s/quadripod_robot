#!/usr/bin/env python

# pulse.py

import rospy
from geometry_msgs.msg import Twist
from base_controller.msg import MotionSequence
import time
import numpy as np
# import pigpio

deg2ms = lambda angle: (angle / 180.0) * 1000.0 + 1000.0


# class ServoController():
#
#     def __init__(self, pins=None):
#         """
#         Initialize the servo and move them to the standby position
#         :return: nothing
#         """
#         if pins is None:
#             # pins = [16, 20, 21, 26, 19, 13, 6, 5]
#             # pins = [21, 26, 16, 20,6, 5, 19, 13]
#             pins = [6,5,19,13,21,26,16,20]
#             # pins = [5,6,13,19,26,21,20,16]
#         # gpio ids of each servo
#         self.pins = pins
#
#         self.pi = pigpio.pi()  # Connect to local Pi.
#
#         # set gpio modes
#         for pin in self.pins:
#             self.pi.set_mode(pin, pigpio.OUTPUT)
#         # start 1500 us servo pulses on gpio4
#         #for pin in self.pins:
#         #    self.pi.set_servo_pulsewidth(pin, 1500)
#         #    time.sleep(0.25)
#
#     def move(self, position_sequence, correction, delay_step=0.25, delay_serv=0.0):
#         for step in position_sequence:
#             for i, pin in enumerate(self.pins):
#                 self.pi.set_servo_pulsewidth(pin, deg2ms(step[i] + correction[i]))
#                 time.sleep(delay_serv)
#             time.sleep(delay_step)
#
#     def release(self):
#         """
#         release all servos and stop the deamon
#         :return:
#         """
#         for pin in self.pins:
#             self.pi.set_servo_pulsewidth(pin, 0)  # stop servo pulses
#         self.pi.stop()  # terminate connection and release resources


class QuadripodModel():

    def __init__(self,):

        ################################################
        # static params of the gait
        ################################################

        # how much to raise the legs when walking
        self.delta = 15

        self.init_angles = np.array(
            [[90, 90 + self.delta, 90, 90 - self.delta, 90, 90 - self.delta, 90, 90 + self.delta]])
        # values to correct mechanical alignment of servos
        self.corrections = np.array([-20, 40, 20, -30, 20, -20, -20, 40])

        # how to affect the values when moving the body without walking
        # body_p* refers to position
        # body_o* refers to orientation
        self.body_pz = np.array([0, 1, 0, -1, 0, -1, 0, 1]) # ok
        self.body_px = np.array([1, 0, -1, 0, 1, 0, -1, 0]) # ok
        self.body_py = np.array([-1, 0, 1, 0, 1, 0, -1, 0])  # not py but spacing
        self.body_ox = np.array([0, -1, 0, -1, 0, 1, 0, 1])  # ok
        self.body_oy = np.array([0, 1, 0, -1, 0, 1, 0, -1]) # ok
        self.body_oz = np.array([1, 0, 1, 0, 1, 0, 1, 0])  # ok
        self.gain = 10 # coefficient applied on body pose corrections

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
        linear = 0.5 * twist.linear.x + 0.5
        angular = 0.5 * twist.angular.z + 0.5
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
        self.body_twist.linear.x = twist.linear.x
        self.body_twist.linear.y = twist.linear.y
        self.body_twist.linear.z = twist.linear.z
        self.body_twist.angular.x = twist.angular.x
        self.body_twist.angular.y = twist.angular.y
        self.body_twist.angular.z = twist.angular.z


if __name__ == '__main__':
    rospy.init_node('gait_controller', anonymous=False)
    # controller = ServoController()
    quadripod = QuadripodModel()
    pub = rospy.Publisher('/motionsequence', MotionSequence, queue_size=1)

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
            msg.step_delay = 0.200
            msg.serv_delay = 0.
        else:
            rospy.loginfo("got move under threshold")
            # positions[-1, :] = quadripod.init_angles.astype(np.uint16)
            msg.positions = quadripod.init_angles.flatten().astype(np.uint8)
            msg.correction = body_pose.astype(np.int16)
            msg.step_delay = 0.
            msg.serv_delay = 0.
        pub.publish(msg)

    rospy.Subscriber("/cmd_vel", Twist, move_callback, queue_size=1)
    rospy.Subscriber("/body_pose", Twist, quadripod.set_body_twist, queue_size=1)
    # rospy.on_shutdown(controller.release)

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
