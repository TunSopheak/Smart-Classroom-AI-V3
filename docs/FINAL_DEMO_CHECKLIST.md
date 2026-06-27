# Final Demo Checklist

## Before demo

- [ ] Pull latest main branch
- [ ] Use correct virtual environment
- [ ] Check OpenCV face module
- [ ] Check YOLO import
- [ ] Run tests
- [ ] Start server on port 8001
- [ ] Open dashboard
- [ ] Reset demo data
- [ ] Confirm active session
- [ ] Confirm face model is trained
- [ ] Prepare phone for phone-use alert demo
- [ ] Prepare 10-15 second video recording demo

## Commands

```powershell
.\.venv\Scripts\python.exe -c "import cv2; print(cv2.__version__); print('cv2.face exists:', hasattr(cv2, 'face'))"
.\.venv\Scripts\python.exe -c "from ultralytics import YOLO; print('YOLO OK')"
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

## Pages to show

- [ ] Dashboard
- [ ] Academics
- [ ] Sessions
- [ ] AI Training
- [ ] AI Monitoring
- [ ] Behavior Reports
- [ ] Video Records
- [ ] Attendance
- [ ] System Status

## Demo order

1. Dashboard - explain workflow
2. Reset Demo
3. AI Training - explain camera/photo training
4. AI Monitoring - start camera and monitoring
5. Show face recognition
6. Show phone-use candidate alert
7. Record and save video evidence
8. Open Behavior Reports
9. Open Video Records
10. Open Attendance

## Safety explanation

- [ ] Mention that behavior detection is candidate-based
- [ ] Mention teacher review is required
- [ ] Mention system supports teacher, not replaces teacher
