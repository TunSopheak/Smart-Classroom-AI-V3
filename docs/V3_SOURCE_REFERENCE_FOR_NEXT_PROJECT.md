# V3 Source Reference for Next Project

## New Project Name

Smart Classroom with AI Monitoring - IoT Project

## Purpose

This document uses Smart Classroom AI V3 as a source reference for building a cleaner, cooler, and more scalable new project from scratch.

The new project should not simply copy V3. It should learn from V3 and rebuild with better architecture, better UI, and better IoT/AI separation.

## Important V3 Lessons

1. Attendance must be separate from student registration.
2. QR card should belong to each student, not to a session.
3. QR actions should be inside Student Management.
4. QR scanner should show inline scan status instead of jumping to another page.
5. Active session should be the source of truth for attendance.
6. Face recognition and QR attendance should save method separately: face / qr / manual.
7. Behavior detection should be candidate review only, not final punishment.
8. Snapshot and video evidence help teachers review later.
9. Reports Center makes the system easier to explain.
10. Dashboard should act as the final demo control center.

## V3 Main Workflows

### Student QR Workflow

1. Teacher creates student.
2. System generates permanent QR identity.
3. Teacher views or downloads QR card.
4. Student uses same QR every class.
5. QR Scanner scans the card.
6. System records attendance into current active session.

### Face Recognition Workflow

1. Teacher captures or uploads student face images.
2. System trains face model.
3. AI Monitoring recognizes student.
4. System records attendance into active session.
5. Method is saved as face.

### Behavior Monitoring Workflow

1. AI Monitoring detects behavior candidates.
2. Phone-use candidate creates red alert frame.
3. System saves snapshot evidence.
4. Teacher reviews Behavior Reports later.

### Reports Workflow

Reports Center shows:

- Attendance summary
- Present / Late / Absent count
- Face / QR / Manual method count
- AI event summary
- Alert evidence review

## Recommended New Project Structure

smart-classroom-iot-project/
  backend/
    app/
      api/
      core/
      models/
      schemas/
      services/
      ai/
      iot/
      database/
  frontend/
    web-dashboard/
  mobile/
    flutter-app/
  edge/
    raspberry-pi/
  firmware/
    esp32/
  docs/

## Recommended Build Order

1. Project setup and clean architecture
2. Database models
3. Student management
4. Class / subject / session management
5. QR card generation
6. QR scanner attendance
7. Attendance dashboard and reports
8. AI Training Center
9. Face recognition attendance
10. Behavior monitoring candidate review
11. Snapshot and video evidence
12. Reports Center
13. Raspberry Pi camera integration
14. ESP32 sensors and automation
15. Flutter mobile app
16. Final demo polish and documentation
