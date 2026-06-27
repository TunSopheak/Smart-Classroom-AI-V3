const startButton = document.getElementById("start-camera");
const stopButton = document.getElementById("stop-camera");
const video = document.getElementById("camera-preview");
const overlay = document.getElementById("detection-overlay");

const statusText = document.getElementById("camera-status");
const cameraBadge = document.getElementById("camera-badge");
const cameraFrame = document.getElementById("camera-frame");

const analyzeOnceButton = document.getElementById("analyze-once");
const startAIButton = document.getElementById("start-ai");
const stopAIButton = document.getElementById("stop-ai");

const faceAIBadge = document.getElementById("face-ai-badge");
const recognitionStatus = document.getElementById("recognition-status");
const recognitionList = document.getElementById("recognition-list");

const behaviorBadge = document.getElementById("behavior-badge");
const behaviorStatus = document.getElementById("behavior-system-status");
const personCountText = document.getElementById("person-count");
const phoneCountText = document.getElementById("phone-candidates");
const lookingAwayText = document.getElementById("looking-away-candidates");
const headDownText = document.getElementById("head-down-candidates");

let cameraStream = null;
let aiTimer = null;
let lastCaptureWidth = 640;
let lastCaptureHeight = 480;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setCameraStatus(message, label, className) {
  if (statusText) statusText.textContent = message;
  if (cameraBadge) {
    cameraBadge.textContent = label;
    cameraBadge.className = "status-pill " + className;
  }
}

function setFaceAIStatus(message, label, className) {
  if (recognitionStatus) recognitionStatus.textContent = message;
  if (faceAIBadge) {
    faceAIBadge.textContent = label;
    faceAIBadge.className = "status-pill " + className;
  }
}

function setBehaviorStatus(message, label, className) {
  if (behaviorStatus) behaviorStatus.textContent = message;
  if (behaviorBadge) {
    behaviorBadge.textContent = label;
    behaviorBadge.className = "status-pill " + className;
  }
}

function setAIButtonsEnabled(enabled) {
  if (analyzeOnceButton) analyzeOnceButton.disabled = !enabled;
  if (startAIButton) startAIButton.disabled = !enabled;
}

function resizeOverlay() {
  if (!overlay || !video) return;
  overlay.width = video.clientWidth;
  overlay.height = video.clientHeight;
}

function clearOverlay() {
  if (!overlay) return;
  const ctx = overlay.getContext("2d");
  ctx.clearRect(0, 0, overlay.width, overlay.height);
}

function drawBox(ctx, box, label, color, scaleX, scaleY, lineWidth) {
  const x = box.x * scaleX;
  const y = box.y * scaleY;
  const w = box.w * scaleX;
  const h = box.h * scaleY;

  ctx.lineWidth = lineWidth;
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.strokeRect(x, y, w, h);

  ctx.font = "16px Arial";
  const textWidth = ctx.measureText(label).width + 16;
  ctx.fillRect(x, Math.max(0, y - 28), textWidth, 26);

  ctx.fillStyle = "#ffffff";
  ctx.fillText(label, x + 8, Math.max(18, y - 9));
}

function drawDetections(recognitions, behavior) {
  if (!overlay || !video) return;

  resizeOverlay();
  const ctx = overlay.getContext("2d");
  ctx.clearRect(0, 0, overlay.width, overlay.height);

  const scaleX = overlay.width / lastCaptureWidth;
  const scaleY = overlay.height / lastCaptureHeight;

  const persons = behavior?.person_candidates || [];
  persons.forEach((box, index) => {
    drawBox(ctx, box, `Person ${index + 1}`, "#3b82f6", scaleX, scaleY, 2);
  });

  recognitions.forEach((item) => {
    if (!item.box) return;

    const label = item.recognized
      ? `${item.student_display_name || item.student_name || item.student_code} ${item.confidence}%`
      : `Unknown ${item.confidence}%`;

    const color = item.recognized ? "#10b981" : "#f59e0b";
    drawBox(ctx, item.box, label, color, scaleX, scaleY, 4);
  });
}

function captureFrameAsDataUrl() {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;

  lastCaptureWidth = canvas.width;
  lastCaptureHeight = canvas.height;

  const context = canvas.getContext("2d");
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  return canvas.toDataURL("image/jpeg", 0.92);
}

function updateBehaviorUI(behavior) {
  if (!behavior) return;

  if (personCountText) personCountText.textContent = behavior.person_count ?? 0;
  if (phoneCountText) phoneCountText.textContent = behavior.phone_candidates ?? 0;
  if (lookingAwayText) lookingAwayText.textContent = behavior.looking_away_candidates ?? 0;
  if (headDownText) headDownText.textContent = behavior.head_down_candidates ?? 0;

  setBehaviorStatus(
    behavior.summary || "Behavior frame analyzed.",
    "Behavior Running",
    "status-success"
  );
}

function renderRecognitionResult(result) {
  const recognition = result.recognition || {};
  const recognitions = recognition.recognitions || [];
  const attendanceResults = result.attendance_results || [];
  const behavior = result.behavior || {};

  drawDetections(recognitions, behavior);
  updateBehaviorUI(behavior);

  if (!recognitionList) return;

  if (!result.ok) {
    recognitionList.innerHTML = `<div class="note-box status-danger">${escapeHtml(result.message)}</div>`;
    return;
  }

  if (recognitions.length === 0) {
    recognitionList.innerHTML = `<div class="note-box">No face recognized in this frame.</div>`;
    return;
  }

  let html = "";

  recognitions.forEach((item, index) => {
    const attendance = attendanceResults[index] || {};
    const studentCode = item.student_display_name || item.student_name || item.student_code || "Unknown";
    const knownText = item.recognized ? "Recognized" : "Unknown";
    const pillClass = item.recognized ? "status-success" : "status-warning";

    let attendanceMessage = "No attendance recorded.";
    if (attendance.ok && attendance.student_name) {
      attendanceMessage = `${attendance.student_code} - ${attendance.student_name}: ${attendance.status}`;
      if (attendance.duplicate) attendanceMessage += " (duplicate skipped)";
    } else if (attendance.message) {
      attendanceMessage = attendance.message;
    }

    html += `
      <div class="recognition-card">
        <div>
          <strong>${escapeHtml(studentCode)}</strong>
          <span class="status-pill ${pillClass}">${knownText}</span>
        </div>
        <p>Confidence: ${escapeHtml(item.confidence)} | Distance: ${escapeHtml(item.distance)} | Threshold: ${escapeHtml(item.threshold)}</p>
        <p>${escapeHtml(attendanceMessage)}</p>
      </div>
    `;
  });

  recognitionList.innerHTML = html;
}

async function analyzeFrame() {
  if (!cameraStream) {
    setFaceAIStatus("Start camera first.", "Camera Needed", "status-warning");
    return;
  }

  try {
    setFaceAIStatus("Analyzing current frame...", "Analyzing", "status-info");

    const imageData = captureFrameAsDataUrl();
    const formData = new FormData();
    formData.append("image_data", imageData);

    const response = await fetch("/ai-monitoring/analyze-frame", {
      method: "POST",
      body: formData,
    });

    const text = await response.text();
    let result;

    try {
      result = JSON.parse(text);
    } catch (parseError) {
      throw new Error("Backend did not return JSON: " + text.slice(0, 200));
    }

    renderRecognitionResult(result);

    if (!result.ok) {
      setFaceAIStatus(result.message || "Analysis failed.", "Not Ready", "status-warning");
      return;
    }

    const recognizedCount = result.recognition?.recognized_count || 0;
    const personCount = result.behavior?.person_count || 0;

    setFaceAIStatus(
      `Recognized: ${recognizedCount}, Persons: ${personCount}`,
      "AI Running",
      "status-success"
    );
  } catch (error) {
    console.error("AI analysis failed:", error);
    setFaceAIStatus("AI analysis failed: " + (error.message || error.name), "Error", "status-danger");
  }
}

function startAIAnalysis() {
  if (aiTimer) return;

  analyzeFrame();
  aiTimer = setInterval(analyzeFrame, 2000);

  if (startAIButton) startAIButton.disabled = true;
  if (stopAIButton) stopAIButton.disabled = false;

  setFaceAIStatus("AI attendance and behavior monitoring are running.", "AI Running", "status-success");
}

function stopAIAnalysis() {
  if (aiTimer) {
    clearInterval(aiTimer);
    aiTimer = null;
  }

  if (startAIButton) startAIButton.disabled = false;
  if (stopAIButton) stopAIButton.disabled = true;

  setFaceAIStatus("AI analysis stopped.", "Stopped", "status-muted");
}

if (startButton && stopButton && video) {
  startButton.addEventListener("click", async () => {
    try {
      setCameraStatus("Requesting camera permission...", "Starting", "status-info");

      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });

      video.muted = true;
      video.playsInline = true;
      video.srcObject = cameraStream;
      await video.play();

      resizeOverlay();

      startButton.disabled = true;
      stopButton.disabled = false;
      setAIButtonsEnabled(true);

      if (cameraFrame) cameraFrame.classList.add("camera-active");

      setCameraStatus("Camera is running from this computer.", "Running", "status-success");
      setBehaviorStatus(
        "Camera is ready. AI can analyze attendance and behavior candidates now.",
        "Ready",
        "status-info"
      );
    } catch (error) {
      console.error("Camera start failed:", error);
      setCameraStatus("Camera failed: " + (error.name || error.message), "Error", "status-danger");
      setBehaviorStatus("Camera failed, so AI cannot analyze frames yet.", "Error", "status-danger");
    }
  });

  stopButton.addEventListener("click", () => {
    stopAIAnalysis();

    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      cameraStream = null;
    }

    video.srcObject = null;
    startButton.disabled = false;
    stopButton.disabled = true;
    setAIButtonsEnabled(false);
    clearOverlay();

    if (cameraFrame) cameraFrame.classList.remove("camera-active");

    setCameraStatus("Camera stopped. Click Start Camera.", "Stopped", "status-muted");
    setBehaviorStatus("Behavior AI stopped.", "AI Not Started", "status-warning");
  });
}

window.addEventListener("resize", resizeOverlay);

if (analyzeOnceButton) analyzeOnceButton.addEventListener("click", analyzeFrame);
if (startAIButton) startAIButton.addEventListener("click", startAIAnalysis);
if (stopAIButton) stopAIButton.addEventListener("click", stopAIAnalysis);


// ================================
// Stage 9 Video Evidence Recording
// ================================

const startRecordingButton = document.getElementById("start-recording");
const stopRecordingButton = document.getElementById("stop-recording");
const saveRecordingButton = document.getElementById("save-recording");
const recordingBadge = document.getElementById("recording-badge");
const recordingMessage = document.getElementById("recording-message");
const recordingEventType = document.getElementById("recording-event-type");
const recordingNote = document.getElementById("recording-note");

let mediaRecorder = null;
let recordedChunks = [];
let recordedBlob = null;
let recordingStartedAt = null;
let recordingDurationSeconds = 0;

function setRecordingStatus(message, label, className) {
  if (recordingMessage) recordingMessage.textContent = message;
  if (recordingBadge) {
    recordingBadge.textContent = label;
    recordingBadge.className = "status-pill " + className;
  }
}

function setRecordingButtons(state) {
  if (!startRecordingButton || !stopRecordingButton || !saveRecordingButton) return;

  if (state === "ready") {
    startRecordingButton.disabled = !cameraStream;
    stopRecordingButton.disabled = true;
    saveRecordingButton.disabled = !recordedBlob;
  } else if (state === "recording") {
    startRecordingButton.disabled = true;
    stopRecordingButton.disabled = false;
    saveRecordingButton.disabled = true;
  } else if (state === "recorded") {
    startRecordingButton.disabled = false;
    stopRecordingButton.disabled = true;
    saveRecordingButton.disabled = false;
  } else {
    startRecordingButton.disabled = true;
    stopRecordingButton.disabled = true;
    saveRecordingButton.disabled = true;
  }
}

function getSupportedMimeType() {
  const types = [
    "video/webm;codecs=vp9",
    "video/webm;codecs=vp8",
    "video/webm",
  ];

  for (const type of types) {
    if (window.MediaRecorder && MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }

  return "";
}

function startVideoRecording() {
  if (!cameraStream) {
    setRecordingStatus("Start camera first before recording.", "Camera Needed", "status-warning");
    return;
  }

  if (!window.MediaRecorder) {
    setRecordingStatus("MediaRecorder is not supported in this browser.", "Not Supported", "status-danger");
    return;
  }

  recordedChunks = [];
  recordedBlob = null;
  recordingDurationSeconds = 0;
  recordingStartedAt = Date.now();

  const mimeType = getSupportedMimeType();
  const options = mimeType ? { mimeType } : {};

  mediaRecorder = new MediaRecorder(cameraStream, options);

  mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) {
      recordedChunks.push(event.data);
    }
  };

  mediaRecorder.onstop = () => {
    const finalMimeType = mediaRecorder.mimeType || "video/webm";
    recordedBlob = new Blob(recordedChunks, { type: finalMimeType });
    recordingDurationSeconds = recordingStartedAt
      ? (Date.now() - recordingStartedAt) / 1000
      : 0;

    setRecordingStatus(
      `Recording stopped. Clip length: ${recordingDurationSeconds.toFixed(1)}s. Click Save Clip.`,
      "Clip Ready",
      "status-info"
    );
    setRecordingButtons("recorded");
  };

  mediaRecorder.start();
  setRecordingStatus("Recording video evidence...", "Recording", "status-danger");
  setRecordingButtons("recording");
}

function stopVideoRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
}

async function saveVideoRecording() {
  if (!recordedBlob) {
    setRecordingStatus("No recorded clip to save.", "No Clip", "status-warning");
    return;
  }

  const formData = new FormData();
  formData.append("video_file", recordedBlob, "ai_monitoring_clip.webm");
  formData.append("event_type", recordingEventType?.value || "manual_clip");
  formData.append("note", recordingNote?.value || "");
  formData.append("duration_seconds", recordingDurationSeconds.toFixed(2));

  try {
    setRecordingStatus("Saving video evidence into active session...", "Saving", "status-info");
    if (saveRecordingButton) saveRecordingButton.disabled = true;

    const response = await fetch("/video-records/upload", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (!result.ok) {
      throw new Error(result.message || "Save failed.");
    }

    recordedBlob = null;
    recordedChunks = [];

    setRecordingStatus("Video evidence saved successfully. Open Video Records to review.", "Saved", "status-success");
    setRecordingButtons("ready");
  } catch (error) {
    console.error("Video save failed:", error);
    setRecordingStatus("Video save failed: " + (error.message || error.name), "Error", "status-danger");
    setRecordingButtons("recorded");
  }
}

if (startRecordingButton) {
  startRecordingButton.addEventListener("click", startVideoRecording);
}
if (stopRecordingButton) {
  stopRecordingButton.addEventListener("click", stopVideoRecording);
}
if (saveRecordingButton) {
  saveRecordingButton.addEventListener("click", saveVideoRecording);
}

// Enable recording button after camera starts.
if (startButton) {
  startButton.addEventListener("click", () => {
    setTimeout(() => {
      if (cameraStream) {
        setRecordingButtons("ready");
        setRecordingStatus("Camera ready. You can record a short evidence clip.", "Ready", "status-info");
      }
    }, 700);
  });
}

if (stopButton) {
  stopButton.addEventListener("click", () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      stopVideoRecording();
    }
    setRecordingButtons("disabled");
    setRecordingStatus("Camera stopped. Start camera to record video evidence.", "Not Recording", "status-muted");
  });
}


// ================================
// Stage 9.4 Record AI View With Boxes
// Overrides previous raw-camera recording
// ================================

let evidenceCanvas = null;
let evidenceContext = null;
let evidenceAnimationFrame = null;
let evidenceStream = null;

function stopEvidenceCanvasLoop() {
  if (evidenceAnimationFrame) {
    cancelAnimationFrame(evidenceAnimationFrame);
    evidenceAnimationFrame = null;
  }

  if (evidenceStream) {
    evidenceStream.getTracks().forEach((track) => track.stop());
    evidenceStream = null;
  }
}

function drawEvidenceFrame() {
  if (!cameraStream || !video) return;

  const width = video.videoWidth || lastCaptureWidth || 640;
  const height = video.videoHeight || lastCaptureHeight || 480;

  if (!evidenceCanvas) {
    evidenceCanvas = document.createElement("canvas");
    evidenceContext = evidenceCanvas.getContext("2d");
  }

  if (evidenceCanvas.width !== width || evidenceCanvas.height !== height) {
    evidenceCanvas.width = width;
    evidenceCanvas.height = height;
  }

  evidenceContext.clearRect(0, 0, width, height);
  evidenceContext.drawImage(video, 0, 0, width, height);

  // Draw the AI overlay frame boxes into the recorded video.
  if (overlay) {
    evidenceContext.drawImage(overlay, 0, 0, width, height);
  }

  // Small recording label for teacher evidence context.
  evidenceContext.fillStyle = "rgba(15, 23, 42, 0.72)";
  evidenceContext.fillRect(14, 14, 230, 34);
  evidenceContext.fillStyle = "#ffffff";
  evidenceContext.font = "16px Arial";
  evidenceContext.fillText("AI Monitoring Evidence", 26, 37);

  evidenceAnimationFrame = requestAnimationFrame(drawEvidenceFrame);
}

function startVideoRecording() {
  if (!cameraStream) {
    setRecordingStatus("Start camera first before recording.", "Camera Needed", "status-warning");
    return;
  }

  if (!window.MediaRecorder) {
    setRecordingStatus("MediaRecorder is not supported in this browser.", "Not Supported", "status-danger");
    return;
  }

  recordedChunks = [];
  recordedBlob = null;
  recordingDurationSeconds = 0;
  recordingStartedAt = Date.now();

  stopEvidenceCanvasLoop();
  drawEvidenceFrame();

  if (!evidenceCanvas || !evidenceCanvas.captureStream) {
    setRecordingStatus("Canvas recording is not supported in this browser.", "Not Supported", "status-danger");
    return;
  }

  evidenceStream = evidenceCanvas.captureStream(24);

  const mimeType = getSupportedMimeType();
  const options = mimeType ? { mimeType } : {};

  mediaRecorder = new MediaRecorder(evidenceStream, options);

  mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) {
      recordedChunks.push(event.data);
    }
  };

  mediaRecorder.onstop = () => {
    const finalMimeType = mediaRecorder.mimeType || "video/webm";
    recordedBlob = new Blob(recordedChunks, { type: finalMimeType });
    recordingDurationSeconds = recordingStartedAt
      ? (Date.now() - recordingStartedAt) / 1000
      : 0;

    stopEvidenceCanvasLoop();

    setRecordingStatus(
      `AI monitoring clip ready: ${recordingDurationSeconds.toFixed(1)}s. Click Save Clip.`,
      "Clip Ready",
      "status-info"
    );
    setRecordingButtons("recorded");
  };

  mediaRecorder.start();
  setRecordingStatus("Recording AI view with frame boxes...", "Recording", "status-danger");
  setRecordingButtons("recording");
}

function stopVideoRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  } else {
    stopEvidenceCanvasLoop();
  }
}

async function saveVideoRecording() {
  if (!recordedBlob) {
    setRecordingStatus("No recorded clip to save.", "No Clip", "status-warning");
    return;
  }

  const formData = new FormData();
  formData.append("video_file", recordedBlob, "ai_monitoring_evidence.webm");
  formData.append("event_type", "ai_monitoring_clip");
  formData.append("note", recordingNote?.value || "AI monitoring evidence clip with frame boxes.");
  formData.append("duration_seconds", recordingDurationSeconds.toFixed(2));

  try {
    setRecordingStatus("Saving AI monitoring clip into active session...", "Saving", "status-info");
    if (saveRecordingButton) saveRecordingButton.disabled = true;

    const response = await fetch("/video-records/upload", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (!result.ok) {
      throw new Error(result.message || "Save failed.");
    }

    recordedBlob = null;
    recordedChunks = [];

    setRecordingStatus("Video evidence saved with AI frame boxes. Open Video Records to review.", "Saved", "status-success");
    setRecordingButtons("ready");
  } catch (error) {
    console.error("Video save failed:", error);
    setRecordingStatus("Video save failed: " + (error.message || error.name), "Error", "status-danger");
    setRecordingButtons("recorded");
  }
}


// ================================
// Stage 9.5 Evidence Clip With Real AI Boxes
// Records video + direct AI detection boxes
// ================================

let latestRecognitionsForEvidence = [];
let latestBehaviorForEvidence = {};

// Override drawDetections so we always keep latest AI boxes for recording.
function drawDetections(recognitions, behavior) {
  latestRecognitionsForEvidence = Array.isArray(recognitions) ? recognitions : [];
  latestBehaviorForEvidence = behavior || {};

  if (!overlay || !video) return;

  resizeOverlay();
  const ctx = overlay.getContext("2d");
  ctx.clearRect(0, 0, overlay.width, overlay.height);

  const scaleX = overlay.width / lastCaptureWidth;
  const scaleY = overlay.height / lastCaptureHeight;

  const persons = latestBehaviorForEvidence?.person_candidates || [];
  persons.forEach((box, index) => {
    drawBox(ctx, box, `Person ${index + 1}`, "#3b82f6", scaleX, scaleY, 2);
  });

  latestRecognitionsForEvidence.forEach((item) => {
    if (!item.box) return;

    const label = item.recognized
      ? `${item.student_display_name || item.student_name || item.student_code} ${item.confidence}%`
      : `Unknown ${item.confidence}%`;

    const color = item.recognized ? "#10b981" : "#f59e0b";
    drawBox(ctx, item.box, label, color, scaleX, scaleY, 4);
  });
}

function drawEvidenceBox(ctx, box, label, color, scaleX, scaleY, lineWidth) {
  if (!box) return;

  const x = box.x * scaleX;
  const y = box.y * scaleY;
  const w = box.w * scaleX;
  const h = box.h * scaleY;

  ctx.lineWidth = lineWidth;
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.strokeRect(x, y, w, h);

  ctx.font = "18px Arial";
  const textWidth = ctx.measureText(label).width + 18;
  const labelY = Math.max(0, y - 32);

  ctx.fillRect(x, labelY, textWidth, 30);
  ctx.fillStyle = "#ffffff";
  ctx.fillText(label, x + 9, labelY + 21);
}

function drawEvidenceHeader(ctx, width, height) {
  const now = new Date().toLocaleString();

  ctx.fillStyle = "rgba(15, 23, 42, 0.78)";
  ctx.fillRect(14, 14, 420, 42);

  ctx.fillStyle = "#ef4444";
  ctx.beginPath();
  ctx.arc(34, 35, 7, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#ffffff";
  ctx.font = "18px Arial";
  ctx.fillText("AI Monitoring Evidence Clip", 50, 40);

  ctx.fillStyle = "rgba(15, 23, 42, 0.72)";
  ctx.fillRect(14, height - 50, Math.min(width - 28, 720), 36);

  ctx.fillStyle = "#ffffff";
  ctx.font = "15px Arial";
  ctx.fillText(`Recorded: ${now} | Green = recognized face | Blue = person candidate`, 28, height - 27);
}

function drawEvidenceFrame() {
  if (!cameraStream || !video) return;

  const width = video.videoWidth || lastCaptureWidth || 640;
  const height = video.videoHeight || lastCaptureHeight || 480;

  if (!evidenceCanvas) {
    evidenceCanvas = document.createElement("canvas");
    evidenceContext = evidenceCanvas.getContext("2d");
  }

  if (evidenceCanvas.width !== width || evidenceCanvas.height !== height) {
    evidenceCanvas.width = width;
    evidenceCanvas.height = height;
  }

  evidenceContext.clearRect(0, 0, width, height);
  evidenceContext.drawImage(video, 0, 0, width, height);

  const scaleX = width / (lastCaptureWidth || width);
  const scaleY = height / (lastCaptureHeight || height);

  const persons = latestBehaviorForEvidence?.person_candidates || [];
  persons.forEach((box, index) => {
    drawEvidenceBox(evidenceContext, box, `Person ${index + 1}`, "#3b82f6", scaleX, scaleY, 3);
  });

  latestRecognitionsForEvidence.forEach((item) => {
    if (!item.box) return;

    const label = item.recognized
      ? `${item.student_display_name || item.student_name || item.student_code} ${item.confidence}%`
      : `Unknown ${item.confidence}%`;

    const color = item.recognized ? "#10b981" : "#f59e0b";
    drawEvidenceBox(evidenceContext, item.box, label, color, scaleX, scaleY, 5);
  });

  if (latestRecognitionsForEvidence.length === 0 && persons.length === 0) {
    evidenceContext.fillStyle = "rgba(245, 158, 11, 0.92)";
    evidenceContext.fillRect(14, 66, 420, 34);
    evidenceContext.fillStyle = "#111827";
    evidenceContext.font = "15px Arial";
    evidenceContext.fillText("No AI boxes yet ? keep AI Monitoring running.", 28, 88);
  }

  drawEvidenceHeader(evidenceContext, width, height);

  evidenceAnimationFrame = requestAnimationFrame(drawEvidenceFrame);
}

// Override recording start: auto-run AI + record composed canvas.
function startVideoRecording() {
  if (!cameraStream) {
    setRecordingStatus("Start camera first before recording.", "Camera Needed", "status-warning");
    return;
  }

  if (!window.MediaRecorder) {
    setRecordingStatus("MediaRecorder is not supported in this browser.", "Not Supported", "status-danger");
    return;
  }

  // Important: auto-start AI so frame boxes appear in the saved evidence clip.
  if (!aiTimer) {
    startAIAnalysis();
  }

  recordedChunks = [];
  recordedBlob = null;
  recordingDurationSeconds = 0;
  recordingStartedAt = Date.now();

  stopEvidenceCanvasLoop();
  drawEvidenceFrame();

  if (!evidenceCanvas || !evidenceCanvas.captureStream) {
    setRecordingStatus("Canvas recording is not supported in this browser.", "Not Supported", "status-danger");
    return;
  }

  evidenceStream = evidenceCanvas.captureStream(24);

  const mimeType = getSupportedMimeType();
  const options = mimeType ? { mimeType } : {};

  mediaRecorder = new MediaRecorder(evidenceStream, options);

  mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) {
      recordedChunks.push(event.data);
    }
  };

  mediaRecorder.onstop = () => {
    const finalMimeType = mediaRecorder.mimeType || "video/webm";
    recordedBlob = new Blob(recordedChunks, { type: finalMimeType });
    recordingDurationSeconds = recordingStartedAt
      ? (Date.now() - recordingStartedAt) / 1000
      : 0;

    stopEvidenceCanvasLoop();

    setRecordingStatus(
      `AI evidence clip ready: ${recordingDurationSeconds.toFixed(1)}s. Click Save Clip.`,
      "Clip Ready",
      "status-info"
    );
    setRecordingButtons("recorded");
  };

  mediaRecorder.start();
  setRecordingStatus("Recording camera + AI frame boxes...", "Recording", "status-danger");
  setRecordingButtons("recording");
}

async function saveVideoRecording() {
  if (!recordedBlob) {
    setRecordingStatus("No recorded clip to save.", "No Clip", "status-warning");
    return;
  }

  const formData = new FormData();
  formData.append("video_file", recordedBlob, "ai_monitoring_with_boxes.webm");
  formData.append("event_type", "ai_monitoring_clip");
  formData.append("note", recordingNote?.value || "AI monitoring evidence clip with face/person frame boxes.");
  formData.append("duration_seconds", recordingDurationSeconds.toFixed(2));

  try {
    setRecordingStatus("Saving AI evidence clip into active session...", "Saving", "status-info");
    if (saveRecordingButton) saveRecordingButton.disabled = true;

    const response = await fetch("/video-records/upload", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (!result.ok) {
      throw new Error(result.message || "Save failed.");
    }

    recordedBlob = null;
    recordedChunks = [];

    setRecordingStatus("Saved. Video Records now contains camera + AI frame boxes.", "Saved", "status-success");
    setRecordingButtons("ready");
  } catch (error) {
    console.error("Video save failed:", error);
    setRecordingStatus("Video save failed: " + (error.message || error.name), "Error", "status-danger");
    setRecordingButtons("recorded");
  }
}


// ================================
// Stage 11 Behavior Alert Color Boxes
// Final override: red alert, amber warning, green normal, yellow unknown
// ================================

function boxCenterForAlert(box) {
  return {
    x: (box?.x || 0) + (box?.w || 0) / 2,
    y: (box?.y || 0) + (box?.h || 0) / 2,
  };
}

function pointInsideBoxForAlert(point, box) {
  if (!point || !box) return false;
  return (
    point.x >= box.x &&
    point.x <= box.x + box.w &&
    point.y >= box.y &&
    point.y <= box.y + box.h
  );
}

function alertForRecognition(item, behavior) {
  const alerts = behavior?.alert_candidates || [];
  if (!item?.box) return null;

  const center = boxCenterForAlert(item.box);

  return alerts.find((alert) => {
    if (alert.student_code && item.student_code && alert.student_code === item.student_code) {
      return true;
    }
    return pointInsideBoxForAlert(center, alert.box);
  });
}

function updateBehaviorUI(behavior) {
  if (!behavior) return;

  const alertCount = (behavior.alert_candidates || []).length;
  const warningCount = (behavior.warning_candidates || []).length;

  if (personCountText) personCountText.textContent = behavior.person_count ?? 0;
  if (phoneCountText) phoneCountText.textContent = behavior.phone_candidates ?? 0;
  if (lookingAwayText) lookingAwayText.textContent = behavior.looking_away_candidates ?? 0;
  if (headDownText) headDownText.textContent = behavior.head_down_candidates ?? 0;

  let message = behavior.summary || "Behavior frame analyzed.";
  let label = "Behavior Running";
  let className = "status-success";

  if (alertCount > 0) {
    message = `${message}. ${alertCount} alert candidate(s) saved to Behavior Reports with snapshot.`;
    label = "Alert";
    className = "status-danger";
  } else if (warningCount > 0) {
    message = `${message}. ${warningCount} warning candidate(s) found.`;
    label = "Warning";
    className = "status-warning";
  }

  setBehaviorStatus(message, label, className);
}

function drawDetections(recognitions, behavior) {
  latestRecognitionsForEvidence = Array.isArray(recognitions) ? recognitions : [];
  latestBehaviorForEvidence = behavior || {};

  if (!overlay || !video) return;

  resizeOverlay();
  const ctx = overlay.getContext("2d");
  ctx.clearRect(0, 0, overlay.width, overlay.height);

  const scaleX = overlay.width / lastCaptureWidth;
  const scaleY = overlay.height / lastCaptureHeight;

  const persons = latestBehaviorForEvidence?.person_candidates || [];
  persons.forEach((box, index) => {
    drawBox(ctx, box, `Person ${index + 1}`, "#3b82f6", scaleX, scaleY, 2);
  });

  const warnings = latestBehaviorForEvidence?.warning_candidates || [];
  warnings.forEach((item) => {
    if (!item.box) return;
    drawBox(ctx, item.box, item.label || "Warning", "#f59e0b", scaleX, scaleY, 3);
  });

  const alerts = latestBehaviorForEvidence?.alert_candidates || [];
  alerts.forEach((item) => {
    if (!item.box) return;
    const alertName = item.student_name || "Student";
    drawBox(ctx, item.box, `${alertName} | ${item.label || "Alert"}`, "#ef4444", scaleX, scaleY, 5);
  });

  const phoneBoxes = latestBehaviorForEvidence?.phone_candidate_boxes || [];
  phoneBoxes.forEach((box) => {
    drawBox(ctx, box, "Phone/Object", "#ef4444", scaleX, scaleY, 3);
  });

  latestRecognitionsForEvidence.forEach((item) => {
    if (!item.box) return;

    const alert = alertForRecognition(item, latestBehaviorForEvidence);
    const displayName = item.student_display_name || item.student_name || item.student_code || "Unknown";

    let label = item.recognized
      ? `${displayName} ${item.confidence}%`
      : `Unknown ${item.confidence}%`;

    let color = item.recognized ? "#10b981" : "#f59e0b";
    let lineWidth = item.recognized ? 4 : 3;

    if (alert) {
      label = `${displayName} | ${alert.label || "Alert"}`;
      color = "#ef4444";
      lineWidth = 6;
    }

    drawBox(ctx, item.box, label, color, scaleX, scaleY, lineWidth);
  });
}

function drawEvidenceFrame() {
  if (!cameraStream || !video) return;

  const width = video.videoWidth || lastCaptureWidth || 640;
  const height = video.videoHeight || lastCaptureHeight || 480;

  if (!evidenceCanvas) {
    evidenceCanvas = document.createElement("canvas");
    evidenceContext = evidenceCanvas.getContext("2d");
  }

  if (evidenceCanvas.width !== width || evidenceCanvas.height !== height) {
    evidenceCanvas.width = width;
    evidenceCanvas.height = height;
  }

  evidenceContext.clearRect(0, 0, width, height);
  evidenceContext.drawImage(video, 0, 0, width, height);

  const scaleX = width / (lastCaptureWidth || width);
  const scaleY = height / (lastCaptureHeight || height);

  const persons = latestBehaviorForEvidence?.person_candidates || [];
  persons.forEach((box, index) => {
    drawEvidenceBox(evidenceContext, box, `Person ${index + 1}`, "#3b82f6", scaleX, scaleY, 3);
  });

  const warnings = latestBehaviorForEvidence?.warning_candidates || [];
  warnings.forEach((item) => {
    if (!item.box) return;
    drawEvidenceBox(evidenceContext, item.box, item.label || "Warning", "#f59e0b", scaleX, scaleY, 3);
  });

  const alerts = latestBehaviorForEvidence?.alert_candidates || [];
  alerts.forEach((item) => {
    if (!item.box) return;
    const alertName = item.student_name || "Student";
    drawEvidenceBox(evidenceContext, item.box, `${alertName} | ${item.label || "Alert"}`, "#ef4444", scaleX, scaleY, 6);
  });

  const phoneBoxes = latestBehaviorForEvidence?.phone_candidate_boxes || [];
  phoneBoxes.forEach((box) => {
    drawEvidenceBox(evidenceContext, box, "Phone/Object", "#ef4444", scaleX, scaleY, 3);
  });

  latestRecognitionsForEvidence.forEach((item) => {
    if (!item.box) return;

    const alert = alertForRecognition(item, latestBehaviorForEvidence);
    const displayName = item.student_display_name || item.student_name || item.student_code || "Unknown";

    let label = item.recognized
      ? `${displayName} ${item.confidence}%`
      : `Unknown ${item.confidence}%`;

    let color = item.recognized ? "#10b981" : "#f59e0b";
    let lineWidth = item.recognized ? 4 : 3;

    if (alert) {
      label = `${displayName} | ${alert.label || "Alert"}`;
      color = "#ef4444";
      lineWidth = 6;
    }

    drawEvidenceBox(evidenceContext, item.box, label, color, scaleX, scaleY, lineWidth);
  });

  if (latestRecognitionsForEvidence.length === 0 && persons.length === 0) {
    evidenceContext.fillStyle = "rgba(245, 158, 11, 0.92)";
    evidenceContext.fillRect(14, 66, 420, 34);
    evidenceContext.fillStyle = "#111827";
    evidenceContext.font = "15px Arial";
    evidenceContext.fillText("No AI boxes yet ? keep AI Monitoring running.", 28, 88);
  }

  drawEvidenceHeader(evidenceContext, width, height);

  evidenceAnimationFrame = requestAnimationFrame(drawEvidenceFrame);
}


// ================================
// Stage 11.4 Accuracy Tuning Drawing Override
// Cleaner labels + safer low-confidence display
// ================================

function drawDetections(recognitions, behavior) {
  latestRecognitionsForEvidence = Array.isArray(recognitions) ? recognitions : [];
  latestBehaviorForEvidence = behavior || {};

  if (!overlay || !video) return;

  resizeOverlay();
  const ctx = overlay.getContext("2d");
  ctx.clearRect(0, 0, overlay.width, overlay.height);

  const scaleX = overlay.width / lastCaptureWidth;
  const scaleY = overlay.height / lastCaptureHeight;

  const persons = latestBehaviorForEvidence?.person_candidates || [];
  const alerts = latestBehaviorForEvidence?.alert_candidates || [];
  const warnings = latestBehaviorForEvidence?.warning_candidates || [];
  const phoneBoxes = latestBehaviorForEvidence?.phone_candidate_boxes || [];

  persons.forEach((box, index) => {
    const hasAlert = alerts.some((alert) => alert.box && pointInsideBoxForAlert(boxCenterForAlert(box), alert.box));
    if (!hasAlert) {
      drawBox(ctx, box, `Person ${index + 1}`, "#3b82f6", scaleX, scaleY, 2);
    }
  });

  warnings.forEach((item) => {
    if (!item.box) return;
    drawBox(ctx, item.box, item.label || "Warning", "#f59e0b", scaleX, scaleY, 3);
  });

  // Draw only object box for phone candidate. Student red box is drawn by recognition if matched.
  phoneBoxes.forEach((box) => {
    drawBox(ctx, box, "Phone/Object Candidate", "#ef4444", scaleX, scaleY, 3);
  });

  latestRecognitionsForEvidence.forEach((item) => {
    if (!item.box) return;

    const alert = alertForRecognition(item, latestBehaviorForEvidence);
    const displayName = item.student_display_name || item.student_name || item.student_code || "Unknown";

    let label = item.recognized
      ? `${displayName} ${item.confidence}%`
      : `Unknown ${item.confidence || ""}%`;

    let color = item.recognized ? "#10b981" : "#f59e0b";
    let lineWidth = item.recognized ? 4 : 3;

    if (item.low_confidence && item.predicted_student_code && !item.recognized) {
      label = `Low confidence face ${item.confidence}%`;
      color = "#f59e0b";
      lineWidth = 3;
    }

    if (alert && item.recognized) {
      label = `${displayName} | ${alert.label || "Alert"}`;
      color = "#ef4444";
      lineWidth = 6;
    }

    drawBox(ctx, item.box, label, color, scaleX, scaleY, lineWidth);
  });

  // If alert cannot match a recognized student, show generic red person alert.
  alerts.forEach((alert) => {
    const matched = latestRecognitionsForEvidence.some((item) => item.recognized && alertForRecognition(item, latestBehaviorForEvidence));
    if (!matched && alert.box) {
      drawBox(ctx, alert.box, alert.label || "Alert Candidate", "#ef4444", scaleX, scaleY, 5);
    }
  });
}

function drawEvidenceFrame() {
  if (!cameraStream || !video) return;

  const width = video.videoWidth || lastCaptureWidth || 640;
  const height = video.videoHeight || lastCaptureHeight || 480;

  if (!evidenceCanvas) {
    evidenceCanvas = document.createElement("canvas");
    evidenceContext = evidenceCanvas.getContext("2d");
  }

  if (evidenceCanvas.width !== width || evidenceCanvas.height !== height) {
    evidenceCanvas.width = width;
    evidenceCanvas.height = height;
  }

  evidenceContext.clearRect(0, 0, width, height);
  evidenceContext.drawImage(video, 0, 0, width, height);

  const scaleX = width / (lastCaptureWidth || width);
  const scaleY = height / (lastCaptureHeight || height);

  const persons = latestBehaviorForEvidence?.person_candidates || [];
  const alerts = latestBehaviorForEvidence?.alert_candidates || [];
  const warnings = latestBehaviorForEvidence?.warning_candidates || [];
  const phoneBoxes = latestBehaviorForEvidence?.phone_candidate_boxes || [];

  persons.forEach((box, index) => {
    const hasAlert = alerts.some((alert) => alert.box && pointInsideBoxForAlert(boxCenterForAlert(box), alert.box));
    if (!hasAlert) {
      drawEvidenceBox(evidenceContext, box, `Person ${index + 1}`, "#3b82f6", scaleX, scaleY, 3);
    }
  });

  warnings.forEach((item) => {
    if (!item.box) return;
    drawEvidenceBox(evidenceContext, item.box, item.label || "Warning", "#f59e0b", scaleX, scaleY, 3);
  });

  phoneBoxes.forEach((box) => {
    drawEvidenceBox(evidenceContext, box, "Phone/Object Candidate", "#ef4444", scaleX, scaleY, 3);
  });

  latestRecognitionsForEvidence.forEach((item) => {
    if (!item.box) return;

    const alert = alertForRecognition(item, latestBehaviorForEvidence);
    const displayName = item.student_display_name || item.student_name || item.student_code || "Unknown";

    let label = item.recognized
      ? `${displayName} ${item.confidence}%`
      : `Unknown ${item.confidence || ""}%`;

    let color = item.recognized ? "#10b981" : "#f59e0b";
    let lineWidth = item.recognized ? 4 : 3;

    if (item.low_confidence && item.predicted_student_code && !item.recognized) {
      label = `Low confidence face ${item.confidence}%`;
      color = "#f59e0b";
      lineWidth = 3;
    }

    if (alert && item.recognized) {
      label = `${displayName} | ${alert.label || "Alert"}`;
      color = "#ef4444";
      lineWidth = 6;
    }

    drawEvidenceBox(evidenceContext, item.box, label, color, scaleX, scaleY, lineWidth);
  });

  alerts.forEach((alert) => {
    const matched = latestRecognitionsForEvidence.some((item) => item.recognized && alertForRecognition(item, latestBehaviorForEvidence));
    if (!matched && alert.box) {
      drawEvidenceBox(evidenceContext, alert.box, alert.label || "Alert Candidate", "#ef4444", scaleX, scaleY, 5);
    }
  });

  if (latestRecognitionsForEvidence.length === 0 && persons.length === 0) {
    evidenceContext.fillStyle = "rgba(245, 158, 11, 0.92)";
    evidenceContext.fillRect(14, 66, 420, 34);
    evidenceContext.fillStyle = "#111827";
    evidenceContext.font = "15px Arial";
    evidenceContext.fillText("No AI boxes yet ? keep AI Monitoring running.", 28, 88);
  }

  drawEvidenceHeader(evidenceContext, width, height);

  evidenceAnimationFrame = requestAnimationFrame(drawEvidenceFrame);
}


// ================================
// Stage 11.5 Final Accuracy Drawing Override
// Hide weak unknown noise + clean phone alert label
// ================================

function drawDetections(recognitions, behavior) {
  latestRecognitionsForEvidence = Array.isArray(recognitions) ? recognitions : [];
  latestBehaviorForEvidence = behavior || {};

  if (!overlay || !video) return;

  resizeOverlay();
  const ctx = overlay.getContext("2d");
  ctx.clearRect(0, 0, overlay.width, overlay.height);

  const scaleX = overlay.width / lastCaptureWidth;
  const scaleY = overlay.height / lastCaptureHeight;

  const persons = latestBehaviorForEvidence?.person_candidates || [];
  const alerts = latestBehaviorForEvidence?.alert_candidates || [];
  const phoneBoxes = latestBehaviorForEvidence?.phone_candidate_boxes || [];

  persons.forEach((box, index) => {
    const hasAlert = alerts.some((alert) => alert.box && pointInsideBoxForAlert(boxCenterForAlert(box), alert.box));
    if (!hasAlert) {
      drawBox(ctx, box, `Person ${index + 1}`, "#3b82f6", scaleX, scaleY, 2);
    }
  });

  phoneBoxes.forEach((box) => {
    drawBox(ctx, box, `Phone Candidate ${box.confidence || ""}%`, "#ef4444", scaleX, scaleY, 3);
  });

  latestRecognitionsForEvidence.forEach((item) => {
    if (!item.box) return;

    // Hide very weak unknown face noise.
    if (!item.recognized && (item.confidence || 0) < 42) {
      return;
    }

    const alert = alertForRecognition(item, latestBehaviorForEvidence);
    const displayName = item.student_display_name || item.student_name || item.student_code || "Unknown";

    let label = item.recognized
      ? `${displayName} ${item.confidence}%`
      : `Unknown Face ${item.confidence || ""}%`;

    let color = item.recognized ? "#10b981" : "#f59e0b";
    let lineWidth = item.recognized ? 4 : 3;

    if (item.low_confidence && item.predicted_student_code && !item.recognized) {
      label = `Low Confidence ${item.confidence}%`;
      color = "#f59e0b";
      lineWidth = 3;
    }

    if (alert && item.recognized) {
      label = `${displayName} | Phone-use Alert`;
      color = "#ef4444";
      lineWidth = 6;
    }

    drawBox(ctx, item.box, label, color, scaleX, scaleY, lineWidth);
  });

  alerts.forEach((alert) => {
    const matched = latestRecognitionsForEvidence.some((item) => item.recognized && alertForRecognition(item, latestBehaviorForEvidence));
    if (!matched && alert.box) {
      drawBox(ctx, alert.box, "Phone-use Alert", "#ef4444", scaleX, scaleY, 5);
    }
  });
}

function drawEvidenceFrame() {
  if (!cameraStream || !video) return;

  const width = video.videoWidth || lastCaptureWidth || 640;
  const height = video.videoHeight || lastCaptureHeight || 480;

  if (!evidenceCanvas) {
    evidenceCanvas = document.createElement("canvas");
    evidenceContext = evidenceCanvas.getContext("2d");
  }

  if (evidenceCanvas.width !== width || evidenceCanvas.height !== height) {
    evidenceCanvas.width = width;
    evidenceCanvas.height = height;
  }

  evidenceContext.clearRect(0, 0, width, height);
  evidenceContext.drawImage(video, 0, 0, width, height);

  const scaleX = width / (lastCaptureWidth || width);
  const scaleY = height / (lastCaptureHeight || height);

  const persons = latestBehaviorForEvidence?.person_candidates || [];
  const alerts = latestBehaviorForEvidence?.alert_candidates || [];
  const phoneBoxes = latestBehaviorForEvidence?.phone_candidate_boxes || [];

  persons.forEach((box, index) => {
    const hasAlert = alerts.some((alert) => alert.box && pointInsideBoxForAlert(boxCenterForAlert(box), alert.box));
    if (!hasAlert) {
      drawEvidenceBox(evidenceContext, box, `Person ${index + 1}`, "#3b82f6", scaleX, scaleY, 3);
    }
  });

  phoneBoxes.forEach((box) => {
    drawEvidenceBox(evidenceContext, box, `Phone Candidate ${box.confidence || ""}%`, "#ef4444", scaleX, scaleY, 3);
  });

  latestRecognitionsForEvidence.forEach((item) => {
    if (!item.box) return;

    if (!item.recognized && (item.confidence || 0) < 42) {
      return;
    }

    const alert = alertForRecognition(item, latestBehaviorForEvidence);
    const displayName = item.student_display_name || item.student_name || item.student_code || "Unknown";

    let label = item.recognized
      ? `${displayName} ${item.confidence}%`
      : `Unknown Face ${item.confidence || ""}%`;

    let color = item.recognized ? "#10b981" : "#f59e0b";
    let lineWidth = item.recognized ? 4 : 3;

    if (item.low_confidence && item.predicted_student_code && !item.recognized) {
      label = `Low Confidence ${item.confidence}%`;
      color = "#f59e0b";
      lineWidth = 3;
    }

    if (alert && item.recognized) {
      label = `${displayName} | Phone-use Alert`;
      color = "#ef4444";
      lineWidth = 6;
    }

    drawEvidenceBox(evidenceContext, item.box, label, color, scaleX, scaleY, lineWidth);
  });

  alerts.forEach((alert) => {
    const matched = latestRecognitionsForEvidence.some((item) => item.recognized && alertForRecognition(item, latestBehaviorForEvidence));
    if (!matched && alert.box) {
      drawEvidenceBox(evidenceContext, alert.box, "Phone-use Alert", "#ef4444", scaleX, scaleY, 5);
    }
  });

  if (latestRecognitionsForEvidence.length === 0 && persons.length === 0) {
    evidenceContext.fillStyle = "rgba(245, 158, 11, 0.92)";
    evidenceContext.fillRect(14, 66, 420, 34);
    evidenceContext.fillStyle = "#111827";
    evidenceContext.font = "15px Arial";
    evidenceContext.fillText("No AI boxes yet ? keep AI Monitoring running.", 28, 88);
  }

  drawEvidenceHeader(evidenceContext, width, height);

  evidenceAnimationFrame = requestAnimationFrame(drawEvidenceFrame);
}

