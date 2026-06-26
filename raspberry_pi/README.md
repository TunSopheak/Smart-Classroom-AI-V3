# Raspberry Pi 5 Integration Notes

Device: Raspberry Pi 5 2GB

## Role in Smart Classroom AI V3

The Raspberry Pi can be used as a classroom camera device.

Recommended roles:

1. Camera source near classroom entrance
2. Capture student face when entering
3. Send snapshot/frame to the backend
4. Backend performs face recognition attendance
5. Web dashboard shows attendance and AI monitoring results

## Why computer camera is used in the demo

For presentation reliability, the current demo uses the computer webcam.

Reasons:

- Easier to test
- Faster debugging
- More stable during presentation
- Avoids Raspberry Pi camera driver/network issues

## Recommended classroom setup

- Raspberry Pi camera near entrance for attendance
- Wider classroom camera for behavior monitoring
- Teacher dashboard on laptop or projector

## Future Pi Client Flow

1. Raspberry Pi captures image from camera
2. Encodes image as base64
3. Sends image to backend endpoint
4. Backend returns recognized student, attendance status, and behavior candidates

## Important

For Raspberry Pi 5 2GB, keep AI lightweight.

Recommended:

- Use OpenCV Haar + LBPH for face attendance
- Avoid heavy YOLO models during live demo
- Use optional snapshot mode instead of high FPS video stream
