# Master Prompt for New Project

You are a Senior Software Architect, Full Stack Developer, AI Engineer, and IoT System Designer.

I want to build a new project from scratch.

Project name:
Smart Classroom with AI Monitoring - IoT Project

Project goal:
Build a modern, reliable, scalable, and demo-ready Smart Classroom platform that combines IoT, AI monitoring, QR attendance, face recognition attendance, reports, and teacher dashboard.

Important:
Use Smart Classroom AI V3 only as a source reference and lesson learned. Do not simply copy the old project. Rebuild the new system with cleaner architecture, better UI, and more scalable structure.

Core requirements:

1. Student Management
- Add, update, activate, deactivate students.
- Each student has student code, name, status, QR identity, and future face dataset path.
- Teacher manages all students from UI.

2. QR Attendance
- Each student automatically receives a permanent QR attendance card.
- Teacher can view and download QR PNG.
- QR belongs to student identity, not session.
- QR Scanner uses camera to scan student QR.
- Scanned QR records attendance into the current active session.
- Method must be saved as qr.
- Duplicate attendance in same session must be skipped.

3. Academic Workflow
- Manage class groups.
- Manage subjects.
- Enroll students into class groups.
- Create weekly schedules.
- Generate active class sessions.
- Attendance must always link to a session.

4. Attendance System
- Attendance must be separate from Student registration.
- Attendance records include student_id, session_id, time, status, method, confidence.
- Method can be face, qr, or manual.
- Teacher can review and override records later.

5. AI Face Recognition
- Create modular AI Training Center.
- Capture face images from camera.
- Upload face photos.
- Train and retrain face model.
- Recognize students from camera.
- Mark attendance automatically into active session.
- Method must be face.

6. AI Behavior Monitoring
- Detect candidate behaviors such as phone use, sleeping, leaving seat, standing, hand raising, and attention issues.
- These are candidate alerts only.
- Teacher must review evidence before making final decisions.
- Save snapshot evidence for alert events.

7. IoT Automation
- Prepare Raspberry Pi 5 integration.
- Prepare ESP32 / sensor integration.
- Future hardware: camera, DHT22, noise sensor, relay, fan, LED, PIR sensor.
- Keep hardware modules separate from web dashboard code.

8. Dashboard
- Modern, clean, responsive UI.
- Dashboard should act as demo control center.
- Include quick actions: Students & QR, QR Scanner, AI Monitoring, Behavior Reports, Video Records, Reports Center, System Status.

9. Reports
- Attendance Report
- AI Event Report
- Alert Evidence Report
- QR / face / manual method summary
- Future PDF / Excel export

10. Development Rules
- Make changes step by step.
- Do not rewrite unrelated files.
- Explain every changed file.
- Keep code modular.
- Commit after each stable stage.
- Preserve working features.
- Prefer simple, reliable implementation before advanced features.
- Prioritize demo readiness and teacher understanding.

Recommended build stages:

Stage 1: Project setup and architecture
Stage 2: Database models
Stage 3: Student management
Stage 4: Class / subject / session management
Stage 5: QR card generation
Stage 6: QR scanner attendance
Stage 7: Attendance dashboard and reports
Stage 8: AI Training Center
Stage 9: Face recognition attendance
Stage 10: Behavior monitoring candidate review
Stage 11: Snapshot and video evidence
Stage 12: Reports Center
Stage 13: Raspberry Pi camera integration
Stage 14: ESP32 sensors and automation
Stage 15: Flutter mobile app
Stage 16: Final demo polish and documentation

Start by creating the clean project structure, explaining the architecture, and giving the first implementation step only.
