#!/usr/bin/env python

# pulse.py

import rospy
from geometry_msgs.msg import Twist
import time
import numpy as np
import pigpio

deg2ms = lambda angle: (angle / 180.0) * 1000.0 + 1000.0


class ServoController():

    def __init__(self, pins=None):
        """
        Initialize the servo and move them to the standby position
        :return: nothing
        """
        if pins is None:
            # pins = [16, 20, 21, 26, 19, 13, 6, 5]
            # pins = [21, 26, 16, 20,6, 5, 19, 13]
            pins = [6,5,19,13,21,26,16,20]
        # gpio ids of each servo
        self.pins = pins

        self.pi = pigpio.pi()  # Connect to local Pi.

        # set gpio modes
        for pin in self.pins:
            self.pi.set_mode(pin, pigpio.OUTPUT)
        # start 1500 us servo pulses on gpio4
        for pin in self.pins:
            self.pi.set_servo_pulsewidth(pin, 1500)
            time.sleep(0.25)

    def move(self, position_sequence, correction, delay_step=0.25, delay_serv=0.0):
        for step in position_sequence:
            for i, pin in enumerate(self.pins):
                self.pi.set_servo_pulsewidth(pin, deg2ms(step[i] + correction[i]))
                time.sleep(delay_serv)
            time.sleep(delay_step)

    def release(self):
        """
        release all servos and stop the deamon
        :return:
        """
        for pin in self.pins:
            self.pi.set_servo_pulsewidth(pin, 0)  # stop servo pulses
        self.pi.stop()  # terminate connection and release resources


class QuadripodModel():

    def __init__(self,):

        ################################################
        # static params of the gait
        ################################################

        # how much to raise the legs when walking
        self.delta = 20

        self.init_angles = np.array(
            [[90, 90 + self.delta, 90, 90 - self.delta, 90, 90 - self.delta, 90, 90 + self.delta]])
        # values to correct mechanical alignment of servos
        self.corrections = np.array([-20, 10, 20, 0, 20, 20, -20, 0])

        # how to affect the values when moving the body without walking
        # body_p* refers to position
        # body_o* refers to orientation
        self.body_pz = np.array([0, 1, 0, -1, 0, -1, 0, 1])
        self.body_px = np.array([-1, 0, 1, 0, -1, 0, 1, 0])
        self.body_py = np.array([0, 0, 0, 0, 0, 0, 0, 0])  # None
        self.body_ox = np.array([0, -1, 0, -1, 0, 1, 0, 1])  # untested
        self.body_oy = np.array([0, 1, 0, -1, 0, 1, 0, -1])
        self.body_oz = np.array([0, 0, 0, 0, 0, 0, 0, 0])  # None

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
        linear = 0.5 * twist.linear.y + 0.5
        angular = 0.5 * twist.angular.z + 0.5
        linear_sequence = np.array([
            [75, 90, 70, 90 - self.delta, 110, 90 - self.delta, 105, 90],
            [75, 90 + self.delta, 70, 90, 110, 90, 105, 90 + self.delta],
            [110, 90 + self.delta, 110, 90, 75, 90, 60, 90 + self.delta],
            [110, 90, 110, 90 - self.delta, 75, 90 - self.delta, 60, 90]
        ])
        angular_sequence = np.array([
            [110, 90, 70, 90 - self.delta, 75, 90 - self.delta, 105, 90],
            [110, 90 + self.delta, 70, 90, 75, 90, 105, 90 + self.delta],
            [75, 90 + self.delta, 110, 90, 110, 90, 60, 90 + self.delta],
            [75, 90, 110, 90 - self.delta, 110, 90 - self.delta, 60, 90]
        ])
        return 0.5 * ((linear * linear_sequence) + (1 - linear) * linear_sequence[::-1]) \
               + 0.5 * ((angular * angular_sequence) + (1 - angular) * angular_sequence[::1])

    def compute_pose(self):
        """
        update the body pose by using the twist
        :param twist: the twist of the body pos refering to the legs
        :return: the correction to apply on the servos in order to achieve this body position
        """
        return self.corrections \
               + self.body_px * self.body_twist.linear.x \
               + self.body_py * self.body_twist.linear.y \
               + self.body_pz * self.body_twist.linear.z \
               + self.body_ox * self.body_twist.angular.x \
               + self.body_oy * self.body_twist.angular.y \
               + self.body_oz * self.body_twist.angular.z

    def set_body_twist(self, twist):
        """
        Set the body twist value
        :param twist: twist info about the body position/orientation
        :return: None
        """
        self.body_twist = twist


if __name__ == '__main__':
    rospy.init_node('base_controller', anonymous=False)
    controller = ServoController()
    quadripod = QuadripodModel()
    # move the legs to initial position
    controller.move(quadripod.init_angles, quadripod.corrections, 1., 1.)

    def move_callback(twist):
        if (abs(twist.linear.y) > 0.05) and (abs(twist.angular.z) > 0.05):
            walk_sequence = quadripod.walk(twist)
            body_pose = quadripod.compute_pose()
            # todo: replace controller.move by msg emission
            controller.move(walk_sequence, body_pose + quadripod.corrections)
        else:
            controller.move(quadripod.init_angles, quadripod.corrections)


    rospy.Subscriber("/cmd_vel", Twist, move_callback, queue_size=1)
    rospy.Subscriber("/body_pose", Twist, quadripod.set_body_twist, queue_size=1)
    # todo add rospy shutdown handler
    # rospy.spin()
    time.sleep(10)
    controller.release()
