export interface OverviewKPIs {
  total_scanned_24h: number;
  high_risk_verdicts_24h: number;
  amber_fallbacks_24h: number;
  avg_latency_ms: number;
  total_class_a_iocs: number;
  sla_compliance_rate: number;
}

export interface TemporalDataPoint {
  time: string;
  text_volume: number;
  url_volume: number;
  audio_volume: number;
  total: number;
}

export interface ImpersonationEntity {
  entity: string;
  count: number;
  percentage: number;
  color: string;
}

export interface OverviewResponse {
  status: string;
  generated_at: string;
  kpis: OverviewKPIs;
  temporal_curve: TemporalDataPoint[];
  impersonation_distribution: ImpersonationEntity[];
}

export interface ThreatCampaign {
  id: string;
  name: string;
  lure_type: string;
  target_entity_spoofed: string;
  status: "active" | "monitoring" | "disrupted";
  total_submissions: number;
  first_detected_at: string;
  last_detected_at: string;
  indicator_count: number;
}

export interface ThreatIndicator {
  id: string;
  campaign_id: string | null;
  indicator_type: "url" | "domain" | "phone" | "bank_account" | "crypto_wallet";
  raw_indicator: string;
  normalized_value: string;
  verdict: "RED" | "AMBER" | "GREEN";
  risk_score: number;
  occurrence_count: number;
  first_seen_at: string;
  last_seen_at: string;
}

export interface HomographAlert {
  id: string;
  domain: string;
  is_punycode: boolean;
  spoofed_entity: string;
  technique: string;
  risk_score: number;
  occurrence_count: number;
  last_seen_at: string;
}

export interface TelemetryEvent {
  id: string;
  timestamp: string;
  payload_type: "text" | "url" | "audio_voice_note";
  verdict: "RED" | "AMBER" | "GREEN";
  rule_triggered: string;
  latency_ms: number;
  preview: string;
}

export interface ExtractedEntities {
  urls: string[];
  domains: string[];
  phone_numbers: string[];
  ibans: string[];
  crypto_wallets: string[];
}

export interface AllowlistMatch {
  verified_domain: string;
  entity_name: string;
}

export interface HomographAnalysis {
  is_spoof: boolean;
  domain: string;
  rule: string;
}

export interface SLMAnalysis {
  is_impersonation: boolean;
  detected_tactics: string[];
  confidence_score: number;
  urgency_or_coercion: boolean;
  financial_or_credential_demand: boolean;
  reasoning_summary: string;
}

export interface AudioAnalysis {
  is_synthetic: boolean;
  spectral_anomaly_score: number;
  p_value: number;
  is_abstaining: boolean;
  duration_seconds: number;
}

export interface TriageVerificationResponse {
  request_id: string;
  verdict: "RED" | "AMBER" | "GREEN";
  rule_triggered: string;
  reason: string;
  risk_score: number;
  escalation_url?: string | null;
  police_contact?: string | null;
  response_template_en: string;
  response_template_ar: string;
  extracted_entities: ExtractedEntities;
  allowlist_match?: AllowlistMatch | null;
  homograph_analysis?: HomographAnalysis | null;
  slm_analysis?: SLMAnalysis | null;
  audio_analysis?: AudioAnalysis | null;
  ocr_extracted_text?: string | null;
  input_type_detected: "text" | "url" | "audio" | "image";
  execution_latency_ms: number;
  privacy_notice: string;
}
