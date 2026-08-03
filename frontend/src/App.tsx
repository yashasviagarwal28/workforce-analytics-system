import { useEffect, useState } from "react";
import { fetchAnomalies, fetchSummary, updateReview } from "./api";
import type { Anomaly, ReviewStatus, Summary } from "./types";
import "./styles.css";

const statuses: ReviewStatus[] = [
  "pending",
  "confirmed_issue",
  "legitimate",
  "resolved",
];

export default function App() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [items, setItems] = useState<Anomaly[]>([]);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [summaryData, anomalyData] = await Promise.all([
        fetchSummary(),
        fetchAnomalies(),
      ]);
      setSummary(summaryData);
      setItems(anomalyData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function changeStatus(item: Anomaly, status: ReviewStatus) {
    const updated = await updateReview(item.punch_id, status, item.reviewer_notes ?? "");
    setItems((current) =>
      current.map((row) => (row.punch_id === updated.punch_id ? updated : row)),
    );
    setSummary(await fetchSummary());
  }

  if (loading) return <main><p>Loading OpsPulse…</p></main>;

  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">Workforce anomaly review</p>
          <h1>OpsPulse</h1>
          <p>Prioritized timekeeping records for human review.</p>
        </div>
        <button onClick={() => void load()}>Refresh</button>
      </header>

      {error && <p role="alert" className="error">{error}</p>}

      {summary && (
        <section className="cards" aria-label="Summary metrics">
          <article><strong>{summary.total_records}</strong><span>Total records</span></article>
          <article><strong>{summary.flagged_records}</strong><span>Flagged</span></article>
          <article><strong>{summary.pending_reviews}</strong><span>Pending</span></article>
          <article><strong>{summary.confirmed_issues}</strong><span>Confirmed</span></article>
        </section>
      )}

      <section className="panel">
        <h2>Flagged records</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Punch</th>
                <th>Employee</th>
                <th>Department</th>
                <th>Score</th>
                <th>Reason hint</th>
                <th>Review status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.punch_id}>
                  <td>{item.punch_id}</td>
                  <td>{item.employee_id}</td>
                  <td>{item.department_id}</td>
                  <td>{item.anomaly_score.toFixed(3)}</td>
                  <td>{item.reason_hint}</td>
                  <td>
                    <select
                      aria-label={`Review status for ${item.punch_id}`}
                      value={item.review_status}
                      onChange={(event) =>
                        void changeStatus(item, event.target.value as ReviewStatus)
                      }
                    >
                      {statuses.map((status) => (
                        <option key={status} value={status}>
                          {status.replace(/_/g, " ")}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
