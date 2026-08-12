import { useEffect, useState } from "react";

const emptyForm = {
  name: "",
  email: "",
  subject: "",
  description: ""
};

function Badge({ value }) {
  const cls = value.toLowerCase().replace(/\s+/g, "-");
  return <span className={`badge ${cls}`}>{value}</span>;
}

function App() {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({});
  const [form, setForm] = useState(emptyForm);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("All");

  async function load() {
    const query = new URLSearchParams();

    if (search) query.set("search", search);
    if (status !== "All") query.set("status", status);

    const [ticketResponse, statsResponse] = await Promise.all([
      fetch(`/api/tickets?${query.toString()}`),
      fetch("/api/stats")
    ]);

    setTickets(await ticketResponse.json());
    setStats(await statsResponse.json());
  }

  useEffect(() => {
    load();
  }, [status]);

  function change(event) {
    setForm({
      ...form,
      [event.target.name]: event.target.value
    });
  }

  async function analyze() {
    if (!form.subject || !form.description) {
      setMessage("Enter subject and description first.");
      return;
    }

    setLoading(true);
    setMessage("");

    const response = await fetch("/api/tickets/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        subject: form.subject,
        description: form.description
      })
    });

    const data = await response.json();

    setLoading(false);

    if (!response.ok) {
      setMessage(data.error || "Analysis failed");
      return;
    }

    setAnalysis(data);
  }

  async function submit(event) {
    event.preventDefault();

    setLoading(true);
    setMessage("");

    const response = await fetch("/api/tickets", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(form)
    });

    const data = await response.json();

    setLoading(false);

    if (!response.ok) {
      setMessage(data.error || "Could not create ticket");
      return;
    }

    setMessage(`Ticket #${data.id} created successfully.`);
    setForm(emptyForm);
    setAnalysis(null);
    load();
  }

  async function updateStatus(id, nextStatus) {
    const response = await fetch(`/api/tickets/${id}/status`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ status: nextStatus })
    });

    if (response.ok) {
      load();
    }
  }

  function searchTickets(event) {
    event.preventDefault();
    load();
  }

  return (
    <div>
      <header className="topbar">
        <div>
          <div className="brand">SupportAI</div>
          <div className="subtitle">
            Smart Support Ticket Resolution Platform
          </div>
        </div>
        <div className="live">● AI ENGINE ONLINE</div>
      </header>

      <main className="container">
        <section className="hero">
          <div>
            <span className="eyebrow">REAL-WORLD AI APPLICATION</span>
            <h1>Resolve support requests faster.</h1>
            <p>
              Submit a ticket and let the AI classify, prioritize,
              route and recommend a resolution.
            </p>
          </div>
          <div className="hero-icon">AI</div>
        </section>

        <section className="stats">
          <div className="stat"><span>Total</span><strong>{stats.total || 0}</strong></div>
          <div className="stat"><span>Open</span><strong>{stats.open || 0}</strong></div>
          <div className="stat"><span>In Progress</span><strong>{stats.in_progress || 0}</strong></div>
          <div className="stat"><span>Urgent</span><strong>{stats.urgent || 0}</strong></div>
          <div className="stat"><span>Resolved</span><strong>{stats.resolved || 0}</strong></div>
        </section>

        {message && <div className="message">{message}</div>}

        <section className="main-grid">
          <div className="card">
            <div className="card-title">
              <div>
                <h2>Report a Problem</h2>
                <p>Describe the customer's issue.</p>
              </div>
            </div>

            <form onSubmit={submit}>
              <label>Name</label>
              <input
                name="name"
                value={form.name}
                onChange={change}
                placeholder="Customer name"
                required
              />

              <label>Email</label>
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={change}
                placeholder="customer@example.com"
                required
              />

              <label>Subject</label>
              <input
                name="subject"
                value={form.subject}
                onChange={change}
                placeholder="Payment failed"
                required
              />

              <label>Description</label>
              <textarea
                name="description"
                value={form.description}
                onChange={change}
                placeholder="Explain the problem in detail..."
                rows="7"
                required
              />

              <div className="form-actions">
                <button
                  type="button"
                  className="secondary"
                  onClick={analyze}
                  disabled={loading}
                >
                  {loading ? "Analyzing..." : "Analyze with AI"}
                </button>

                <button type="submit" disabled={loading}>
                  Create Ticket
                </button>
              </div>
            </form>
          </div>

          <div className="card">
            <div className="card-title">
              <div>
                <h2>AI Analysis</h2>
                <p>Automatic ticket triage.</p>
              </div>
              <span className="ai-chip">LANGGRAPH</span>
            </div>

            {!analysis ? (
              <div className="empty-analysis">
                <div className="brain">AI</div>
                <h3>No analysis yet</h3>
                <p>
                  Enter a subject and description, then click
                  <b> Analyze with AI</b>.
                </p>
              </div>
            ) : (
              <div className="analysis">
                <div className="analysis-grid">
                  <div><span>Category</span><Badge value={analysis.category} /></div>
                  <div><span>Priority</span><Badge value={analysis.priority} /></div>
                  <div><span>Sentiment</span><Badge value={analysis.sentiment} /></div>
                  <div><span>Assigned Team</span><Badge value={analysis.team} /></div>
                </div>

                <div className="resolution">
                  <h3>Suggested Resolution</h3>
                  <p>{analysis.suggested_resolution}</p>
                </div>
              </div>
            )}
          </div>
        </section>

        <section className="card tickets-card">
          <div className="ticket-toolbar">
            <div>
              <h2>Support Queue</h2>
              <p>Review and update incoming tickets.</p>
            </div>

            <form className="search" onSubmit={searchTickets}>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search tickets..."
              />
              <button>Search</button>
            </form>
          </div>

          <div className="filters">
            {["All", "Open", "In Progress", "Resolved", "Closed"].map((item) => (
              <button
                key={item}
                className={status === item ? "filter active" : "filter"}
                onClick={() => setStatus(item)}
              >
                {item}
              </button>
            ))}
          </div>

          {tickets.length === 0 ? (
            <div className="empty">No tickets found.</div>
          ) : (
            <div className="ticket-list">
              {tickets.map((ticket) => (
                <article className="ticket" key={ticket.id}>
                  <div className="ticket-main">
                    <div className="ticket-top">
                      <span className="ticket-id">#{ticket.id}</span>
                      <h3>{ticket.subject}</h3>
                    </div>

                    <p>{ticket.description}</p>

                    <div className="ticket-meta">
                      <span>{ticket.name}</span>
                      <span>{ticket.email}</span>
                      <span>Team: {ticket.team}</span>
                    </div>
                  </div>

                  <div className="ticket-side">
                    <Badge value={ticket.priority} />
                    <Badge value={ticket.category} />
                    <Badge value={ticket.status} />

                    <select
                      value={ticket.status}
                      onChange={(e) =>
                        updateStatus(ticket.id, e.target.value)
                      }
                    >
                      <option>Open</option>
                      <option>In Progress</option>
                      <option>Resolved</option>
                      <option>Closed</option>
                    </select>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
