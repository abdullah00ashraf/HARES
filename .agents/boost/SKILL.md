---
name: boost
description: Multi-agent deep reasoning and rigorous verification pipeline for complex software engineering tasks, concurrency bugs, race conditions, intricate refactoring, and algorithmic optimizations.
---

# Boost Deep Reasoning Skill

This skill operationalizes the Antigravity Boost Multi-Agent Reasoning Pipeline within the workspace.

## Three-Phase Reasoning Pipeline

### Phase 1: Goal and Strategy Formulation
1. **Deconstruct Requirements:** Break down complex engineering challenges into discrete, verifiable subtasks.
2. **Map Invariants & Dependencies:** Identify architectural invariants, constraints, interfaces, and potential failure modes.
3. **Establish Verification Criteria:** Formulate explicit success assertions, unit tests, and performance benchmarks before writing production code.

### Phase 2: Parallel Execution & Verification Workstreams
1. **Implementation Workstream:** Construct modular, strongly-typed code conforming to closed contracts (`extra="forbid"`).
2. **Investigation Workstream:** Trace execution call graphs, verify memory lifecycles, and check boundary conditions.
3. **Local Isolated Verification:** Execute build targets and automated test suites (`pytest`, `cargo test`) after each modification to catch regressions early.

### Phase 3: Synthesis, Test Regression & Delivery
1. **End-to-End Regression Testing:** Run the full project test suite across all subsystems.
2. **Falsification & Adversarial Auditing:** Stress test edge cases (NaN/Inf, timeouts, attestation failures, concurrency race conditions).
3. **Continuous Documentation Sync:** Log all changes and decisions in `development.md` and `memory.md` in adherence to the Continuous Multi-Pass Update Protocol.
