import { useState } from "react";

export default function CitationChip({ section, passage }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <span className="chip" onClick={() => setOpen(true)}>{section}</span>
      {open && (
        <div className="modal" onClick={() => setOpen(false)}>
          <div className="modal-body" onClick={(e) => e.stopPropagation()}>
            <h4>{section}</h4>
            <p>{passage}</p>
            <button onClick={() => setOpen(false)}>Close</button>
          </div>
        </div>
      )}
    </>
  );
}