# Smart Classroom AI V3

Clean demo-ready Smart Classroom system.

## Core Goal

Help teachers manage classroom attendance and monitoring using:

- AI Face Attendance
- AI Training Center
- Behavior Monitoring Candidate Review
- Computer Webcam
- Optional Raspberry Pi camera/snapshot support

## Stage Plan

1. Project skeleton + database + students + sessions + attendance logic
2. Computer webcam + clean AI Monitoring page
3. Face Dataset Management + AI Training Center
4. Face Recognition Auto Attendance
5. Behavior Monitoring candidates
6. Raspberry Pi optional snapshot/live stream
7. Dashboard polish + demo instructions

## Run

PowerShell commands:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload

Open:

http://127.0.0.1:8000
http://127.0.0.1:8000/ai-monitoring

## Face Dataset Format

Do not commit dataset images.

models/face_dataset/STU0001_TunSopheak/01.jpg
models/face_dataset/STU0001_TunSopheak/02.jpg

The code before underscore must match student_code in the database.
