import { useState } from "react";
import Chat from "../components/Chat";
import FieldsPanel from "../components/FieldsPanel";

export default function AssistantPage() {
  const [fields, setFields] = useState({});
  // Generates a random UUID only ONCE when the component mounts
  const [sessionId] = useState(() => crypto.randomUUID()); 

  return (
    <div className="container">
      <Chat sessionId={sessionId} onFieldsUpdate={setFields} />
      <FieldsPanel fields={fields} />
    </div>
  );
}