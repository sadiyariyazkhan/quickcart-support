const BASE_URL = "http://127.0.0.1:8000";

export async function sendChat(sessionId, text) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, text: text }),
  });
  return res.json();
}

export async function sendVoice(sessionId, audioBlob) {
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("audio", audioBlob, "recording.wav");

  const res = await fetch(`${BASE_URL}/voice`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function getTickets(category = "", status = "") {
  const params = new URLSearchParams();
  if (category) params.append("category", category);
  if (status) params.append("status", status);
  
  const res = await fetch(`${BASE_URL}/tickets?${params.toString()}`);
  return res.json();
}