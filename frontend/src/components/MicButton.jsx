import { useState, useRef } from "react";

export default function MicButton({ onAudioReady, disabled }) {
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  async function toggleRecording() {
    // If already recording, STOP and send
    if (recording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      setRecording(false);
      return;
    }

    // Start a new recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/wav" });
        onAudioReady(blob);
        stream.getTracks().forEach((track) => track.stop()); // Turn off mic
      };

      mediaRecorder.start();
      setRecording(true);

      // Safety auto-stop after 15 seconds (in case user forgets to stop)
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
          mediaRecorderRef.current.stop();
          setRecording(false);
        }
      }, 60000);

    } catch (err) {
      alert("Microphone access denied or not available.");
    }
  }

  return (
    <button
      className={`mic-btn ${recording ? "recording" : ""}`}
      onClick={toggleRecording}
      disabled={disabled}
      title={recording ? "Click to stop and send" : "Click to speak"}
    >
      {recording ? "⏹ Stop" : "🎤"}
    </button>
  );
}