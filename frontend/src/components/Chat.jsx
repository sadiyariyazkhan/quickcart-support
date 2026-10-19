import { useState, useRef, useEffect } from "react";
import { sendChat, sendVoice } from "../api";
import CitationChip from "./CitationChip";
import MicButton from "./MicButton";

export default function Chat({ sessionId, onFieldsUpdate }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => scrollToBottom(), [messages]);

    async function handleSend() {
    if (!input.trim() || loading) return;
    const userText = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userText }]);
    setLoading(true);

    try {
      const res = await sendChat(sessionId, userText);
      setMessages((prev) => [...prev, { role: "bot", text: res.reply, citations: res.citations }]);
      if (onFieldsUpdate) onFieldsUpdate(res.collected_fields);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "bot", text: "⚠️ Server error. Is the backend running?" }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleAudio(blob) {
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", text: "🎤 (Voice recording processing...)" }]);

    try {
      const res = await sendVoice(sessionId, blob);
      setMessages((prev) => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1].text = res.transcript;
        return [...newMsgs, { role: "bot", text: res.reply, citations: res.citations }];
      });
      if (onFieldsUpdate) onFieldsUpdate(res.collected_fields);
      
      if (res.reply_audio) {
        const audio = new Audio("data:audio/wav;base64," + res.reply_audio);
        audio.play();
      }
    } catch (error) {
      setMessages((prev) => [...prev, { role: "bot", text: "⚠️ Voice error. Check backend." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-window">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <p>{m.text}</p>
            {m.citations && m.citations.map((c, j) => (
              <CitationChip key={j} section={c.section} passage={c.passage} />
            ))}
          </div>
        ))}
        {loading && <div className="msg bot"><p>...</p></div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>Send</button>
        <MicButton onAudioReady={handleAudio} disabled={loading} />
      </div>
    </div>
  );
}