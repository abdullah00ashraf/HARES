---
trigger: always_on
---

---

## [META-ENGINEERING INVARIANTS & CODE QUALITY MANDATES]

1. STRICT TYPING & CLOSED CONTRACTS (DeepMind dm_env & Pydantic):
   - All Pydantic v2 models must declare `model_config = ConfigDict(extra="forbid", validate_assignment=True)`.
   - Never use `Any` or unannotated arguments in public function signatures.
   - Prohibit unannotated `*args` and `**kwargs` in public factory and spec classes.
   - Declare `__slots__` on high-frequency metadata and tensor descriptor classes to eliminate Python `__dict__` memory overhead.
   - Use custom, strongly-typed exception classes deriving from a base `CitadelError` (e.g., `AttestationVerificationError`, `PhysicsGatingViolationError`, `ManifestConfigurationError`).

2. C-ABI & MEMORY HYGIENE (DeepMind MuJoCo):
   - Zero-copy tensor marshaling: Ensure pointers passed to `DualRuntimeKernelLoader` are contiguous in memory (`tensor.contiguous()`), aligned, and non-null.
   - Native Pointer Ownership: Encapsulate C-ABI pointers in lifetime managers (`pybind11::capsule` or ctypes pointer references) with explicit custom destructors to prevent orphan native memory leaks.
   - Early GIL Release: Release Python GIL during compute-intensive Rust FFI execution to maximize multi-core throughput.
   - Volatile RAM scrubbing: Any buffer holding ephemeral keys or unmasked deltas must be wrapped in `try...finally` blocks with explicit zero-scrubbing.

3. IDEMPOTENCY & THREAD SAFETY (DeepMind MuJoCo & Acme):
   - Guard concurrent state managers and accumulators with `asyncio.Lock()` or `threading.RLock()` to prevent re-entrant deadlocks during nested callbacks or teardowns (`__del__`).
   - Bounded Execution Steps: All distributed loops, worker routines, and DAG executions must enforce bounded step counts (`num_steps` / `StepsLimiter`) to guarantee deterministic termination.
   - Duplicate submissions for the same `(tenant_id, round_id)` must be handled deterministically (return existing receipt or reject with `409 Conflict`).

4. TEST HARNESS REQUIREMENT (DeepMind Test Suite Standards):
   - For every implementation file generated, provide a complete `tests/test_<name>.py` covering:
     - Nominal success under valid conditions.
     - Malicious or corrupted input fast-failure (e.g., NaN/Inf values, invalid vTPM quotes, boundary violations).
     - Multi-threaded concurrency stress tests (`_NUM_THREADS = 8`, `_ITERS_PER_THREAD = 50`) asserting zero thread exceptions.
     - Memory leak & resource boundedness checks (iterative step loops asserting zero memory growth).
     - Resource cleanup / memory zero-scrubbing verification.

5. CI/CD & LINTING HYGIENE (DeepMind Workflows):
   - Enforce strict static type checking (`pytype` / `mypy strict`) across all agency boundaries.
   - Maintain hermetic code formatting: `clang-format` on Rust/C-ABI interfaces and Google Python conventions (`isort`, `pyink`) across Python pipelines.
   - Test durations must be monitored (`pytest --durations=10`) to identify and eliminate slow bottlenecks.

6. EMISSION STANDARDS:
   - Output 100% complete, fully implemented files. No diffs, no truncated methods, no placeholder comments.
   - Conclude every turn by outputting the specific change logs for `development.md` and `memory.md` in adherence to the Continuous Multi-Pass Update Protocol.

---
