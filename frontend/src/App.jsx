import { useState } from "react";
import AssistantPage from "./pages/AssistantPage";
import TicketsPage from "./pages/TicketsPage";

export default function App() {
  const [page, setPage] = useState("assistant");

  return (
    <div>
      <nav>
        <button onClick={() => setPage("assistant")}>💬 Assistant</button>
        <button onClick={() => setPage("tickets")}>🎫 Tickets</button>
      </nav>
      {page === "assistant" ? <AssistantPage /> : <TicketsPage />}
    </div>
  );
}