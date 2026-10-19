import { useEffect, useState } from "react";
import { getTickets } from "../api";

export default function TicketTable() {
  const [tickets, setTickets] = useState([]);
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    getTickets(category, status).then((data) => setTickets(data.items || []));
  }, [category, status]);

  return (
    <div style={{ padding: "20px", width: "100%" }}>
      <div className="filters">
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All Categories</option>
          <option value="Delivery delay">Delivery delay</option>
          <option value="Damaged item">Damaged item</option>
          <option value="Wrong item">Wrong item</option>
          <option value="Missing item">Missing item</option>
          <option value="Refund">Refund</option>
          <option value="Payment">Payment</option>
          <option value="Other">Other</option>
        </select>

        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="Open">Open</option>
          <option value="In Progress">In Progress</option>
          <option value="Resolved">Resolved</option>
        </select>
      </div>

      <table>
        <thead>
          <tr>
            <th>Ticket ID</th>
            <th>Category</th>
            <th>Status</th>
            <th>Order ID</th>
            <th>Mobile</th>
            <th>Summary</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr key={t.ticket_id}>
              <td>{t.ticket_id}</td>
              <td>{t.category}</td>
              <td>{t.status}</td>
              <td>{t.order_id}</td>
              <td>{t.mobile}</td>
              <td>{t.summary}</td>
            </tr>
          ))}
          {tickets.length === 0 && (
            <tr><td colSpan="6" style={{textAlign:"center"}}>No tickets found.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}