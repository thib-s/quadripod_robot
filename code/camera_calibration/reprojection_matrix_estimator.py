import cv2
import numpy as np
import sys

img_points = []
world_points = []

i = 0

def warp_constant_TRR(img, M, shape=None):
    if shape is None:
        shape = img.shape
    return cv2.warpPerspective(img, M, (shape[1], shape[0]))

def callback(event, x, y, flags, param):
    global i
    if event==4:
        print("img coord: %i, %i" % (x, y))
        try:
            w_coord_str  = input("coordinates in the real world (; separated) or 'q' to undo :")
            if w_coord_str != "q":
                w_y_str, w_x_str = w_coord_str.strip().split(';')
                w_x = float(w_x_str)
                w_y = float(w_y_str)
                img_points.append((x,y))
                world_points.append((w_x, w_y))
                i += 1
        except :
            print("error while reading the coordinates...")
            # e = sys.exc_info()[0]
            # print(e)


window_name = "test"
print("this soft intend to compute the rectification matrix for the camera:")
print("in order to use it, keep this terminal opened, and clic on a pixel in the image")
print("then enter the position in the robot frame, in cm")
print("X axis is the forward direction in the robot frame")
print("Y axis is the side direction in the robot frame (left has negative values, right has positive)")
im_disp = None
while im_disp is None:
    img_name = input("please enter the image file path: ")
    im_disp = cv2.imread(img_name)
cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
cv2.setMouseCallback(window_name, callback)
key = 0
while (i < 4) and (key!=ord('r')):
    cv2.imshow(window_name,im_disp)
    key = cv2.waitKey(10) & 0xFF
img_points = np.matrix(img_points, dtype=np.float32)
world_points = np.matrix(world_points, dtype=np.float32)
print(img_points)
print(world_points)
res = int(input("please enter world resolution (pix/cm) :"))
minX = int(input("min X coordinate in the image (cm):"))
maxX = int(input("max X coordinate in the image (cm):"))
minY = int(input("min Y coordinate in the image (cm):"))
maxY = int(input("max Y coordinate in the image (cm):"))
print(res)
world_points[:,0] -= minX
world_points[:,1] -= minY
world_points *= res
out_image_shape = ((maxY-minY)*res, (maxX-minX)*res)
print("output image shape: %i, %i" % out_image_shape)
transformation_matrix = cv2.getPerspectiveTransform(img_points, world_points)
rectified_img = warp_constant_TRR(im_disp, transformation_matrix, out_image_shape)
# rectified_img = cv2.remap(src=im_disp,map1=img_points,map2=world_points,interpolation=cv2.INTER_LINEAR)
# print(rectified_img) 
# print("x max: %i" % world_points[:,1].max())
# print("y max: %i" % world_points[:,0].max())
cv2.imshow("rectified image", rectified_img)#cv2.resize(rectified_img, (400,200)))
while key!=ord('q'):
    key = cv2.waitKey() & 0xFF
print(transformation_matrix)
# Press key `q` to quit the program
exit()
