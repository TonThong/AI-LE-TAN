// Microphone permission check
const micBadgeEl = document.querySelector("#micBadge");
const micStatusEl = document.querySelector("#micStatus");

function setMicState(state, text) {
  micBadgeEl.dataset.state = state;
  micStatusEl.textContent = text;
}

async function checkMicrophonePermission() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setMicState("error", "Trình duyệt không hỗ trợ micro");
    return false;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: true
    });

    // Thành công: đã cấp quyền micro
    setMicState("ready", "Đã cấp quyền micro");

    // Tắt micro sau khi kiểm tra quyền
    stream.getTracks().forEach((track) => track.stop());

    return true;
  } catch (error) {
    console.error("Micro permission error:", error);

    if (error.name === "NotAllowedError") {
      setMicState("error", "Micro đang bị chặn");
    } else if (error.name === "NotFoundError") {
      setMicState("error", "Không tìm thấy micro");
    } else {
      setMicState("error", "Không thể truy cập micro");
    }

    return false;
  }
}
checkMicrophonePermission();

// Session state management
let isSessionRunning = false;

function setSessionRunning(running) {
  isSessionRunning = running;

  startButton.disabled = running;
  endButton.disabled = !running;

  if (running) {
    setMicState("listening", "Trò chuyện");
  } else {
    setMicState("ready", "Đã cấp quyền micro");
  }
}

// Voice detection variables
let hasVoice = false;
let voiceDuration = 0;
let lastCheckTime = 0;

const VOICE_THRESHOLD = 0.035; 
const MIN_VOICE_DURATION = 300;

// Recording and silence detection
const startButton = document.querySelector("#startButton");
const endButton = document.querySelector("#endButton");

let audioContext;
let analyser;
let silenceTimer = null;

const SILENCE_THRESHOLD = 0.03;
const SILENCE_DELAY = 2000;

let mediaRecorder;
let audioChunks = [];
let currentStream = null;

startButton.addEventListener("click", async () => {
  try {
    setSessionRunning(true);
    await startRecording();
  } catch (error) {
    console.error("Error accessing microphone:", error);
  }
})

async function startRecording() {
  currentStream = await navigator.mediaDevices.getUserMedia({ audio: true });

  audioChunks = [];

  hasVoice = false;
  voiceDuration = 0;
  lastCheckTime = performance.now();

  clearTimeout(silenceTimer);
  silenceTimer = null;

  if (audioContext) {
    await audioContext.close();
    audioContext = null;
  }

  mediaRecorder = new MediaRecorder(currentStream, {
    mimeType: "audio/webm"
  });

  mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
      audioChunks.push(event.data);
      console.log("Audio chunk recorded:", event.data);
    }
  };

  mediaRecorder.onstop = async () => {
    clearTimeout(silenceTimer);
    silenceTimer = null;

    if (audioContext) {
      await audioContext.close();
      audioContext = null;
    }

    if (currentStream) {
      currentStream.getTracks().forEach((track) => track.stop());
      currentStream = null;
    }

    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

    if (hasVoice && audioBlob.size > 1000) {
      await sendAudioToBackend(audioBlob);
    }

    // Chỉ tự ghi âm lại nếu phiên vẫn đang chạy
    if (isSessionRunning) {
      await startRecording();
    }
  };

  mediaRecorder.start();

  startSilenceDetection(currentStream);
}

function startSilenceDetection(stream) {
  audioContext = new AudioContext();

  analyser = audioContext.createAnalyser();
  analyser.fftSize = 2048;

  const microphone = audioContext.createMediaStreamSource(stream);
  microphone.connect(analyser);

  const dataArray = new Uint8Array(analyser.fftSize);

  function checkSilence() {
    if (!mediaRecorder || mediaRecorder.state !== "recording") {
      return;
    }

    analyser.getByteTimeDomainData(dataArray);

    let sum = 0;

    for (let i = 0; i < dataArray.length; i++) {
      const value = (dataArray[i] - 128) / 128;
      sum += value * value;
    }

    const volume = Math.sqrt(sum / dataArray.length);

    const now = performance.now();
    const deltaTime = now - lastCheckTime;
    lastCheckTime = now;

    // Kiểm tra có âm thanh đủ lâu không
    if (volume >= VOICE_THRESHOLD) {
      voiceDuration += deltaTime;

      if (voiceDuration >= MIN_VOICE_DURATION) {
        hasVoice = true;
      }
    }

    // Kiểm tra im lặng để tự stop
    if (volume < SILENCE_THRESHOLD) {
      if (!silenceTimer) {
        silenceTimer = setTimeout(() => {
          if (mediaRecorder.state === "recording") {
            mediaRecorder.stop();
          }
        }, SILENCE_DELAY);
      }
    } else {
      clearTimeout(silenceTimer);
      silenceTimer = null;
    }

    requestAnimationFrame(checkSilence);
  }

  checkSilence();
}

endButton.addEventListener("click", async () => {
  try {
    if (!isSessionRunning) return;

    setSessionRunning(false);

    clearTimeout(silenceTimer);
    silenceTimer = null;

    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
    }

    if (currentStream) {
      currentStream.getTracks().forEach((track) => track.stop());
      currentStream = null;
    }

    if (audioContext) {
      await audioContext.close();
      audioContext = null;
    }
  } catch (error) {
    console.error("Error stopping recording:", error);
  }
});

// Function to send audio to backend
async function sendAudioToBackend(audioBlob) {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");

  const response = await fetch("/api/voice/transcribe", {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error('Failed to send audio to backend: ' + response.statusText);
  }

  const result = await response.json();
  console.log("Backend result:", result);

  if (result.qwen_response) {
    await playSynthesizedSpeech(result.qwen_response);
  }
  return result;
}

// Function to play synthesized speech
let currentAudio = null;

async function playSynthesizedSpeech(text) {
  if (!text || !text.trim()) {
    return;
  }

  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
  }

  const response = await fetch("/api/voice/synthesize", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      text: text
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`TTS error: ${errorText}`);
  }

  const audioBlob = await response.blob();
  const audioUrl = URL.createObjectURL(audioBlob);

  currentAudio = new Audio(audioUrl);

  try {
    await new Promise((resolve, reject) => {
      currentAudio.onended = resolve;
      currentAudio.onerror = reject;

      currentAudio.play().catch(reject);
    });
  } finally {
    URL.revokeObjectURL(audioUrl);
    currentAudio = null;
  }
}