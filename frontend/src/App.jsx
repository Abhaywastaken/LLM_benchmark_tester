import React, { useEffect, useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";

const API_BASE = "http://localhost:8000";

function average(values) {
  if (!values.length) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function shortModelName(name) {
  return name
    .replace("Meta: ", "")
    .replace("Google: ", "")
    .replace("NVIDIA: ", "")
    .replace("OpenAI: ", "")
    .replace("DeepSeek: ", "");
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="chart-tooltip">
      <strong>{label}</strong>
      <p>{payload[0].name}: {payload[0].value}</p>
    </div>
  );
}

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  async function loadResults() {
    try {
      const res = await fetch(`${API_BASE}/results`);
      const json = await res.json();
      setData(json);
    } catch (error) {
      setData({
        message:
          "Could not connect to backend. Make sure FastAPI is running on http://localhost:8000",
        scores: [],
        cases: [],
        raw_answers: {}
      });
    }
  }

  async function runBenchmark() {
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/run`, {
        method: "POST"
      });

      const json = await res.json();
      setData(json);
    } catch (error) {
      setData({
        message:
          "Benchmark failed or backend is not running. Check your backend terminal for errors.",
        scores: [],
        cases: [],
        raw_answers: {}
      });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadResults();
  }, []);

  const leaderboard = useMemo(() => {
    if (!data?.scores) return [];

    const map = {};

    for (const score of data.scores) {
      if (!map[score.model_id]) {
        map[score.model_id] = [];
      }

      map[score.model_id].push(score.score);
    }

    return Object.entries(map)
      .map(([model, scores]) => ({
        model,
        label: shortModelName(model),
        averageScore: Number(average(scores).toFixed(2))
      }))
      .sort((a, b) => b.averageScore - a.averageScore);
  }, [data]);

  const byTest = useMemo(() => {
    if (!data?.scores) return [];

    const map = {};

    for (const score of data.scores) {
      const key = `${shortModelName(score.model_id)} / ${score.test_type}`;

      if (!map[key]) {
        map[key] = [];
      }

      map[key].push(score.score);
    }

    return Object.entries(map).map(([name, scores]) => ({
      name,
      score: Number(average(scores).toFixed(2))
    }));
  }, [data]);

  const hasErrors = useMemo(() => {
    if (!data?.raw_answers) return false;

    return Object.values(data.raw_answers).some((answer) =>
      String(answer).startsWith("ERROR:")
    );
  }, [data]);

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">EVM · Solidity · LLM Benchmarking</p>
          <h1>EvoAudit Bench</h1>
          <p>
            Benchmarking OpenRouter-hosted LLMs on EVM smart contract security
            and DeFi trading logic vulnerabilities.
          </p>
        </div>

        <div className="actions">
          <button onClick={runBenchmark} disabled={loading}>
            {loading ? "Running benchmark..." : "Run Benchmark"}
          </button>

          <button className="secondary-button" onClick={loadResults} disabled={loading}>
            Refresh Results
          </button>
        </div>
      </header>

      {data?.message && <div className="notice">{data.message}</div>}

      {hasErrors && (
        <div className="notice error">
          Some model calls returned API errors. Scroll to Raw Model Answers to
          see which model failed.
        </div>
      )}

      <section className="stats">
        <div className="stat-card">
          <span>Run ID</span>
          <strong>{data?.run_id || "No run yet"}</strong>
        </div>

        <div className="stat-card">
          <span>Cases</span>
          <strong>{data?.cases?.length || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Scores</span>
          <strong>{data?.scores?.length || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Models</span>
          <strong>{leaderboard.length || 0}</strong>
        </div>
      </section>

      <section className="grid">
        <div className="card chart-card">
          <div className="card-header">
            <div>
              <h2>Overall Model Leaderboard</h2>
              <p>Average score across all benchmark cases.</p>
            </div>
          </div>

          {leaderboard.length > 0 ? (
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={leaderboard} margin={{ top: 16, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#24314f" />
                <XAxis
                  dataKey="label"
                  tick={{ fill: "#dbe7ff", fontSize: 12 }}
                  axisLine={{ stroke: "#4d5d7c" }}
                  tickLine={{ stroke: "#4d5d7c" }}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fill: "#dbe7ff", fontSize: 12 }}
                  axisLine={{ stroke: "#4d5d7c" }}
                  tickLine={{ stroke: "#4d5d7c" }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="averageScore"
                  name="Average Score"
                  fill="#ffffff"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="empty">No benchmark results yet.</p>
          )}

          {leaderboard.length > 0 && (
            <table className="mini-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Model</th>
                  <th>Average Score</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((row, index) => (
                  <tr key={row.model}>
                    <td>#{index + 1}</td>
                    <td>{row.model}</td>
                    <td>{row.averageScore}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card chart-card">
          <div className="card-header">
            <div>
              <h2>Score by Test Type</h2>
              <p>Breakdown by model and benchmark category.</p>
            </div>
          </div>

          {byTest.length > 0 ? (
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={byTest} margin={{ top: 16, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#24314f" />
                <XAxis
                  dataKey="name"
                  hide
                  tick={{ fill: "#dbe7ff", fontSize: 12 }}
                  axisLine={{ stroke: "#4d5d7c" }}
                  tickLine={{ stroke: "#4d5d7c" }}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fill: "#dbe7ff", fontSize: 12 }}
                  axisLine={{ stroke: "#4d5d7c" }}
                  tickLine={{ stroke: "#4d5d7c" }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="score"
                  name="Score"
                  fill="#ffffff"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="empty">No test-type scores yet.</p>
          )}
        </div>
      </section>

      <section className="card">
        <h2>Model Scores</h2>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Case</th>
                <th>Test</th>
                <th>Score</th>
                <th>Detected</th>
                <th>False Positives</th>
              </tr>
            </thead>

            <tbody>
              {data?.scores?.map((s, index) => (
                <tr key={index}>
                  <td>{s.model_id}</td>
                  <td>{s.case_id}</td>
                  <td>{s.test_type}</td>
                  <td>
                    <span className={s.score >= 80 ? "score-pill good" : s.score > 0 ? "score-pill mid" : "score-pill bad"}>
                      {s.score}
                    </span>
                  </td>
                  <td>
                    {s.detected_bugs}/{s.total_bugs}
                  </td>
                  <td>{s.false_positives}</td>
                </tr>
              ))}

              {!data?.scores?.length && (
                <tr>
                  <td colSpan="6">No scores available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <h2>Benchmark Cases</h2>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Contract</th>
                <th>Test Type</th>
                <th>Hidden Bugs</th>
              </tr>
            </thead>

            <tbody>
              {data?.cases?.map((c) => (
                <tr key={c.case_id}>
                  <td>{c.case_id}</td>
                  <td>{c.contract_name}</td>
                  <td>{c.test_type}</td>
                  <td>{c.bugs?.length || 0}</td>
                </tr>
              ))}

              {!data?.cases?.length && (
                <tr>
                  <td colSpan="4">No cases available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <h2>Raw Model Answers</h2>

        {data?.raw_answers && Object.keys(data.raw_answers).length > 0 ? (
          Object.entries(data.raw_answers).map(([key, value]) => {
            const isError = String(value).startsWith("ERROR:");

            return (
              <details
                key={key}
                className={isError ? "raw-answer raw-error" : "raw-answer"}
              >
                <summary>{key}</summary>
                <pre>{value}</pre>
              </details>
            );
          })
        ) : (
          <p className="empty">No raw answers available.</p>
        )}
      </section>
    </div>
  );
}

export default App;