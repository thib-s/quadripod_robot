// Use the image_transport classes instead.

#include <ros/ros.h>
#include <image_transport/image_transport.h>
#include <cv_bridge/cv_bridge.h>
#include <sensor_msgs/image_encodings.h>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/highgui/highgui.hpp>
#include "std_msgs/Float32.h"
#include <stdio.h>

//static const std::string OPENCV_WINDOW = "Image window";
//static const std::string OPENCV_WINDOW2 = "Image window 2";
#define WIDTH 300
#define HEIGHT 250

using namespace cv;
static const Matx<float, 3, 3> M = {-3.05982034e-01, -8.62902667e-01,  2.20658626e+02,
               -3.59717139e-03,  3.65197655e-01, -1.40549509e+02,
               1.72874841e-04, -5.67108638e-03,  1.00000000e+00};
//{2.83879261e-01, -4.35035750e-01, 1.47285409e+01,
//               2.06979923e-03, 3.66344984e-01, -1.44948536e+02,
//               -9.84997247e-05, -5.84897619e-03, 1.0};
//static const Mat M = Mat(3,3, CV_32F, m);

class ImageConverter {
  ros::NodeHandle nh_;
  image_transport::ImageTransport it_;
  image_transport::Subscriber image_sub_;
//  image_transport::Publisher image_pub_;
  ros::Publisher delta_pub;
  Mat src_gray, src_warp, src_smoothed;
  Mat grad_x, grad_y, abs_grad_x, abs_grad_y, angles, magnitude;
  int scale = 1;
  int d = 0;
  int ddepth = CV_16S;
  int sum, lum, lumsum;
  float mean_angle, mean_magnitude;
  float delta;

public:
    ImageConverter() : it_(nh_) //c++11 syntax (call it_(nh_) prior to this func )
    {
//        cv::startWindowThread();
//        image_transport::ImageTransport it_(nh_);
	    this->image_sub_ = it_.subscribe("/raspicam_node/image", 1, &ImageConverter::imageCallback, this);
	    this->delta_pub = nh_.advertise<std_msgs::Float32>("/plannar_cam/delta", 1);
//	    this->image_pub_ = it_.advertise("/plannar_cam/image", 1);
//        // Subscrive to input video feed and publish output video feed
//        image_sub_ = it_.subscribe("/camera/image_raw", 1,
//        &ImageConverter::imageCb, this);
//        image_pub_ = it_.advertise("/image_converter/output_video", 1);

//        cv::namedWindow(OPENCV_WINDOW);
//        cv::namedWindow(OPENCV_WINDOW2);
    }


    ~ImageConverter()
    {
//    cv::destroyWindow(OPENCV_WINDOW);
    }

    void imageCallback(const sensor_msgs::ImageConstPtr& msg)
    {
        cv_bridge::CvImageConstPtr cv_ptr;//CvImagePtr cv_ptr;
        try
        {
            cv_ptr = cv_bridge::toCvShare(msg, "bgr8");//cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::BGR8);
            cvtColor( cv_ptr->image, src_gray, CV_BGR2GRAY );
            warpPerspective(src_gray, src_warp, M, Size(WIDTH, HEIGHT));
            medianBlur(src_warp, src_smoothed, 11);
            src_smoothed.convertTo(src_smoothed, CV_64F);
            src_smoothed /= 255.0;
            Sobel( src_smoothed, grad_x, ddepth, 1, 0, 5, scale, d, BORDER_DEFAULT);
            convertScaleAbs( grad_x, abs_grad_x );
            Sobel( src_smoothed, grad_y, ddepth, 0, 1, 5, scale, d, BORDER_DEFAULT);
            convertScaleAbs( grad_y, abs_grad_y );
            addWeighted( abs_grad_x, 0.5, abs_grad_y, 0.5, 0, magnitude );
            sum = 0;
            lumsum = 0;
            lum;
            for (int i = 200; i < magnitude.rows; ++i)
            {
                uchar* pixel = magnitude.ptr<uchar>(i);
                for (int j = 0; j < magnitude.cols; ++j)
                {
                    lum = *pixel++;
                    sum += j * lum;
                    lumsum += lum;
                }
            }
            delta = (float)(sum)/((float)(lumsum)*5.);
            printf("res is %.3f \n", (float)(sum)/(float)(lumsum));
//            cartToPolar( grad_x, grad_y, magnitude, angles);

        }
        catch (cv_bridge::Exception& e)
        {
            ROS_ERROR("cv_bridge exception: %s", e.what());
            return;
        }
//        magnitude *= 255;
//        magnitude.convertTo(magnitude, CV_8U);
//         cv::imshow(OPENCV_WINDOW, magnitude);
//         cv::imshow(OPENCV_WINDOW2, src_smoothed);
//         cv::waitKey(3);
         //cv_ptr->image = grad;
//         this->image_pub_.publish(cv_ptr->toImageMsg());
        std_msgs::Float32 msg_delta;
        msg_delta.data = delta;
        this->delta_pub.publish(msg_delta);
    }

};

int main(int argc, char **argv)
{
	ros::init(argc, argv, "image_converter");
//	ros::NodeHandle nh_;
	ImageConverter ic = ImageConverter();
//	ros::Rate loop_rate(10);
	ros::spin();
//    while (ros::ok())
//    {
//        ros::spinOnce();
//        loop_rate.sleep();
//    }
    return 0;
}
