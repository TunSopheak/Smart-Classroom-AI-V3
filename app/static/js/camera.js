const startButton = document.getElementById("start-camera");
const stopButton = document.getElementById("stop-camera");
const video = document.getElementById("camera-preview");
const statusText = document.getElementById("camera-status");
const cameraBadge = document.getElementById("camera-badge");
const cameraFrame = document.getElementById("camera-frame");
const behaviorBadge = document.getElementById("behavior-badge");
const behaviorStatus = document.getElementById("behavior-system-status");

let cameraStream = null;

function setCameraStatus(message, label, className) {
  if (statusText) {
    statusText.textContent = message;
  }

  if (cameraBadge) {
    cameraBadge.textContent = label;
    cameraBadge.className = "status-pill " + className;
  }
}

function setBehaviorMessage(message) {
  if (behaviorStatus) {
    behaviorStatus.textContent = message;
  }
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

      startButton.disabled = true;
      stopButton.disabled = false;

      if (cameraFrame) {
        cameraFrame.classList.add("camera-active");
      }

      setCameraStatus("Camera is running from this computer.", "Running", "status-success");
      setBehaviorMessage("Camera is ready. Behavior AI analysis will be connected in the next stage.");

      if (behaviorBadge) {
        behaviorBadge.textContent = "Waiting for AI";
        behaviorBadge.className = "status-pill status-info";
      }
    } catch (error) {
      console.error("Camera start failed:", error);
      setCameraStatus("Camera failed: " + (error.name || error.message), "Error", "status-danger");
      setBehaviorMessage("Camera failed, so behavior AI cannot analyze frames yet.");
    }
  });

  stopButton.addEventListener("click", () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      cameraStream = null;
    }

    video.srcObject = null;
    startButton.disabled = false;
    stopButton.disabled = true;

    if (cameraFrame) {
      cameraFrame.classList.remove("camera-active");
    }

    setCameraStatus("Camera stopped. Click Start Camera.", "Stopped", "status-muted");
    setBehaviorMessage("Behavior AI is not connected yet. Stage 2/5 will analyze camera frames.");

    if (behaviorBadge) {
      behaviorBadge.textContent = "AI Not Started";
      behaviorBadge.className = "status-pill status-warning";
    }
  });
}
