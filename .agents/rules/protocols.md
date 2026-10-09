---
trigger: always_on
---

---

trigger: always_on
---

---

## [CITADEL-CORE: DOMAIN-SPECIFIC ARCHITECTURAL MANDATES]

To maintain the sovereign, zero-trust integrity of the CITADEL-CORE engine, you must strictly adhere to the following project-specific engineering rules:

### 1. ZERO-COPY TELEMETRY & MEMORY PIPELINES (PyArrow & mlock)

* **The Rule:** Never use standard `pandas.read_csv()` or in-memory Pandas dataframes for high-frequency telemetry.
* **Implementation:** You must use `pyarrow.parquet` with memory-mapping (`memory_map=True`). All data ingress must route through the `ZeroCopyParquetStreamer` to prevent RAM bloat during 633M+ record fusions.
* **Security:** Client-side training buffers must be assumed to run under Linux `mlockall` (memory pinning). Do not write intermediate training states, gradients, or unencrypted weights to persistent disk.

### 2. PHYSICS-INFORMED NEURAL NETWORK (PINN) STABILITY

* **The Rule:** Never use standard Mean Squared Error (MSE) for hyperbolic equations (e.g., 2D SWE), as shockwaves will cause gradient explosion.
* **Implementation:** Always utilize the custom `LogCoshLoss` and `HydraulicLockLoss` manifolds.
* **Autograd Constraints:** When computing physics residuals via `torch.autograd.grad`, you must pass `create_graph=True, retain_graph=True, allow_unused=True`. Always check if the resulting gradient is `None` before applying continuity penalties, as coordinate disconnection is a common failure mode.

### 3. LANGGRAPH & MCP 2.0 MESH DETERMINISM

* **The Rule:** The control plane is a strictly deterministic 5-Wave DAG governed by MCP 2.0. Do not introduce non-deterministic LLM calls or unbounded loops into the round coordinator.
* **Implementation:** The `CircuitBreakerArbitrator` must strictly enforce the hierarchy: `security_attestation > convergence_delta > round_timeout`.
* **State Updates:** LangGraph state (`FederatedMeshState`) must be treated as an immutable `TypedDict`. State transitions must append or replace deterministically, avoiding race conditions during concurrent agency packet ingestion.

### 4. WILLOW PROTOCOL & CRYPTOGRAPHIC ISOLATION

* **The Rule:** Never write logic that attempts to decrypt the Willow payload outside of the Google Cloud Confidential Space TEE (via Oak Containers).
* **Implementation:** The gateway and control plane must treat `encrypted_masked_delta` and `encrypted_mask` as opaque Base64 strings.
* **HPKE Erasure:** Inside the enclave (`cfc_engine.py`), ephemeral Data Encryption Keys (DEKs) derived via HKDF must be zero-scrubbed from RAM immediately after the `MERGE` phase using deterministic context managers.

### 5. MANIFEST-DRIVEN TRUTH (No Hardcoding)

* **The Rule:** Never hardcode CRS (Coordinate Reference Systems like EPSG:32640), network graph nodes, or tenant IDs.
* **Implementation:** Every component must dynamically resolve its configuration by injecting the `ManifestLoader` (which parses `system_manifest.yaml`). If a tenant ID or physical parameter is not in the active manifest, the system must fast-fail.

### 6. NO PLAINTEXT LOGGING

* **The Rule:** Never log model weights, SCADA telemetry values, or attestation private keys.
* **Implementation:** Logging (via `logger.info` or OpenTelemetry sinks) must only capture structural metadata: round IDs, tensor shapes, $L_2$ norms, convergence deltas, and execution latencies.

### 7. C-ABI POINTER WRAPPER LIFECYCLE & CAPSULE HYGIENE (DeepMind MuJoCo Alignment)

* **The Rule:** Raw pointers passed across the Python/Rust C-ABI boundary (`DualRuntimeKernelLoader`) must never be held unmanaged or exposed naked without deterministic ownership and custom destructors.
* **Implementation:** FFI wrappers must track owner handles (via `pybind11::capsule` or ctypes pointer references) with explicit capsule destructors. All arrays passed across FFI must be validated for memory contiguity (`tensor.contiguous()`), memory alignment, and non-null pointers before dereferencing. Release the GIL early during pure Rust/C compute routines.

### 8. DISTRIBUTED WORKER DETERMINISM & BOUNDED ITERATION LIMITERS (DeepMind Acme Alignment)

* **The Rule:** Agentic execution loops, asynchronous worker actors, and LangGraph DAG transitions must enforce deterministic step counters and bounded iteration limits (`StepsLimiter` / iteration caps) to guarantee deadlock-free termination in both testing and production.
* **Implementation:** Decouple variable sources and state updates; actor-learner parameter exchanges must use explicit snapshotting (`get_variables`) to prevent state corruption during concurrent asynchronous packet staging. Observers and metrics collection must never mutate running environment or model state.

### 9. OUT-OF-CORE SPATIAL PIPELINE & GRAPH FINALIZATION (DeepMind AlphaFold Alignment)

* **The Rule:** High-dimensional spatial-temporal tensors and multi-gigabyte telemetry batches must be shape-introspected prior to allocation, and computational graphs must be finalized.
* **Implementation:**
  * Dynamic shape introspection (`eval_shape`) must precede buffer allocations for high-resolution 2D SWE meshes.
  * Drop all non-numeric Python `object_` pointers (`dtype != 'O'`) before tensor acceleration and FFI marshaling.
  * Asynchronous tensor operations across TEE boundaries must execute synchronization barriers (`block_until_ready()`) to prevent GPU/CPU memory race conditions.
  * Freeze computational graphs (`graph.finalize()`) to mathematically prevent memory leaks from graph mutation during long-running federated rounds.

### 10. RIGID SPECIFICATION CONTRACTS & VARARGS PROHIBITION (DeepMind dm_env Alignment)

* **The Rule:** Public boundary schemas, datapacket specifications, and tenant interface contracts must strictly prohibit unannotated `*args` and `**kwargs`.
* **Implementation:** All telemetry and parameter envelopes must declare explicit `shape`, `dtype`, and bounds specifications with a strict `.validate(value)` method. Performance-critical metadata holders and spec wrappers must define `__slots__` to eliminate Python dictionary overhead and prevent dynamic attribute pollution.

---

### 11. AIR-GAPPED ZERO-SAAS WEB INTERFACES & DECOUPLED CANVAS ENGINES

* **The Rule:** Real-time dashboards, operational HUDs, and web monitoring interfaces must be strictly 100% self-contained in static assets. Under no circumstances may code import or make network requests to external CDNs, third-party JavaScript libraries, external fonts (e.g. Google Fonts), or analytics beacons.
* **Implementation:**
  * All static assets must reside locally under `dashboard/static/` and execute in air-gapped environments without WAN connectivity.
  * Frame rendering must run decoupled at 60 FPS via `requestAnimationFrame` using native HTML5 Canvas, completely insulated from inbound WebSocket packet frequencies.
  * Audit feeds and UI queues must enforce fixed memory and DOM ring buffers (capped at 100 entries) with oldest-element recycling to prevent browser memory leaks during multi-day continuous operations.
  * Cryptographic Merkle inclusion verification must be executed natively in-browser via `window.crypto.subtle.digest("SHA-256", buffer)` without external npm or CDN dependencies.
  * WebSocket broadcasting from ASGI background tasks must be thread-safe, utilizing `asyncio.run_coroutine_threadsafe` across thread boundaries to prevent event loop deadlocks.

---

