/* Shim (ours): OpenCV 2.x "highgui.h" -> imgcodecs (imread/imwrite). No GUI is used by the compiled core files. */
#pragma once
#include <opencv2/imgcodecs.hpp>
