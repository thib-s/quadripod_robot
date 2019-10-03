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

IMG_H = 350

IMG_W = 300

DELTA_BAND = 50

M = np.matrix([[-3.05982034e-01, -8.62902667e-01,  2.20658626e+02],
               [-3.59717139e-03,  3.65197655e-01, -1.40549509e+02],
               [1.72874841e-04, -5.67108638e-03,  1.00000000e+00]], dtype=np.float32)


def warp_constant_TRR(img):
    return cv2.warpPerspective(img, M, (IMG_W, IMG_H))


class image_converter:

    def __init__(self):
        self.image_pub = rospy.Publisher("/plannar_cam/image", Image, queue_size=1)
        # self.angle_pub = rospy.Publisher("/plannar_cam/theta", Float32, queue_size=1)
        self.delta_pub = rospy.Publisher("/plannar_cam/delta", Float32, queue_size=1)

        self.bridge = CvBridge()
        self.image_sub = rospy.Subscriber("/raspicam_node/image", Image, self.callback)

    @staticmethod
    def to_bw(img):
        return cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)[-DELTA_BAND:, :], 11)
        # 11 car bordure de 2cm et precision de 5pix/cm (nombre pairs exclus dans medianBlur)

    @staticmethod
    def compute_gradients(bw_img):
        sobelx = cv2.Sobel(bw_img, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(bw_img, cv2.CV_64F, 0, 1, ksize=3)
        return None, np.sqrt(np.square(sobelx) + np.square(sobely))#cv2.addWeighted(np.abs(sobelx), 0.5, np.abs(sobely), 0.5, 0)
        # magnitudes, angles = cv2.cartToPolar(sobelx, sobely)
        # # angles = np.arctan2(sobely, sobelx)
        # angles[angles > (np.pi / 2)] -= np.pi
        # angles[angles < (-np.pi / 2)] += np.pi
        # # modules = np.sqrt(np.square(sobelx) + np.square(sobely))
        # return angles, magnitudes

    # @staticmethod
    # def extract_theta(angles, modules):
    #     # avg_angle = np.average(angles, weights=modules)
    #     values, bins = np.histogram(angles.flatten(), bins=np.arange(-np.pi * 0.5, +np.pi * 0.5, 0.05),
    #                                 weights=modules.flatten(), density=True)
    #     # print("sum of modules (theta): %.2f" % modules.sum())
    #     # print(values)
    #     major_angle_idx = np.argmax(values)
    #     major_angle = 0.5 * (bins[major_angle_idx] + bins[major_angle_idx + 1])
    #     # print("angle: %.3f" % np.rad2deg(avg_angle))
    #     if modules.sum() > 500000:
    #         print("major angle: %.3f" % np.rad2deg(major_angle))
    #         return major_angle
    #     else:
    #         print("houston, we lost the line")
    #         return None

    @staticmethod
    def extract_delta(modules):
        # pos_values, pos_bins = np.histogram(range(IMG_W), bins=range(IMG_W), weights=np.average(modules[-25:,:], axis=0), density=True)
        # major_pos_idx = np.argmax(pos_values)
        major_pos_idx = np.average(range(IMG_W), weights=np.average(modules[-DELTA_BAND:, :], axis=0))
        major_pos = (major_pos_idx - (IMG_W/2)) / 5  # conversion en cm
        # print("sum of modules (delta): %.2f" % modules[-DELTA_BAND:,:].sum())
        if (modules[-DELTA_BAND:, :].sum()) > 30000:
            print("major_pos : %.1f" % major_pos)
            return major_pos
        else:
            print("houston we lost the line end")
            return None

    # @staticmethod
    # def display_vector_field(angles, modules):
    #     hsv_field = np.ndarray((angles.shape[0], angles.shape[1], 3), dtype=np.float32)
    #     hsv_field[:, :, 0] = 255 * (angles + (np.pi / 2)) / np.pi  # map angle to hue in [0, 255]
    #     hsv_field[:, :, 2] = (modules - modules.min()) / (modules.max() - modules.min())  # map module to value [0,1]
    #     hsv_field[:, :, 1] = 1.  # constant staturation
    #     bw_img = cv2.cvtColor(hsv_field, cv2.COLOR_HSV2RGB)  # back to rgb
    #     cv2.imshow("Image window", bw_img)
    #     cv2.waitKey(3)

    def callback(self, data):
        try:
            cv_image = cv2.resize(self.bridge.imgmsg_to_cv2(data, "bgr8"), (410, 308))
            cv_image = warp_constant_TRR(cv_image)
            bw_img = self.to_bw(cv_image)
            angles, magnitudes = self.compute_gradients(bw_img)
            delta = self.extract_delta(magnitudes)
            if delta is not None:
                self.delta_pub.publish(Float32(delta))
            # theta = self.extract_theta(angles, magnitudes)
            # if theta is not None:
            #     self.angle_pub.publish(Float32(theta))
            self.image_pub.publish(self.bridge.cv2_to_imgmsg(np.array(bw_img, dtype=np.uint8), "8UC1"))# cv_image, "rgb8"))
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
