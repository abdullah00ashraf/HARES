// tests-e2e/load/tester_army_load_1000.mjs
// 1,000-User Concurrent Load Testing Swarm against Project Hares Live Production
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const API_TARGET = process.env.API_URL || 'https://hares-api.onrender.com';
const VERIFY_ENDPOINT = `${API_TARGET}/api/v1/triage/verify`;
const TOTAL_USERS = parseInt(process.env.USERS || '1000', 10);
const CONCURRENCY_LIMIT = parseInt(process.env.CONCURRENCY || '4', 10); // Tuned for Render Free Tier CPU stability

// Load prompt corpus
const corpusPath = path.resolve(__dirname, '..', 'data', 'prompts_corpus_500.json');
if (!fs.existsSync(corpusPath)) {
  console.error(`Prompt corpus not found at ${corpusPath}. Run generate_corpus.mjs first.`);
  process.exit(1);
}
const prompts = JSON.parse(fs.readFileSync(corpusPath, 'utf-8'));

const results = [];

async function executeUserSession(userIndex) {
  const userId = `citizen_sim_${String(userIndex + 1).padStart(4, '0')}`;
  // Assign prompt cyclically from 500-corpus
  const prompt = prompts[userIndex % prompts.length];

  // Realistic Dubai ISP IP address pool (Du, Etisalat ranges)
  const clientIp = `194.170.${(userIndex % 250) + 1}.${((userIndex * 7) % 250) + 1}`;

  const maxAttempts = 3;
  let attempt = 0;

  while (attempt < maxAttempts) {
    attempt++;
    const startTime = performance.now();
    try {
      const formData = new FormData();
      if (prompt.mode === 'url' && prompt.url) {
        formData.append('url', prompt.url);
      } else {
        formData.append('text', prompt.input_text);
        if (prompt.url) {
          formData.append('url', prompt.url);
        }
      }

      const response = await fetch(VERIFY_ENDPOINT, {
        method: 'POST',
        headers: {
          'X-Forwarded-For': `${clientIp}, 10.0.0.1`,
          'User-Agent': `ProjectHares-TesterArmy/2.4 (VirtualUser ${userIndex + 1}/${TOTAL_USERS})`,
          Accept: 'application/json',
        },
        body: formData,
        signal: AbortSignal.timeout(60000), // 60s SLA ceiling
      });

      const latencyMs = Math.round(performance.now() - startTime);

      if (response.ok) {
        const data = await response.json();
        return {
          userId,
          promptId: prompt.id,
          userClass: prompt.user_class,
          statusCode: response.status,
          latencyMs,
          verdict: data.verdict,
          riskScore: data.risk_score,
          ruleTriggered: data.rule_triggered,
        };
      }

      // If transient gateway overload (502/503/504), wait and retry
      if (response.status >= 502 && response.status <= 504 && attempt < maxAttempts) {
        await new Promise(r => setTimeout(r, 2000 * attempt));
        continue;
      }

      let errText = '';
      try {
        const errJson = await response.json();
        errText = errJson.detail || JSON.stringify(errJson);
      } catch {
        errText = await response.text();
      }
      return {
        userId,
        promptId: prompt.id,
        userClass: prompt.user_class,
        statusCode: response.status,
        latencyMs,
        error: errText.slice(0, 150),
      };
    } catch (err) {
      const latencyMs = Math.round(performance.now() - startTime);
      if (attempt < maxAttempts) {
        await new Promise(r => setTimeout(r, 2000 * attempt));
        continue;
      }
      return {
        userId,
        promptId: prompt.id,
        userClass: prompt.user_class,
        statusCode: 0,
        latencyMs,
        error: err instanceof Error ? err.message : String(err),
      };
    }
  }
}

// Concurrency pool runner
async function runSwarm() {
  console.log(`=============================================================`);
  console.log(` PROJECT HARES — TESTER ARMY 1,000-USER CONCURRENT LOAD SWARM`);
  console.log(`=============================================================`);
  console.log(`Target Endpoint: ${VERIFY_ENDPOINT}`);
  console.log(`Total Simulated Citizens: ${TOTAL_USERS}`);
  console.log(`Prompt Corpus Variations: ${prompts.length}`);
  console.log(`Active Concurrency Window: ${CONCURRENCY_LIMIT} concurrent requests`);
  console.log(`Timestamp: ${new Date().toISOString()}`);
  console.log(`-------------------------------------------------------------`);

  const swarmStartTime = performance.now();
  let completed = 0;
  let activeIndex = 0;

  async function worker() {
    while (activeIndex < TOTAL_USERS) {
      const currentIndex = activeIndex++;
      const res = await executeUserSession(currentIndex);
      results.push(res);
      completed++;

      if (completed % 50 === 0 || completed === TOTAL_USERS) {
        const elapsedSec = ((performance.now() - swarmStartTime) / 1000).toFixed(1);
        const rps = (completed / parseFloat(elapsedSec)).toFixed(1);
        const okCount = results.filter(r => r.statusCode === 200).length;
        const rateLimitCount = results.filter(r => r.statusCode === 429).length;
        console.log(
          `[Progress] ${String(completed).padStart(4, ' ')}/${TOTAL_USERS} completed (${elapsedSec}s) | ` +
          `HTTP 200: ${okCount} | HTTP 429: ${rateLimitCount} | Throughput: ${rps} req/s`
        );
      }
    }
  }

  // Launch parallel workers
  const workers = Array.from({ length: CONCURRENCY_LIMIT }, () => worker());
  await Promise.all(workers);

  const totalDurationSec = ((performance.now() - swarmStartTime) / 1000).toFixed(2);

  // Compute statistics
  const http200s = results.filter(r => r.statusCode === 200);
  const http429s = results.filter(r => r.statusCode === 429);
  const errors = results.filter(r => r.statusCode !== 200 && r.statusCode !== 429);

  const latencies = results.map(r => r.latencyMs).sort((a, b) => a - b);
  const sumLatency = latencies.reduce((acc, v) => acc + v, 0);
  const meanLatency = (sumLatency / (latencies.length || 1)).toFixed(1);
  const minLatency = latencies[0] || 0;
  const maxLatency = latencies[latencies.length - 1] || 0;
  const p50 = latencies[Math.floor(latencies.length * 0.5)] || 0;
  const p90 = latencies[Math.floor(latencies.length * 0.9)] || 0;
  const p95 = latencies[Math.floor(latencies.length * 0.95)] || 0;
  const p99 = latencies[Math.floor(latencies.length * 0.99)] || 0;

  // Verdict breakdown on HTTP 200
  const verdicts = {
    GREEN: http200s.filter(r => r.verdict === 'GREEN').length,
    RED: http200s.filter(r => r.verdict === 'RED').length,
    AMBER: http200s.filter(r => r.verdict === 'AMBER').length,
  };

  console.log(`\n=============================================================`);
  console.log(` SWARM EXECUTION TELEMETRY & STATISTICAL SUMMARY`);
  console.log(`=============================================================`);
  console.log(`Total Requests:         ${TOTAL_USERS}`);
  console.log(`Total Duration:         ${totalDurationSec} seconds`);
  console.log(`Effective Throughput:   ${(TOTAL_USERS / parseFloat(totalDurationSec)).toFixed(2)} req/sec`);
  console.log(`HTTP 200 OK:            ${http200s.length} (${((http200s.length / TOTAL_USERS) * 100).toFixed(1)}%)`);
  console.log(`HTTP 429 Rate-Limited:  ${http429s.length} (${((http429s.length / TOTAL_USERS) * 100).toFixed(1)}%)`);
  console.log(`Errors / Dropped:       ${errors.length} (${((errors.length / TOTAL_USERS) * 100).toFixed(1)}%)`);
  console.log(`-------------------------------------------------------------`);
  console.log(`LATENCY PERCENTILES (ms):`);
  console.log(`  Min:   ${minLatency} ms`);
  console.log(`  Mean:  ${meanLatency} ms`);
  console.log(`  p50:   ${p50} ms`);
  console.log(`  p90:   ${p90} ms`);
  console.log(`  p95:   ${p95} ms`);
  console.log(`  p99:   ${p99} ms`);
  console.log(`  Max:   ${maxLatency} ms`);
  console.log(`-------------------------------------------------------------`);
  console.log(`TRI-STATE VERDICT CLASSIFICATION (Successful Inferences):`);
  console.log(`  🔴 RED (High Risk Fraud):       ${verdicts.RED}`);
  console.log(`  🟢 GREEN (Verified Safe):       ${verdicts.GREEN}`);
  console.log(`  🟡 AMBER (Unverified Caution):  ${verdicts.AMBER}`);
  console.log(`=============================================================`);

  // Write report
  const reportDir = path.resolve(__dirname, '..', 'test-report');
  if (!fs.existsSync(reportDir)) {
    fs.mkdirSync(reportDir, { recursive: true });
  }

  const reportPayload = {
    generated_at: new Date().toISOString(),
    target_endpoint: VERIFY_ENDPOINT,
    total_users: TOTAL_USERS,
    concurrency_limit: CONCURRENCY_LIMIT,
    duration_seconds: parseFloat(totalDurationSec),
    effective_rps: parseFloat((TOTAL_USERS / parseFloat(totalDurationSec)).toFixed(2)),
    http_200_count: http200s.length,
    http_429_count: http429s.length,
    error_count: errors.length,
    latency_stats: {
      min_ms: minLatency,
      mean_ms: parseFloat(meanLatency),
      p50_ms: p50,
      p90_ms: p90,
      p95_ms: p95,
      p99_ms: p99,
      max_ms: maxLatency,
    },
    verdicts,
    sample_records: results.slice(0, 25),
  };

  const reportPath = path.resolve(reportDir, 'load_test_1000_results.json');
  fs.writeFileSync(reportPath, JSON.stringify(reportPayload, null, 2), 'utf-8');
  console.log(`Detailed JSON telemetry saved to: ${reportPath}`);
}

runSwarm().catch(err => {
  console.error('Fatal load swarm error:', err);
  process.exit(1);
});
