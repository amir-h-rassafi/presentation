# Search Migration Diagrams

Diagram sources for the presentation and article:

- `01-before-bottleneck.mmd` - PostgreSQL `pg_trgm` search bottleneck.
- `02-target-architecture.mmd` - PostgreSQL to BigQuery to Elasticsearch path.
- `03-indexer-sharding.tex` - vector chart for deterministic worker routing by shard key.
- `03-indexer-sharding.mmd` - Mermaid source for the simpler sharding diagram.
- `04-timestamp-lag-guardrail.tex` - vector chart for timestamp-lag guardrail behavior.
- `04-checkpoint-replay-clean.tex` - clean vector chart for replayable checkpoint and sharded write flow.
- `04-checkpoint-replay.tex` - earlier vector chart for replayable checkpoint and write flow.
- `04-shard-state-machine.tex` - vector chart for shard state ownership and uniqueness.
- `04-checkpoint-replay.mmd` - Mermaid source for the simpler checkpoint flow.
- `05-name-index-design.mmd` - multi-field Elasticsearch name index.
- `06-benchmark-rollout.mmd` - benchmark and production decision process.
- `07-human-ranking-evaluation.tex` - vector chart for expert ranking preferences.
- `08-latency-profile.tex` - vector chart for post-migration query latency.

Render one diagram with Mermaid CLI:

```sh
mmdc -i presentations/search-migration/diagrams/02-target-architecture.mmd \
  -o presentations/search-migration/diagrams/02-target-architecture.svg
```

GitHub Markdown can also render these directly inside fenced `mermaid` blocks.
