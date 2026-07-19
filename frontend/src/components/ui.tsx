import { ReactNode } from "react";

export function Bezel({
  children,
  style,
  onClick,
  className = "",
}: {
  children: ReactNode;
  style?: React.CSSProperties;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <div className={`bezel ${className}`} style={style} onClick={onClick}>
      {children}
    </div>
  );
}

export function Label({ children }: { children: ReactNode }) {
  return <div className="label">{children}</div>;
}

export function ReadoutCard({
  label,
  value,
  unit,
  accentColor,
}: {
  label: string;
  value: string | number;
  unit?: string;
  accentColor?: string;
}) {
  return (
    <Bezel style={{ padding: "16px 18px" }}>
      <Label>{label}</Label>
      <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
        <span className="readout-value" style={{ color: accentColor || "var(--color-text)" }}>
          {value}
        </span>
        {unit && <span className="mono" style={{ fontSize: 13, color: "var(--color-muted)" }}>{unit}</span>}
      </div>
    </Bezel>
  );
}

export function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div
        className="mono"
        style={{
          fontSize: 10,
          letterSpacing: "0.14em",
          color: "var(--color-amber)",
          textTransform: "uppercase",
          marginBottom: 6,
        }}
      >
        {eyebrow}
      </div>
      <h1 style={{ fontFamily: "var(--font-display)", fontSize: 24, margin: "0 0 6px 0", fontWeight: 600 }}>
        {title}
      </h1>
      <p style={{ fontSize: 13, color: "var(--color-muted)", margin: 0 }}>{description}</p>
    </div>
  );
}
