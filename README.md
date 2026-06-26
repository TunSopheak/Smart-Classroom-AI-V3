# Smart Classroom AI V3

A clean demo-ready Smart Classroom system using AI face recognition attendance and behavior monitoring candidate review.

## Core Goal

Help teachers manage classroom attendance and classroom monitoring using:

- AI Training Center
- Face Recognition Attendance
- Auto Attendance
- Behavior Monitoring Candidate Review
- Computer Webcam Demo
- Raspberry Pi 5 readiness

## Current Features

1. Student management
2. Session management
3. Demo reset for clean presentation
4. Face dataset capture from webcam
5. LBPH face model training
6. Face recognition attendance
7. Duplicate attendance protection
8. Behavior monitoring candidate review
9. Person count and estimated body/person box
10. System status page
11. Raspberry Pi 5 deployment notes

## Run Project

PowerShell:

cd D:\IT\IT-RUPP\Y3\CN\Project\Smart-Classroom-AI-V3
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001

Open:

http://127.0.0.1:8001

## Main Pages

Dashboard: http://127.0.0.1:8001
Students: http://127.0.0.1:8001/students
Sessions: http://127.0.0.1:8001/sessions
Attendance: http://127.0.0.1:8001/attendance
AI Training: http://127.0.0.1:8001/training
AI Monitoring: http://127.0.0.1:8001/ai-monitoring
System Status: http://127.0.0.1:8001/system-status
Health JSON: http://127.0.0.1:8001/health

## Demo Flow

1. Open Dashboard.
2. Click Reset Demo.
3. Go to AI Training.
4. Select student.
5. Start camera.
6. Capture 10 to 20 face images.
7. Click Train or Retrain Face Model.
8. Go to AI Monitoring.
9. Start camera.
10. Click Analyze Once or Start AI Monitoring.
11. The system recognizes the student and records attendance automatically.
12. Behavior Monitoring shows person count and body/person candidate box.

## Face Dataset Format

Do not commit dataset images.

models/face_dataset/STU0001_TunSopheak/001.jpg
models/face_dataset/STU0001_TunSopheak/002.jpg

The code before underscore must match student_code in the database.

## Git Ignore Reminder

These must stay local only:

smart_classroom_ai_v3.db
models/face_dataset/
models/face_model.yml
models/face_labels.json
.venv/

## Raspberry Pi 5 Note

The current demo uses a computer webcam for stability. Raspberry Pi 5 can be used later as the classroom camera source.

Recommended deployment:

- Raspberry Pi 5 with camera near classroom entrance for face attendance
- Computer/web dashboard for teacher monitoring
- Optional Pi snapshot/live stream endpoint in later deployment
- Raspberry Pi 5 2GB should avoid heavy models during demo

## Limitations

- LBPH face recognition works best with clear face images.
- Far classroom distance may reduce recognition accuracy.
- Behavior Monitoring currently uses candidate review, not final student judgment.
- Body/person box is estimated from face position for demo safety.
- Phone-use detection is planned as an optional advanced model.
