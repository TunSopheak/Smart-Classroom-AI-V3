const startButton = document.getElementById("start-camera");
const stopButton = document.getElementById("stop-camera");
const captureButton = document.getElementById("capture-face");
const trainButton = document.getElementById("train-model");

const video = document.getElementById("camera-preview");
const studentSelect = document.getElementById("student-code");
const statusText = document.getElementById("camera-status");
const cameraBadge = document.getElementById("camera-badge");
const cameraFrame = document.getElementById("camera-frame");
const trainingMessage = document.getElementById("training-message");
const modelMessage = document.getElementById("model-message");
const modelBadge = document.getElementById("model-badge");

let cameraStream = null;
let captureCount = 0;

function setCameraStatus(message, label, className) {
  if (statusText) statusText.textContent = message;
  if (cameraBadge) {
    cameraBadge.textContent = label;
    cameraBadge.className = "status-pill " + className;
  }
}

function setTrainingMessage(message, className = "") {
  if (trainingMessage) {
    trainingMessage.textContent = message;
    trainingMessage.className = "note-box " + className;
  }
}

function setModelMessage(message, className = "") {
  if (modelMessage) {
    modelMessage.textContent = message;
    modelMessage.className = "note-box " + className;
  }
}

async function startCamera() {
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
    captureButton.disabled = false;

    if (cameraFrame) cameraFrame.classList.add("camera-active");

    setCameraStatus("Camera is running. Ready to capture face dataset.", "Running", "status-success");
    setTrainingMessage("Ready. Capture 10 to 20 clear face images for the selected student.");
  } catch (error) {
    console.error("Camera failed:", error);
    setCameraStatus("Camera failed: " + (error.name || error.message), "Error", "status-danger");
    setTrainingMessage("Camera failed. Check browser permission and try again.", "status-danger");
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }

  video.srcObject = null;
  startButton.disabled = false;
  stopButton.disabled = true;
  captureButton.disabled = true;

  if (cameraFrame) cameraFrame.classList.remove("camera-active");

  setCameraStatus("Camera stopped.", "Stopped", "status-muted");
}

function captureFrameAsDataUrl() {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;

  const context = canvas.getContext("2d");
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  return canvas.toDataURL("image/jpeg", 0.92);
}

async function captureFace() {
  if (!cameraStream) {
    setTrainingMessage("Start camera first.", "status-warning");
    return;
  }

  const studentCode = studentSelect.value;
  const imageData = captureFrameAsDataUrl();

  const formData = new FormData();
  formData.append("student_code", studentCode);
  formData.append("image_data", imageData);

  captureButton.disabled = true;
  setTrainingMessage("Capturing face image...");

  try {
    const response = await fetch("/training/capture", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (!response.ok || !result.ok) {
      throw new Error(result.message || "Capture failed.");
    }

    captureCount += 1;

    setTrainingMessage(
      `${result.message} Saved images for ${result.student_code}: ${result.image_count}. Captured this session: ${captureCount}.`,
      "status-success"
    );

    captureButton.disabled = false;
  } catch (error) {
    console.error("Capture failed:", error);
    setTrainingMessage(error.message || "Capture failed.", "status-danger");
    captureButton.disabled = false;
  }
}

async function trainModel() {
  trainButton.disabled = true;
  setModelMessage("Training face model. Please wait...");

  try {
    const response = await fetch("/training/train", {
      method: "POST",
    });

    const result = await response.json();

    if (!response.ok || !result.ok) {
      throw new Error(result.message || "Training failed.");
    }

    setModelMessage(
      `${result.message} Images: ${result.trained_images}, Students: ${result.trained_students}`,
      "status-success"
    );

    if (modelBadge) {
      modelBadge.textContent = "Trained";
      modelBadge.className = "status-pill status-success";
    }

    trainButton.disabled = false;
  } catch (error) {
    console.error("Training failed:", error);
    setModelMessage(error.message || "Training failed.", "status-danger");
    trainButton.disabled = false;
  }
}

if (startButton) startButton.addEventListener("click", startCamera);
if (stopButton) stopButton.addEventListener("click", stopCamera);
if (captureButton) captureButton.addEventListener("click", captureFace);
if (trainButton) trainButton.addEventListener("click", trainModel);


// ================================
// Stage 10.2 Upload Photos Dataset
// ================================

const photoUploadInput = document.getElementById("photo-upload-input");
const uploadPhotosButton = document.getElementById("upload-photos");
const uploadMessage = document.getElementById("upload-message");

function setUploadMessage(message, className = "") {
  if (uploadMessage) {
    uploadMessage.textContent = message;
    uploadMessage.className = "note-box " + className;
  }
}

async function uploadPhotosDataset() {
  if (!photoUploadInput || !photoUploadInput.files || photoUploadInput.files.length === 0) {
    setUploadMessage("Please choose at least one photo.", "status-warning");
    return;
  }

  const studentCode = studentSelect.value;
  const formData = new FormData();
  formData.append("student_code", studentCode);

  Array.from(photoUploadInput.files).forEach((file) => {
    formData.append("files", file);
  });

  uploadPhotosButton.disabled = true;
  setUploadMessage(`Uploading ${photoUploadInput.files.length} photo(s) for ${studentCode}...`);

  try {
    const response = await fetch("/training/upload-photos", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (!response.ok || !result.ok) {
      throw new Error(result.message || "Upload failed.");
    }

    let message = `${result.message} Total dataset for ${result.student_name}: ${result.image_count} images.`;
    if (result.errors && result.errors.length > 0) {
      message += " Some files skipped: " + result.errors.join(" | ");
    }

    setUploadMessage(message, result.skipped_count > 0 ? "status-warning" : "status-success");
    photoUploadInput.value = "";
  } catch (error) {
    console.error("Photo upload failed:", error);
    setUploadMessage(error.message || "Photo upload failed.", "status-danger");
  } finally {
    uploadPhotosButton.disabled = false;
  }
}

if (uploadPhotosButton) uploadPhotosButton.addEventListener("click", uploadPhotosDataset);

