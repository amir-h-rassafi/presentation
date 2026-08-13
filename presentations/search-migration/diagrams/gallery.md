# Mermaid Diagram Gallery

These diagrams are derived from the Medium article:
<https://medium.com/@amir.rassafi/running-search-from-postgresql-pg-trgm-to-elasticsearch-bm25-5e78f23a0a7b>

## 1. PostgreSQL Search Bottleneck

```mermaid
flowchart LR
  user[User name query]
  api[Search API]
  pg[(PostgreSQL<br/>25M records)]
  trgm[pg_trgm<br/>GIN / GiST index]
  cpu[Database CPU saturation]
  slow[~15s tail latency]

  user --> api
  api --> pg
  pg --> trgm
  trgm --> slow
  trgm --> cpu

  cpu -. a few concurrent requests .-> slow

  classDef client fill:#EAF2F8,stroke:#1F4E79,color:#1B2631
  classDef db fill:#FDEBD0,stroke:#C56B2C,color:#1B2631
  classDef risk fill:#FADBD8,stroke:#922B21,color:#1B2631

  class user,api client
  class pg,trgm db
  class cpu,slow risk
```

## 2. Target Architecture

```mermaid
flowchart LR
  pg[(PostgreSQL<br/>source of truth)]
  ds[GCP Datastream<br/>change capture]
  bq[(BigQuery<br/>append-only replica)]
  idx[Indexing service<br/>parallel workers]
  es[(Elasticsearch<br/>search index)]
  api[Search API]
  users[Users]

  pg -->|INSERT / UPDATE / DELETE| ds
  ds -->|CDC events + metadata| bq
  bq -->|lag-aware batches| idx
  idx -->|bulk UPSERT / DELETE| es
  users --> api
  api -->|name search| es

  bq -. debugging history .-> idx
  es -. same document ID as PostgreSQL row ID .-> pg

  classDef source fill:#EAF2F8,stroke:#1F4E79,color:#1B2631
  classDef stream fill:#E8F4F2,stroke:#2A7F78,color:#1B2631
  classDef search fill:#FDEBD0,stroke:#C56B2C,color:#1B2631
  classDef client fill:#F4F6F7,stroke:#5D6D7E,color:#1B2631

  class pg,bq source
  class ds,idx stream
  class es search
  class api,users client
```

## 3. Deterministic Indexer Sharding

```mermaid
flowchart TB
  bq[(BigQuery change rows)]
  router{Shard key<br/>hash(row_id)}

  w1[Worker 1<br/>shards 0-3]
  w2[Worker 2<br/>shards 4-7]
  w3[Worker 3<br/>shards 8-11]
  w4[Worker 4<br/>shards 12-15]

  es[(Elasticsearch)]

  bq --> router
  router --> w1
  router --> w2
  router --> w3
  router --> w4

  w1 -->|bulk writes| es
  w2 -->|bulk writes| es
  w3 -->|bulk writes| es
  w4 -->|bulk writes| es

  note[Deterministic routing keeps each record on a predictable path.]
  router -.-> note

  classDef data fill:#EAF2F8,stroke:#1F4E79,color:#1B2631
  classDef worker fill:#E8F4F2,stroke:#2A7F78,color:#1B2631
  classDef search fill:#FDEBD0,stroke:#C56B2C,color:#1B2631
  classDef note fill:#F4F6F7,stroke:#5D6D7E,color:#1B2631

  class bq data
  class w1,w2,w3,w4,router worker
  class es search
  class note note
```

## 4. Checkpoint And Replay Flow

```mermaid
sequenceDiagram
  autonumber
  participant I as Indexer worker
  participant ES as Elasticsearch
  participant BQ as BigQuery

  I->>ES: Read checkpoint
  ES-->>I: timestamp + LSN + document ID
  I->>BQ: Query newer rows behind safety lag
  BQ-->>I: Ordered change batch
  loop deterministic order
    I->>ES: UPSERT or DELETE using PostgreSQL row ID
  end
  I->>ES: Persist checkpoint after successful batch

  Note over I,ES: Crash recovery replays from the last checkpoint.
  Note over ES: Same document ID makes replay idempotent.
```

## 5. Name Index Design

```mermaid
flowchart TB
  name((name field))

  standard[Standard text<br/>BM25 ranking<br/>full-text behavior]
  keyword[Normalized keyword<br/>exact boost<br/>case + accent normalization]
  prefix[Prefix<br/>partial input<br/>autocomplete-like behavior]
  ngram[Character n-gram<br/>trigram-like fragments<br/>typo tolerance]
  shingle[Word shingle<br/>multi-word names<br/>phrase context]

  name --> standard
  name --> keyword
  name --> prefix
  name --> ngram
  name --> shingle

  query[Query time<br/>combine + weight signals]

  standard --> query
  keyword --> query
  prefix --> query
  ngram --> query
  shingle --> query

  classDef root fill:#1F4E79,stroke:#173B5C,color:#FFFFFF
  classDef field fill:#EAF2F8,stroke:#1F4E79,color:#1B2631
  classDef query fill:#FDEBD0,stroke:#C56B2C,color:#1B2631

  class name root
  class standard,keyword,prefix,ngram,shingle field
  class query query
```

## 6. Benchmark And Rollout

```mermaid
flowchart LR
  q[Historical queries]
  selected[Previously selected results]
  variants[Generated variations<br/>OCR errors, typos, partial names]
  old[PostgreSQL pg_trgm]
  new[Elasticsearch BM25 + analyzers]
  metrics[MRR and mismatch analysis]
  expert[Expert side-by-side review]
  decision{Quality acceptable?}
  rollout[Production rollout]
  tune[Tune analyzers and boosts]

  q --> old
  q --> new
  selected --> metrics
  variants --> old
  variants --> new
  old --> metrics
  new --> metrics
  metrics --> expert
  expert --> decision
  decision -->|yes| rollout
  decision -->|no| tune
  tune --> new

  classDef input fill:#EAF2F8,stroke:#1F4E79,color:#1B2631
  classDef system fill:#E8F4F2,stroke:#2A7F78,color:#1B2631
  classDef decision fill:#FDEBD0,stroke:#C56B2C,color:#1B2631
  classDef done fill:#E9F7EF,stroke:#1E8449,color:#1B2631

  class q,selected,variants input
  class old,new,metrics,expert,tune system
  class decision decision
  class rollout done
```
