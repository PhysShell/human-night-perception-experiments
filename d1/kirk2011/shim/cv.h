/* Shim (ours): the plugin was written against OpenCV 2.3 "cv.h"; map it to the OpenCV 4 C++ headers.
   Only headers; no donor arithmetic lives here. */
#pragma once
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/imgcodecs.hpp>
