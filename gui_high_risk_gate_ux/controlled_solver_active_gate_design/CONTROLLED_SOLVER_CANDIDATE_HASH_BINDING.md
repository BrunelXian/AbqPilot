# Controlled Solver Candidate Hash Binding

- SHA256 is the supported algorithm.
- Candidate paths are read as bytes only when allowed.
- `.env`, ODB files, queue.json, live_status.json, runtime/reports, source sanity-base CAE, and source sanity-base INP are forbidden.
- Hash binding does not execute solver and does not create a solver request.
