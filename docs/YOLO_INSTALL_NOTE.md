# YOLO + Face Recognition Install Note

This project uses both:

- opencv-contrib-python for LBPH face recognition (`cv2.face`)
- ultralytics YOLO for phone/book/person object detection

Do not install YOLO using plain:

pip install ultralytics

because it may install `opencv-python` and break `cv2.face`.

Safe install order:

1. Install core packages:

.\.venv\Scripts\python.exe -m pip install fastapi "uvicorn[standard]" sqlalchemy jinja2 python-multipart numpy pillow httpx opencv-contrib-python

2. Install YOLO dependencies:

.\.venv\Scripts\python.exe -m pip install torch torchvision matplotlib pyyaml requests scipy tqdm psutil py-cpuinfo pandas polars ultralytics-thop

3. Install ultralytics without dependencies:

.\.venv\Scripts\python.exe -m pip install ultralytics --no-deps

4. Verify:

.\.venv\Scripts\python.exe -c "import cv2; print(cv2.__version__); print(hasattr(cv2, 'face'))"
.\.venv\Scripts\python.exe -c "from ultralytics import YOLO; print('YOLO OK')"

Expected:

cv2.face exists = True
YOLO OK
