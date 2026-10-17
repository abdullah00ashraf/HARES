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
  model_engine?: string;
  triage_tier_evaluated?: "TIER_1_DETERMINISTIC" | "TIER_2_NEURAL_ZEROGPU" | "TIER_2_NEURAL_LOCAL" | "TIER_3_OFFLINE_FALLBACK" | string;
  tier_preemption_reason?: string | null;
  privacy_notice: string;
}

export interface DatabaseSyncTelemetry {
  engine: string;
  status: string;
  total_triage_audit_records: number;
  audits_last_24h: number;
  total_threat_indicators: number;
  total_threat_campaigns: number;
  official_allowlist_domains: number;
  last_db_entry_at: string;
  persistence_latency_p99_ms: number;
  zero_pii_compliance: string;
}

export interface SLMInferenceTelemetry {
  model_identifier: string;
  huggingface_repo: string;
  architecture: string;
  parameters_count: number;
  precision: string;
  decoding_engine: string;
  mean_inference_latency_ms: number;
  throughput_tokens_per_sec: number;
  social_engineering_accuracy: number;
  adversarial_prompt_injection_defense_rate: number;
  pydantic_schema_adherence_rate: number;
}

export interface AcousticDeepfakeTelemetry {
  pipeline: string;
  conformal_calibration: {
    method: string;
    alpha_significance: number;
    target_fpr_bound: string;
    empirical_fpr: string;
    conformal_threshold: number;
    tri_band_classification: string;
  };
  max_duration_seconds: number;
  codec_support: string[];
  synthetic_detection_f1: number;
  spoof_classification_latency_ms: number;
}

export interface DeterministicRadarTelemetry {
  exact_allowlist_engine: string;
  idn_homograph_detector: string;
  punycode_interception_rate: number;
  ocr_engine: string;
  rate_limiter: string;
}

export interface ModelMetricsResponse {
  timestamp: string;
  database_sync: DatabaseSyncTelemetry;
  slm_inference: SLMInferenceTelemetry;
  acoustic_deepfake: AcousticDeepfakeTelemetry;
  deterministic_radar: DeterministicRadarTelemetry;
  audit_distribution: {
    verdicts: Record<string, number>;
    payloads: Record<string, number>;
    avg_e2e_turnaround_ms: number;
  };
}

export interface GraphTraceStep {
  stepIndex: number;
  stageName: string;
  mitreTactic: string;
  mitreTechniqueId: string;
  activeNodeIds: string[];
  activeLinkIds: string[];
  description: string;
  riskRating: "CRITICAL" | "HIGH" | "MEDIUM" | "INFO";
}

export interface GraphSnapshot {
  id: string;
  timestamp: string;
  campaignId: string;
  campaignName: string;
  activeStep: number;
  tracedNodesCount: number;
  notes: string;
  sha256Digest: string;
}

export interface GraphSessionRecord {
  sessionId: string;
  startedAt: string;
  campaignName: string;
  eventsCount: number;
  snapshots: GraphSnapshot[];
  isRecording: boolean;
}

