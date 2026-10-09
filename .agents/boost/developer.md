# CITADEL-CORE: Boost Developer Guide & Domain Engineering Manifesto
### Master Invariants, Multi-Domain Specifications, and High-Assurance Coding Standards
**Repository Root:** `c:\Producttolaunch\CITADEL-DXB`  
**Governing Standard:** Antigravity Boost (`/boost`) Deep Reasoning Pipeline  
**Target Environments:** Python 3.11+ / Rust (C-ABI) / Google Cloud Confidential Space (Intel TDX & AMD SEV-SNP) / Web (HTML5/Canvas)

---

## 1. Executive Identity & The Boost Deep Reasoning Paradigm

The **`/boost`** protocol governs the development and maintenance of **CITADEL-CORE**—the Sovereign Confidential Federated Digital Twin Platform. Boost mandates rigorous, multi-agent deep reasoning over surface-level code generation.

### The Three-Phase Boost Engineering Hierarchy
1. **Phase 1: Goal & Strategy Formulation**
   - Deconstruct complex domain engineering challenges into discrete, verifiable subtasks before modifying production trees.
   - Formulate explicit mathematical, physical, and cryptographic invariants.
   - Specify closed interface contracts (`extra="forbid"`, no `*args` / `**kwargs`, typed boundary schemas).
2. **Phase 2: Parallel Isolated Execution & Local Verification**
   - Execute changes in modular, single-responsibility units.
   - Implement bit-accurate parity across dual runtimes (Rust C-ABI $\leftrightarrow$ Vectorized Python).
   - Run local test harnesses immediately after each component change (`pytest`, `cargo test`) to catch regressions before integration.
3. **Phase 3: Synthesis, Adversarial Falsification & Continuous Persistence**
   - Subject implementations to adversarial edge cases (corrupted vTPM quotes, NaN/Inf weight tensors, unphysical negative fluid depths, concurrent WebSocket packet flooding).
   - Validate full project test suites (zero test failures permitted).
   - Persist all design decisions, gotchas, and sprint achievements into `development.md` and `memory.md` in adherence to the Continuous Multi-Pass Update Protocol.

---

## 2. Meta-Engineering Invariants & Google DeepMind Code Alignment

All code authored in CITADEL-CORE must strictly adhere to invariants mined from Google DeepMind's flagship engineering codebases (`third_party/`):

### 2.1 Closed Specification Contracts (dm_env Alignment)
- **Prohibition of Varargs:** Never use unannotated `*args` or `**kwargs` in public API methods, schema models, or factory functions.
- **Strict Pydantic v2 Models:** Every Pydantic model must declare:
  ```python
  model_config = ConfigDict(extra="forbid", validate_assignment=True)
  ```
- **Memory Footprint Optimization:** High-frequency telemetry envelopes, tensor metadata, and proof step holders must declare `__slots__` or strict field types to eliminate dynamic Python dictionary overhead.

### 2.2 C-ABI & Memory Hygiene (MuJoCo Alignment)
- **Native Pointer Ownership:** Raw pointers passed across the Python/Rust FFI boundary (`DualRuntimeKernelLoader`) must be held in lifetime managers (`pybind11::capsule` or ctypes pointer references) with explicit custom destructors.
- **Zero-Copy Marshaling:** Arrays marshaled to C-ABI kernels must be validated for memory contiguity (`tensor.contiguous()`), memory alignment, and non-null pointers before dereferencing.
- **Early GIL Release:** Release the Python GIL during compute-intensive Rust FFI verification to maximize multi-core throughput inside the hardware enclave.
- **Volatile RAM Crypto-Erasure:** Memory buffers holding ephemeral keys or unmasked deltas must be explicitly overwritten with `b'\x00' * len(key)` via `try...finally` blocks.

### 2.3 Distributed Execution & Worker Determinism (Acme Alignment)
- **Decoupled Variable Sources:** Segregate telemetry generation (`Actor`), parameter updates (`Learner`), and variable sources (`VariableSource`).
- **Bounded Iteration Limiters:** Distributed loops, worker actors, and LangGraph DAG transitions must enforce deterministic step counters and bounded iteration limits (`StepsLimiter`) to guarantee deadlock-free termination.
- **Thread Safety:** State managers and accumulators must be guarded by `threading.RLock()` to permit recursive re-entrant locking during nested callbacks or error handling.

### 2.4 Spatial Pipelines & Graph Finalization (AlphaFold Alignment)
- **Dynamic Shape Introspection:** Dynamic shape introspections (`eval_shape`) must precede buffer allocations for high-resolution 2D SWE meshes.
- **Non-Numeric Pointer Sanitization:** Drop all non-numeric Python `object_` pointers (`dtype != 'O'`) before tensor acceleration and FFI marshaling.
- **Computational Graph Freezing:** Freeze computational graphs (`graph.finalize()`) to mathematically prevent memory leaks from graph mutations during continuous federated rounds.

---

## 3. Subjected Domain Invariants & Engineering Notices

Every component in CITADEL-CORE operates under specific physical and cryptographic domain mandates:

### Domain 1: Geospatial Hydrodynamics (2D Shallow Water Equations / Dubai Hydromet)
* **Coordinate Reference System:** Dynamic EPSG resolution via manifest (e.g. `EPSG:32640` for UTM Zone 40N Dubai).
* **Physical Governing Equations:**
  $$\frac{\partial h}{\partial t} + \frac{\partial (u h)}{\partial x} + \frac{\partial (v h)}{\partial y} = S(x, y, t)$$
* **Shock Stability Mandate:** Never use standard Mean Squared Error (MSE) for hyperbolic shallow water flow; shockwaves cause catastrophic gradient explosions.
* **Loss Manifolds:**
  - `LogCoshLoss`: Behaves as smooth $L_2$ for $|r| \ll 1$ and transitions asymptotically to linear $L_1$ with bounded derivative $\tanh(r) \in [-1, 1]$ for shock jumps.
  - `HydraulicLockLoss`: Exponential barrier penalty strictly preventing non-physical negative water depths ($h < 0$).
* **Exact Boundary Conditions:** Hard Dirichlet constraints enforced via normalized distance function $D(x, y)$ that identically evaluates to 0 on $\partial\Omega$ (`HardDirichletBoundary`).

### Domain 2: Electrical Power Grid SCADA (IEEE Bus Networks)
* **Topology:** Directed/undirected network graphs with buses (Slack/Generator, Load, Transmission) and transmission lines characterized by conductance $G$ and susceptance $B$.
* **Physical Governing Equations:** Non-linear AC Power Flow balance:
  $$P_i = V_i \sum_{j \in \mathcal{N}(i)} V_j \left(G_{ij} \cos(\theta_{ij}) + B_{ij} \sin(\theta_{ij})\right)$$
  $$Q_i = V_i \sum_{j \in \mathcal{N}(i)} V_j \left(G_{ij} \sin(\theta_{ij}) - B_{ij} \cos(\theta_{ij})\right)$$
* **Engineering Notice:** Voltage magnitudes must center near nominal $V \approx 1.0\text{ p.u.}$, with phase angles $\theta$ bounded within stable operating limits.

### Domain 3: Urban Highway Corridors (Macroscopic Traffic Flow)
* **Topology:** Multi-segment highway corridors modeling density $\rho(x, t)$ and flow rate $q(x, t) = \rho v(\rho)$.
* **Physical Governing Equations:** Lighthill-Whitham-Richards (LWR) conservation PDE:
  $$\frac{\partial \rho}{\partial t} + \frac{\partial (\rho v(\rho))}{\partial x} = 0$$
* **Greenshields Model:** Velocity decreases linearly with density: $v(\rho) = v_{\max}(1 - \rho/\rho_{\text{jam}})$. Shockwave formation occurs when incoming traffic exceeds bottleneck discharge capacity.

### Domain 4: Confidential Hardware Enclaves & Oak Containers
* **Hardware Attestation:** Intel TDX or AMD SEV-SNP running inside Google Cloud Confidential Space.
* **IETF RATS Verification:** Enclave quotes validated against DESC golden measurements (`configs/enclave/attestation_policy.json`) including container image SHA-256 digests.
* **Ephemeral HPKE Key Derivation:** Ephemeral Data Encryption Keys (DEKs) derived deterministically via HKDF from `(policy_id, node_id)`. Keys must only reside in volatile RAM with strict TTL expiration and guaranteed zero-scrubbing.
* **Zero-Plaintext Invariant:** Decryption strictly occurs inside the hardware enclave boundary. Model weights and raw SCADA data must **never** be logged, printed, or emitted outside the TEE.

### Domain 5: Willow Sublinear Secure Aggregation (CRYPTO 2025)
* **One-Shot Committee Masking:** Tenants apply additive homomorphic random pads: $\tilde{\Delta}_k = \Delta_k + M_k$.
* **Sublinear Unmasking:** Enclave computes $\sum \tilde{\Delta}_k - \sum M_k = \sum \Delta_k$, achieving $\mathcal{O}(1)$ committee aggregation without pairwise secret sharing.
* **Pre-Aggregation Gating:** Decrypted updates are validated against physical invariants ($L_2$ norm $C \le 10.0$ and differential residuals) via the C-ABI verification kernel **before** entering the aggregation pool.
* **Differential Privacy:** Calibrated Discrete Gaussian noise injected during finalization satisfying $(\epsilon, \delta)$-DP.

### Domain 6: Tamper-Evident Regulatory Audit Ledger (DESC ISR v2)
* **Database-Level Immutability:** SQLite Write-Ahead Logging (`WAL`) mode with `BEFORE UPDATE` and `BEFORE DELETE` triggers executing `SELECT RAISE(ABORT, ...)` (raising `sqlite3.IntegrityError`).
* **Linear Cryptographic Hash Chaining:** Every entry seals its predecessor:
  $$H_n = \text{SHA256}(n \parallel t \parallel \text{event\_type} \parallel \text{actor\_id} \parallel \text{system\_id} \parallel \text{payload} \parallel H_{n-1})$$
* **RFC 6962 Binary Merkle Trees:** $O(\log N)$ logarithmic inclusion proofs (`MerkleProofStep`) allowing independent client-side verification against published Merkle roots.

### Domain 7: Sovereign Operations Dashboard (Air-Gapped Real-Time Command Center)
* **Air-Gapped Zero-SaaS Guarantee:** 100% self-contained in `dashboard/static/`. Zero external CDN dependencies (no Google Fonts, no Tailwind CDN, no external scripts or icons).
* **60 FPS Decoupled Canvas Engine:** Frame rendering driven via `requestAnimationFrame` at 60 FPS, completely decoupled from incoming WebSocket packet frequency.
* **Memory-Bounded Ring Buffers:** Audit terminal DOM and memory feeds capped at exactly 100 entries with automatic oldest-entry recycling to prevent browser crashes during multi-day monitoring.
* **Native In-Browser Merkle Verification:** Cryptographic proof path validation executed locally in JavaScript via `window.crypto.subtle.digest("SHA-256", buffer)` with zero external crypto libraries.
* **Thread-Safe WebSocket Hub:** Background ASGI tasks dispatching broadcast events must use `dashboard_broadcaster.broadcast_sync(...)` via `asyncio.run_coroutine_threadsafe` to prevent thread-loop deadlocks.

---

## 4. Development & Testing Workflow Checklist

When implementing new features or refactoring existing modules under `/boost`:

1. **Schema First:** Declare strict Pydantic v2 models with `model_config = ConfigDict(extra="forbid", validate_assignment=True)`.
2. **Dual-Runtime Parity:** If writing native Rust C-ABI code in `physics_kernel/`, mirror the exact logic in Python vectorized fallback (`DualRuntimeKernelLoader`).
3. **Write Unit Tests First/In-Step:** Create `tests/test_<component>.py` covering:
   - Nominal success path.
   - Malicious/corrupted inputs (NaN/Inf, boundary overflows, invalid digests).
   - Pydantic `extra="forbid"` violation rejection.
   - Concurrency stress tests under multi-threaded load.
4. **Execute Verification:**
   ```powershell
   python -m pytest tests/test_<component>.py -v
   python -m pytest tests/ -v
   ```
5. **Continuous Documentation Sync:** Immediately append changelogs and architectural decisions to:
   - `development.md`
   - `memory.md`

---

## 5. Summary Matrix of Engine Invariants

| Invariant | Enforcement Mechanism | Failure Consequence |
| :--- | :--- | :--- |
| **Zero-Plaintext** | HPKE in TEE, Base64 ciphertexts on Gateway | Immediate sovereignty breach |
| **PINN Gradient Boundedness** | `LogCoshLoss`, `HydraulicLockLoss` | Gradient explosion on shock jumps |
| **Circuit Breaker Hierarchy** | `ArbitratorCircuitBreaker` (P1 > P2 > P3) | Byzantine corruption or sync deadlock |
| **Audit Immutability** | SQLite SQL triggers + linear SHA-256 chain | DESC ISR v2 regulatory revocation |
| **Air-Gapped Zero-SaaS** | 100% local assets in `dashboard/static/` | Data exfiltration via CDN beacons |
| **Thread-Safe WebSocket Hub** | `asyncio.Lock()` + `run_coroutine_threadsafe` | ASGI worker thread loop deadlocks |
| **Memory Boundedness** | 100-entry DOM ring buffer + `Float32Array` | Browser tab memory crash in 24/7 ops |
