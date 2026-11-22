@echo off
REM One-time download of the offline vision models (about 60 MB). After this, camera recognition needs no internet.
cd /d "%~dp0.."
if not exist models mkdir models
curl -L -o models\face_detection_yunet_2023mar.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
curl -L -o models\face_recognition_sface_2021dec.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
curl -L -o models\mobilenetv2-12.onnx https://github.com/onnx/models/raw/main/validated/vision/classification/mobilenet/model/mobilenetv2-12.onnx
dir models
echo If any file is only a few KB, the download failed. Run this script again with internet on.
