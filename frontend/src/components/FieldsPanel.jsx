export default function FieldsPanel({ fields }) {
  return (
    <aside className="fields-panel">
      <h3>Collected Fields</h3>
      <div><b>Name:</b> {fields?.name || "—"}</div>
      <div><b>Mobile:</b> {fields?.mobile || "—"}</div>
      <div><b>Order ID:</b> {fields?.order_id || "—"}</div>
      <div><b>Issue:</b> {fields?.issue || "—"}</div>
    </aside>
  );
}