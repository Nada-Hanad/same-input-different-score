import React from "react";
import {classificationLabel} from "./classifications";
import {
  type Research,
  type Pair,
  type Target,
  type Interval,
  type Plan,
} from "./model";
export const fmt = (n: number | null | undefined) => n == null ? "Not recorded" : n.toLocaleString("en-US");
export const nice = (s: string) => s.replaceAll("->", " → ");
export function IntervalText({ value }: { value?: Interval | null }) {
  return value ? (
    <span>
      {value.pct.toFixed(4)}%{" "}
      <small>[{value.ci95.map((x) => x.toFixed(4)).join(", ")}]</small>
    </span>
  ) : (
    <span className="muted">Not recorded</span>
  );
}
export function Stat({
  value,
  label,
  detail,
}: {
  value: number | string | null | undefined;
  label: string;
  detail?: string;
}) {
  return (
    <div className="stat">
      <strong>{typeof value === "string" ? value : fmt(value)}</strong>
      <span>{label}</span>
      {detail && <small>{detail}</small>}
    </div>
  );
}
export function Callout({
  children,
  tone = "note",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <aside className={"callout " + tone}>{children}</aside>;
}
export function Table({
  rows,
  label,
  value = "Websites",
  emptyLabel = "Not recorded",
}: {
  rows?: Record<string, number | null> | null;
  label: string;
  value?: string;
  emptyLabel?: string;
}) {
  return (
    <div className="table-scroll">
      <table>
        <caption>{label}</caption>
        <thead>
          <tr>
            <th scope="col">Measurement</th>
            <th scope="col">{value}</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(rows ?? {}).map(([k, v]) => (
            <tr key={k}>
              <th scope="row">{nice(k)}</th>
              <td>{fmt(v)}</td>
            </tr>
          ))}
          {!Object.keys(rows ?? {}).length && (
            <tr>
              <td colSpan={2}>{rows == null ? "Not recorded" : emptyLabel}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
export function Bars({
  rows,
  label,
  colors = ["var(--accent)"],
}: {
  rows: { label: string; values: number[] }[];
  label: string;
  colors?: string[];
}) {
  const max = Math.max(
    1,
    ...rows.map((x) => x.values.reduce((a, b) => a + b, 0)),
  );
  const h = rows.length * 38 + 32;
  return (
    <div className="chart-scroll">
      <svg
        className="bar-chart"
        viewBox={`0 0 740 ${h}`}
        role="img"
        aria-label={label}
      >
        <title>{label}</title>
        {rows.map((r, i) => {
          let offset = 0;
          return (
            <g key={r.label}>
              <text x="0" y={i * 38 + 24} className="chart-label">
                {nice(r.label)}
              </text>
              {r.values.map((v, j) => {
                const x = 250 + (offset / max) * 400;
                offset += v;
                return (
                  <rect
                    key={j}
                    x={x}
                    y={i * 38 + 10}
                    width={(v / max) * 400}
                    height="19"
                    rx="2"
                    fill={colors[j % colors.length]}
                  >
                    <title>
                      {r.label}: {fmt(v)}
                    </title>
                  </rect>
                );
              })}
              <text x="662" y={i * 38 + 24}>
                {fmt(r.values.reduce((a, b) => a + b, 0))}
              </text>
            </g>
          );
        })}
        <line x1="250" y1="0" x2="250" y2={h - 20} stroke="var(--line)" />
      </svg>
    </div>
  );
}
export function PairControl({
  data,
  pair,
  onChange,
}: {
  data: Research;
  pair: Pair;
  onChange: (p: Pair) => void;
}) {
  return (
    <label className="control">
      Release pair
      <select
        aria-label="Release pair"
        title={`${nice(pair.pair)} · ${classificationLabel(pair.class)}`}
        value={pair.pair}
        onChange={(e) =>
          onChange(data.pairs.find((p) => p.pair === e.target.value)!)
        }
      >
        {data.pairs.map((p) => (
          <option key={p.pair} value={p.pair}>
            {nice(p.pair)} · {classificationLabel(p.class)}
          </option>
        ))}
      </select>
    </label>
  );
}
export function TargetControl({
  target,
  onChange,
}: {
  target: Target;
  onChange: (t: Target) => void;
}) {
  return (
    <fieldset className="segmented">
      <legend>Target grade</legend>
      {(["B", "A", "A+"] as Target[]).map((t) => (
        <button key={t} aria-pressed={target === t} onClick={() => onChange(t)}>
          {t} <small>{t === "B" ? 70 : t === "A" ? 90 : 100}+</small>
        </button>
      ))}
    </fieldset>
  );
}
export function Source({ names }: { names: string[] }) {
  return (
    <p className="source">
      Evidence: {names.join(" · ")}. Aggregate export; original records retained
      locally.
    </p>
  );
}
