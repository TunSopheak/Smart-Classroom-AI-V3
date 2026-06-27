# Teacher Explanation Notes

## What the system can do

- Recognize student faces
- Show student names on frame boxes
- Mark attendance automatically
- Detect phone-use candidates using YOLO object detection
- Highlight alerts with red frame boxes
- Save behavior alert snapshots
- Record AI monitoring video with frame boxes
- Store video evidence for later review
- Organize workflow by class, subject, schedule, and session

## Color meaning

- Green: recognized student / normal
- Blue: person or body candidate
- Amber: warning or object candidate
- Red: alert candidate, such as phone-use
- Yellow: unknown or low-confidence face

## Important limitation

Phone-use detection is a candidate alert, not a final judgment. The system highlights possible phone use and saves evidence. The teacher reviews the snapshot or video before making any decision.

## Why video and snapshot are needed

A snapshot helps the teacher quickly see the alert moment. A video helps the teacher review the full context before and after the alert.

## Why student name is shown

Showing only student ID can confuse the viewer. Showing the student name on the frame box helps the teacher and team verify immediately if the AI recognizes correctly.
