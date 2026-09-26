import { useEffect, useState } from "react";

function Stat({ label, value, detail }) {
  return (
    <section className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </section>
  );
}

function isSafeJobId(value) {
  return typeof value === "string" && /^[A-Za-z0-9_-]{1,128}$/.test(value);
}

function App() {
  const [health, setHealth] = useState("checking");
  const [rows, setRows] = useState([]);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState("Ready");
  const [jobId, setJobId] = useState(null);
  const [exchange, setExchange] = useState("Both");
  const [lookback, setLookback] = useState("5");
  const [jump, setJump] = useState("1");
  const [view, setView] = useState("price-pulse");
  const [marketRows, setMarketRows] = useState([]);
  const [unusualRows, setUnusualRows] = useState([]);

  useEffect(() => {
    fetch("/health")
      .then((r) => r.ok ? r.json() : Promise.reject(new Error("API unavailable")))
      .then(() => setHealth("online"))
      .catch(() => setHealth("offline"));
    refreshHistory();
  }, []);

  useEffect(() => {
    if (!jobId || !isSafeJobId(jobId)) {
      if (jobId) setStatus("Invalid job id");
      return undefined;
    }
    const safeJobId = encodeURIComponent(jobId);
    const timer = setInterval(async () => {
      try {
        const response = await fetch(
          `/api/v1/intraday/price-jumps/jobs/${safeJobId}`,
        );
        const job = await response.json();
        setStatus(job.status ?? "unknown");
        if (job.status === "completed") {
          setRows(job.results ?? []);
          setJobId(null);
          clearInterval(timer);
        }
        if (job.status === "failed") {
          setJobId(null);
          clearInterval(timer);
        }
      } catch {
        setStatus("API error");
        setJobId(null);
        clearInterval(timer);
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [jobId]);

  async function loadUnusualActivity() {
    setStatus("Loading unusual activity");
    try {
      const params = new URLSearchParams({
        limit: "20",
        exchange_category: exchange,
      });
      const response = await fetch(
        `/api/v1/intraday/unusual-activity?${params.toString()}`,
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Unable to load activity");
      setUnusualRows(data.results ?? []);
      setView("unusual");
      setStatus("Ready");
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function loadMarketScanner() {
    setStatus("Loading market scanner");
    try {
      const response = await fetch("/api/v1/scanner/market?limit=20");
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Unable to load market scan");
      setMarketRows(data.results ?? []);
      setView("market");
      setStatus("Ready");
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function refreshHistory() {
    try {
      const response = await fetch("/api/v1/intraday/history?limit=10");
      const data = await response.json();
      setHistory(data.scans ?? []);
    } catch {
      setHistory([]);
    }
  }

  async function startScan() {
    setRows([]);
    setView("price-pulse");
    setStatus("Starting");
    try {
      const params = new URLSearchParams({
        exchange_category: exchange,
        lookback_minutes: lookback,
        jump_percent: jump,
      });
      const response = await fetch(
        `/api/v1/intraday/price-jumps/start?${params.toString()}`,
        { method: "POST" },
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Unable to start scan");
      setJobId(data.job_id);
      setStatus("queued");
    } catch (error) {
      setStatus(error.message);
    }
  }

  return (
    <div className="app">
      <header>
        <div>
          <p className="eyebrow">EROS · AI STOCK ANALYZER</p>
          <h1>Intraday Command Center</h1>
          <p className="subtitle">React frontend over the existing FastAPI scanner.</p>
        </div>
        <div className={`health ${health}`}>● API {health}</div>
      </header>

      <main>
        <div className="stats">
          <Stat label="Scanner" value={status} detail="Background job" />
          <Stat label="Candidates" value={rows.length || "—"} detail="Latest pulse" />
          <Stat label="History" value={history.length} detail="Saved scans" />
          <Stat label="Mode" value="NSE + BSE" detail="Existing scanner universe" />
        </div>

        <section className="panel controls">
          <div>
            <label htmlFor="exchange-select">Exchange</label>
            <select id="exchange-select" value={exchange} onChange={(e) => setExchange(e.target.value)}>
              <option>Both</option><option>NSE</option><option>BSE</option>
            </select>
          </div>
          <div>
            <label htmlFor="lookback-select">Lookback</label>
            <select id="lookback-select" value={lookback} onChange={(e) => setLookback(e.target.value)}>
              <option value="5">5 min</option><option value="10">10 min</option><option value="15">15 min</option>
            </select>
          </div>
          <div>
            <label htmlFor="jump-select">Jump threshold</label>
            <select id="jump-select" value={jump} onChange={(e) => setJump(e.target.value)}>
              <option value="1">1%</option><option value="2">2%</option><option value="3">3%</option>
            </select>
          </div>
          <button onClick={startScan} disabled={Boolean(jobId)}>
            {jobId ? "Scanning…" : "Start price-pulse scan"}
          </button>
          <button className="secondary" onClick={loadUnusualActivity}>
            Unusual activity
          </button>
          <button className="secondary" onClick={loadMarketScanner}>
            Market scanner
          </button>
          <button className="secondary" onClick={refreshHistory}>Refresh history</button>
        </section>

        <section className="panel">
          <div className="panel-title">
            <h2>{view === "unusual" ? "Unusual activity" : view === "market" ? "Market scanner" : "Latest price pulses"}</h2>
            <span>
              {view === "unusual" ? unusualRows.length : view === "market" ? marketRows.length : rows.length} results
            </span>
          </div>
          <div className="table-wrap">
            {view === "price-pulse" ? (
              <table>
                <thead><tr><th>Symbol</th><th>Exchange</th><th>Last price</th><th>Change</th><th>Volume</th></tr></thead>
                <tbody>
                  {rows.length ? rows.map((row, i) => (
                    <tr key={row.Symbol ?? i}>
                      <td><strong>{row.Symbol ?? "—"}</strong></td>
                      <td>{row.Exchange ?? "—"}</td>
                      <td>{row["Last price"] ?? "—"}</td>
                      <td>{row["Change over 5m"] ?? "—"}</td>
                      <td>{row["Volume vs recent bars"] ?? "—"}</td>
                    </tr>
                  )) : <tr><td colSpan="5" className="empty">Run a price-pulse scan to populate candidates.</td></tr>}
                </tbody>
              </table>
            ) : view === "unusual" ? (
              <table>
                <thead><tr><th>Symbol</th><th>Exchange</th><th>Signal</th><th>Price</th><th>Volume</th></tr></thead>
                <tbody>
                  {unusualRows.length ? unusualRows.map((row, i) => (
                    <tr key={row.Symbol ?? i}>
                      <td><strong>{row.Symbol ?? "—"}</strong></td>
                      <td>{row.Exchange ?? "—"}</td>
                      <td>{row.Signal ?? row["Activity signal"] ?? "—"}</td>
                      <td>{row.Price ?? row["Last price"] ?? "—"}</td>
                      <td>{row["Volume ratio"] ?? row["Volume vs recent bars"] ?? "—"}</td>
                    </tr>
                  )) : <tr><td colSpan="5" className="empty">No unusual activity returned.</td></tr>}
                </tbody>
              </table>
            ) : (
              <table>
                <thead><tr><th>Symbol</th><th>Price</th><th>Trend</th><th>RSI</th><th>MACD</th><th>AI score</th></tr></thead>
                <tbody>
                  {marketRows.length ? marketRows.map((row, i) => (
                    <tr key={row.Symbol ?? i}>
                      <td><strong>{row.Symbol ?? "—"}</strong></td>
                      <td>{row.Price ?? "—"}</td>
                      <td>{row.Trend ?? "—"}</td>
                      <td>{row.RSI ?? "—"}</td>
                      <td>{row.MACD ?? "—"}</td>
                      <td>{row["AI Score"] ?? row.AI_Score ?? "—"}</td>
                    </tr>
                  )) : <tr><td colSpan="6" className="empty">Load the market scanner to populate results.</td></tr>}
                </tbody>
              </table>
            )}
          </div>
        </section>

        <section className="panel">
          <div className="panel-title"><h2>Recent scan history</h2><span>Last 10</span></div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Completed</th><th>Job</th><th>Candidates</th><th>Universe checked</th></tr></thead>
              <tbody>
                {history.length ? history.map((scan) => (
                  <tr key={scan.job_id}>
                    <td>{scan.completed_at ?? "—"}</td>
                    <td>{scan.job_id?.slice(0, 10) ?? "—"}…</td>
                    <td>{scan.count ?? "—"}</td>
                    <td>{scan.scan_stats?.candidate_count ?? "—"}</td>
                  </tr>
                )) : <tr><td colSpan="4" className="empty">No saved scans yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
