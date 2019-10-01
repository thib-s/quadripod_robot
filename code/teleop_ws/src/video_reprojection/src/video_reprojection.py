#!/usr/bin/env python
from __future__ import print_function

# import roslib
# roslib.load_manifest('my_package')
import sys
import rospy
import cv2
from std_msgs.msg import String, Float32
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge, CvBridgeError
import numpy as np

M = np.matrix([[2.83879261e-01, -4.35035750e-01, 1.47285409e+01],
               [2.06979923e-03, 3.66344984e-01, -1.44948536e+02],
               [-9.84997247e-05, -5.84897619e-03, 1.0]], dtype=np.float32)


def warp_constant_TRR(img):
    return cv2.warpPerspective(img, M, (150, 250))


class image_converter:

    def __init__(self):
        self.image_pub = rospy.Publisher("/plannar_cam/image", Image, queue_size=1)
        self.angle_pub = rospy.Publisher("/plannar_cam/theta", Float32, queue_size=1)
        self.delta_pub = rospy.Publisher("/plannar_cam/delta", Float32, queue_size=1)

        self.bridge = CvBridge()
        self.image_sub = rospy.Subscriber("/raspicam_node/image", Image, self.callback)

    @staticmethod
    def to_bw(img):
        return cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)[50:, :], 11)
        # 11 car bordure de 2cm et precision de 5pix/cm (nombre pairs exclus dans medianBlur)

    @staticmethod
    def compute_gradients(bw_img):
        sobelx = cv2.Sobel(bw_img, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(bw_img, cv2.CV_64F, 0, 1, ksize=3)
        angles = np.arctan2(sobely, sobelx)
        angles[angles > (np.pi / 2)] -= np.pi
        angles[angles < (-np.pi / 2)] += np.pi
        modules = np.sqrt(np.square(sobelx) + np.square(sobely))
        return angles, modules

    @staticmethod
    def extract_theta(angles, modules):
        # avg_angle = np.average(angles, weights=modules)
        values, bins = np.histogram(angles.flatten(), bins=np.arange(-np.pi * 0.5, +np.pi * 0.5, 0.05),
                                    weights=modules.flatten(), density=True)
        # print("sum of modules (theta): %.2f" % modules.sum())
        # print(values)
        major_angle_idx = np.argmax(values)
        major_angle = 0.5 * (bins[major_angle_idx] + bins[major_angle_idx + 1])
        # print("angle: %.3f" % np.rad2deg(avg_angle))
        if modules.sum() > 500000:
            print("major angle: %.3f" % np.rad2deg(major_angle))
            return major_angle
        else:
            print("houston, we lost the line")
            return None

    @staticmethod
    def extract_delta(angles, modules):
        # pos_values, pos_bins = np.histogram(range(150), bins=range(150), weights=np.average(modules[-25:,:], axis=0), density=True)
        # major_pos_idx = np.argmax(pos_values)
        major_pos_idx = np.average(range(150), weights=np.average(modules[-50:, :], axis=0))
        major_pos = (major_pos_idx - 75) / 5  # conversion en cm
        # print("sum of modules (delta): %.2f" % modules[-50:,:].sum())
        if (modules[-50:, :].sum()) > 70000:
            print("major_pos : %.1f" % major_pos)
            return major_pos
        else:
            print("houston we lost the line end")
            return None

    @staticmethod
    def display_vector_field(angles, modules):
        hsv_field = np.ndarray((angles.shape[0], angles.shape[1], 3), dtype=np.float32)
        hsv_field[:, :, 0] = 255 * (angles + (np.pi / 2)) / np.pi  # map angle to hue in [0, 255]
        hsv_field[:, :, 2] = (modules - modules.min()) / (modules.max() - modules.min())  # map module to value [0,1]
        hsv_field[:, :, 1] = 1.  # constant staturation
        bw_img = cv2.cvtColor(hsv_field, cv2.COLOR_HSV2RGB)  # back to rgb
        cv2.imshow("Image window", bw_img)
        cv2.waitKey(3)

    def callback(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
            cv_image = warp_constant_TRR(cv_image)
            bw_img = self.to_bw(cv_image)
            angles, modules = self.compute_gradients(bw_img)
            delta = self.extract_delta(angles, modules)
            if delta is not None:
                self.delta_pub.publish(Float32(delta))
            theta = self.extract_theta(angles, modules)
            if theta is not None:
                self.angle_pub.publish(Float32(theta))
            self.image_pub.publish(self.bridge.cv2_to_imgmsg(cv_image, "bgr8"))
        except CvBridgeError as e:
            print(e)


def main(args):
    ic = image_converter()
    rospy.init_node('image_reprojection', anonymous=True)
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down")
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main(sys.argv)
