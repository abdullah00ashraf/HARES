import { ThreatIndicator } from "./types";

export function generateStixBundle(indicators: ThreatIndicator[]): string {
  const bundleId = `bundle--${crypto.randomUUID()}`;

  const stixObjects = indicators.map((ind) => {
    let pattern = `[network-traffic:dst_ref.value = '${ind.normalized_value}']`;
    if (ind.indicator_type === "url") {
      pattern = `[url:value = '${ind.normalized_value}']`;
    } else if (ind.indicator_type === "domain") {
      pattern = `[domain-name:value = '${ind.normalized_value}']`;
    } else if (ind.indicator_type === "phone") {
      pattern = `[phone-number:value = '${ind.normalized_value}']`;
    } else if (ind.indicator_type === "bank_account") {
      pattern = `[bank-account:iban = '${ind.normalized_value}']`;
    }

    return {
      type: "indicator",
      spec_version: "2.1",
      id: `indicator--${ind.id}`,
      created: ind.first_seen_at,
      modified: ind.last_seen_at,
      name: `Hares Class A Indicator: ${ind.indicator_type}`,
      description: `Harvested via Dubai automated fraud triage. Verdict: ${ind.verdict}`,
      indicator_types: ["malicious-activity"],
      pattern: pattern,
      pattern_type: "stix",
      valid_from: ind.first_seen_at,
      confidence: Math.round(ind.risk_score * 100),
      labels: ["project-hares", "dubai-threat-feed", "class-a-ioc"],
    };
  });

  const bundle = {
    type: "bundle",
    id: bundleId,
    spec_version: "2.1",
    objects: stixObjects,
  };

  return JSON.stringify(bundle, null, 2);
}

export function generateCsvFeed(indicators: ThreatIndicator[]): string {
  const headers = [
    "id",
    "campaign_id",
    "indicator_type",
    "raw_indicator",
    "normalized_value",
    "verdict",
    "risk_score",
    "occurrence_count",
    "first_seen_at",
    "last_seen_at",
  ];

  const rows = indicators.map((ind) => [
    ind.id,
    ind.campaign_id || "",
    ind.indicator_type,
    `"${ind.raw_indicator.replace(/"/g, '""')}"`,
    `"${ind.normalized_value.replace(/"/g, '""')}"`,
    ind.verdict,
    ind.risk_score.toFixed(4),
    ind.occurrence_count,
    ind.first_seen_at,
    ind.last_seen_at,
  ]);

  return [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
}

export async function computeSha256(content: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(content);
  const hashBuffer = await window.crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}
