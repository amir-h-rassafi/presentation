# Search Migration Diagrams

Mermaid source diagrams for the presentation and article:

- `01-before-bottleneck.mmd` - PostgreSQL `pg_trgm` search bottleneck.
- `02-target-architecture.mmd` - PostgreSQL to BigQuery to Elasticsearch path.
- `03-indexer-sharding.mmd` - deterministic worker routing by shard key.
- `04-checkpoint-replay.mmd` - replayable checkpoint and write flow.
- `05-name-index-design.mmd` - multi-field Elasticsearch name index.
- `06-benchmark-rollout.mmd` - benchmark and production decision process.

Render one diagram with Mermaid CLI:

```sh
mmdc -i presentations/search-migration/diagrams/02-target-architecture.mmd \
  -o presentations/search-migration/diagrams/02-target-architecture.svg
```

GitHub Markdown can also render these directly inside fenced `mermaid` blocks.
