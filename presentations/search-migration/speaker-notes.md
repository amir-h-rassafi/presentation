# Presenter notes and remaining facts

The slide changes are applied. Items below distinguish the explanation from facts
that still need Amir's confirmation; do not present unverified details as results.

## Confirm before presenting

- Deployment: exact hosting product and deployment type (Elastic Cloud Hosted,
  Serverless, or self-hosted). The supplied deck says 3 data nodes, 4 cores / 8 GB
  each, 3 primary shards, and one replica per primary, but does not name hosting.
- Indexer: actual partition count, worker-process count, ownership/lease mechanism,
  and whether one process hosts multiple partition loops. Earlier PDF and HTML
  diagrams disagreed; current slides use a conceptual N without inventing a count.
- CDC: confirm append-only BigQuery mode, the actual cursor fields and ordering,
  how exceptionally late events are recovered, and how deletes are applied.
  SOURCE_TIMESTAMP + LSN + document ID must be an adequate stable cursor for the
  real source; do not assume it identifies every event uniquely without checking.
- Freshness: was 15 minutes an observed figure, an acceptance budget, or both?
  What were the buffer, polling, queue, and refresh intervals? Was lag monitored?
  The slides describe accepted asynchronous freshness, not a guaranteed bound.
- Evaluation: actual PostgreSQL and Elasticsearch MRR@k values, k, query count,
  relevance labels, test snapshot, and date. No paired MRR results were supplied.
  The worked 0.50 example is educational, not a measured migration result.
- Human review: confirm sample size and method behind 50.6% Elasticsearch,
  29.4% both, and 20.0% PostgreSQL. These are the existing deck's figures.
- Prefix/shingles: was search_as_you_type tested? Was a shingle ablation measured?
  No unsupported comparison or measured improvement is claimed in the revision.
- Latency: confirm chart provenance, metric boundary (client/API/Elasticsearch
  took), aggregation, concurrency, hardware, and corpus snapshot. The existing
  CCDF has 5,263 observations per engine and an Elasticsearch tail above 1 second.
  It contradicts a universal 100 ms maximum. Raw time-series data were unavailable,
  so the faint screenshot was replaced by this existing comparison, not redrawn
  with fabricated measurements. Achieved throughput remains unreported.
- Selection: confirm the slide's scale, availability, and analyzer-control reasons
  reflect the historical decision. It no longer implies a scored benchmark.
- Timing: the original talk date remains May 2026. Confirm if the event date changed.

## Timestamp lag

“We leave a small buffer before reading the newest CDC window. Events can still
be in flight even when later timestamps are already visible. This trades freshness
for a lower risk of skipping late arrivals.”

Example: a five-minute buffer cannot protect against an event delayed ten minutes.
A fixed buffer is not a completeness guarantee. Explain the actual watermark,
overlap/reconciliation, or late-event recovery mechanism only after confirming it.
Do not say the buffer alone prevents lost rows.

## Checkpointing

“Each indexer partition resumes from its saved cursor, fetches an ordered batch,
writes it, and commits progress only after all relevant items succeed. If processing
fails before that commit, it resumes from the previous cursor.”

Inspect bulk item results, not only the HTTP status. An accepted write and a
search-visible document are different events: refresh controls visibility.
Permanent failures need explicit handling; do not silently checkpoint past them.

## Partition state machine

“One partition has one active owner and one ordered processing loop: read, fetch,
write, check, commit. Different partitions run independently.”

A partition is an application concept, not an Elasticsearch primary shard. A worker
process can host multiple loops; the diagram does not assert production counts.
Stable IDs make repeated document replacement avoid duplicates. Ordered processing
or version checks are still needed to prevent stale overwrites and stale deletes.
Confirm ownership enforcement and source sequence handling before asserting safety.

## Actual query supplied by Amir

The slides and request example preserve all six clauses and their original order:
normalized_keyword (term, boost 300), prefix (match, 40), prefix (fuzziness "1",
40), name (fuzziness "auto", 70), whitespace_tokenizer (match, 30), and word_shingle
(match, 10), with minimum_should_match = 1. The Python slide uses the query variable;
the HTTP example substitutes a company name for that variable.

Matching should-clause scores add. Both prefix clauses can contribute. These
boosts are weights, not guaranteed scores or a strict exact-first ordering. The
outer minimum_should_match requires one clause, not all words. No country filter,
must clause, AND operator, prefix_length, or max_expansions override is added.

No separate n-gram field is queried here. The earlier trigram query and the extra
name.ngram field in the demo mapping remain educational. Actual analyzer settings
have not been supplied: the demonstration's lowercase normalizer, tokenizers,
prefix lengths, and shingle settings are illustrative. The production query alone
cannot establish their configuration or ranking outcomes.

[Boolean query scoring](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-bool-query)

## Prefix and shingles

“A separate prefix field gives explicit control over prefix lengths and analysis,
with two separately scored clauses, one of them fuzzy.”

search_as_you_type is a valid alternative: it supports configurable analysis and
creates shingle/prefix subfields automatically. Punctuation or long names alone
are not reasons it cannot work. If it was not evaluated, say so plainly.

“Word shingles are adjacent tokens: progema fastighets is a two-word example.
They supply an ordered phrase signal alongside individual words.”

Do not claim a measured shingle improvement without a comparison. A shingle match
can affect ranking; it does not guarantee a particular company will rank first.

## Freshness and architecture

“PostgreSQL remains the source of truth. Company search uses an asynchronously
updated Elasticsearch index. Roughly fifteen-minute freshness was acceptable for
this use case.”

The diagrams describe Datastream events in an append-only BigQuery history, not
BigQuery merge-mode state application. Source-to-search delay can include CDC
delivery, the read buffer, polling/queues, indexing, and refresh. Do not attribute
the whole delay to Elasticsearch or claim measured stage timings without evidence.
Show the application still reading/writing transactional data in PostgreSQL.

## MRR and results

“The first relevant result at rank 1 scores 1, at rank 2 scores one half, and absent
from the top 20 scores zero. Average across queries: this example gives MRR@20 0.50.”

Use the same query set, relevance labels, and cutoff for both engines. Historical
clicks/selections can reflect position bias. The displayed human preference result
is separate from MRR: 50.6 + 29.4 = 80% preferred or tied. Do not relabel it as MRR
or ranking parity across the whole corpus. Add paired measured MRR only when available.

## Runnable illustration

example-index.json is a create-index request body for a disposable demonstration
index. example-queries.http contains Dev Tools requests; replace its demo index
name if needed. These are illustrative settings, not an export of production.

Run the create-index request manually with example-index.json, then the example
document and queries. No Elasticsearch cluster was contacted during this revision.

The prefix example uses 2–20 characters and preserves complete tokens. Partial
inputs longer than 20 characters still need a design decision. Lowercase-only
normalization does not fold accents or normalize whitespace/punctuation for exact
matches. The trigram analyzer emits no tokens for words shorter than three
characters; the other fields cover different signals. Standard tokenization is
illustrative: inspect real multilingual names with _analyze before adopting it.

## References

- [PostgreSQL trigrams and GiST/GIN query differences](https://www.postgresql.org/docs/current/pgtrgm.html)
- [Elasticsearch multi-fields](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/multi-fields)
- [Search as you type](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/search-as-you-type)
- [Edge n-gram filter](https://www.elastic.co/docs/reference/text-analysis/analysis-edgengram-tokenfilter)
- [N-gram filter](https://www.elastic.co/docs/reference/text-analysis/analysis-ngram-tokenfilter)
- [Shingle filter](https://www.elastic.co/docs/reference/text-analysis/analysis-shingle-tokenfilter)
- [Bulk item failures](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-bulk)
- [Read and write routing](https://www.elastic.co/docs/deploy-manage/distributed-architecture/reading-and-writing-documents)
- [Refresh and search visibility](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/refresh-parameter)
- [Datastream event delivery and ordering](https://docs.cloud.google.com/datastream/docs/events-and-streams?hl=en)
- [BigQuery destination modes](https://docs.cloud.google.com/datastream/docs/destination-bigquery)
