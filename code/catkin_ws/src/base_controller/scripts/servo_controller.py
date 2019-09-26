#!/usr/bin/env python

import rospy
from base_controller.msg import MotionSequence
import time
import numpy as np
import pigpio


def deg2ms(angle):
    return (angle / 180.0) * 1000.0 + 1000.0


class ServoController():

    def __init__(self, pins=None):
        """
        Initialize the servo and move them to the standby position
        :return: nothing
        """
        if pins is None:
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

    def move(self, msg):
        """
        Take a motion sequence message and apply it to the servos
        :param msg: a MotionSequence message
        :return: None
        """
        raw_pos = msg.positions
        positions_sequence = np.array(raw_pos, dtype=np.uint16).reshape((len(raw_pos)/8, 8))
        for step in positions_sequence:
            for i, pin in enumerate(self.pins):
                self.pi.set_servo_pulsewidth(pin, deg2ms(step[i] + msg.correction[i]))
            	time.sleep(msg.serv_delay)
            time.sleep(msg.step_delay)

    def release(self):
        """
        release all servos and stop the deamon
        :return:
        """
        for pin in self.pins:
            self.pi.set_servo_pulsewidth(pin, 0)  # stop servo pulses
        self.pi.stop()  # terminate connection and release resources


if __name__ == '__main__':
    rospy.init_node('servo_controller', anonymous=False)
    controller = ServoController()
    # move the legs to initial position
    rospy.Subscriber("/motionsequence", MotionSequence, controller.move, queue_size=1)
    # todo add rospy shutdown handler
    rospy.on_shutdown(controller.release)
    rospy.spin()
