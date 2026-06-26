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
      ? `${item.student_code} ${item.confidence}%`
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
    const studentCode = item.student_code || "Unknown";
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
