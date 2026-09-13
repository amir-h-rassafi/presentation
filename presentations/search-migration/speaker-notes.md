# Presenter notes and remaining facts

The slide changes are applied. Items below distinguish the explanation from facts
that still need Amir's confirmation; do not present unverified details as results.

## Confirm before presenting

- Deployment: Elastic Cloud Hosted, confirmed by Amir, chosen for greater control
  over index settings, shards, and replicas. Do not claim Serverless settings are immutable.
- Indexer: Amir confirmed one application partition/shard per worker (1:1).
  The total number was omitted. Ownership enforcement still needs confirmation.
  Elasticsearch primary shards are distinct from these application partitions.
  The supplied default-country script sets 3 primaries per index and 1 replica per
  primary outside DEV (0 in DEV). DE/FR have separate scripts; NZ is excluded.
- CDC: confirm append-only BigQuery mode, the actual cursor fields and ordering,
  how exceptionally late events are recovered, and how deletes are applied.
  SOURCE_TIMESTAMP + LSN + document ID must be an adequate stable cursor for the
  real source; do not assume it identifies every event uniquely without checking.
- Freshness: Amir confirmed 15 minutes was the accepted budget. Keep it explicitly
  labeled as a budget, not an observed delay or a completeness guarantee. Actual
  buffer/poll/queue intervals and late-event recovery remain unconfirmed. The
  supplied creation script sets refresh_interval to 300s; this is not a live export.
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

A partition is an application concept, not an Elasticsearch primary shard. Amir
confirmed a 1:1 partition-to-worker assignment; the total count is still missing.
Stable IDs make repeated document replacement avoid duplicates. Ordered processing
or version checks are still needed to prevent stale overwrites and stale deletes.
Confirm ownership enforcement and source sequence handling before asserting safety.

## Actual query supplied by Amir

Each country has its own index because languages and settings differ. The overall
analyzer approach is similar; this does not mean one language per country or identical
configuration everywhere. The generic companies/demo index name is illustrative.

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
name.ngram field in the demo mapping remain educational. Amir subsequently supplied
the default creation script: production mapping excerpts now use its analyzer names.
The standalone example-index.json and example-queries.http remain illustrative demo
assets, not production exports. The mapped production name.character_ngram field
is absent from the supplied six-clause query.

## Supplied default index script: configuration and caveats

- Country alias business_identity_{country} points to business_identity_{country}_1.
- Managed by Elastic; the script does not reveal node count, CPU, or RAM.
- Three primaries per default country index; one replica per primary outside DEV,
  zero in DEV. These do not establish indexer-worker count or checkpoint-index settings.
- Refresh is configured to 300s. Indexing acknowledgement is not search visibility;
  explicit refreshes or later changes to settings can alter observed timing.
- Prefix uses keyword tokenization, lowercase, ASCII folding, edge n-grams 3–20;
  search uses keyword_normalized. This is the start of the entire name, not each word.
  No 1–2-character prefix tokens are emitted; inputs beyond 20 characters are not
  truncated by the search analyzer. Other query clauses may still match.
- Main text uses standard tokenization; whitespace text adds a keyword-marker
  filter before stemming. Both configure country-specific stop and stem filters.
- Character n-grams use keyword tokenization and exactly 3 characters. Shingles
  use whitespace tokenization, 2–3-word shingles, and output_unigrams=true.
- sync_checkpoints maps last_business_identity_id, last_change_sequence_number,
  last_source_timestamp, source_table, status, target_index, and updated_at. Mapping
  alone does not prove cursor ordering, worker ownership, or exactly-once behavior.

Code-review caveats (not silently corrected; no live cluster contacted):

1. stopwords is generated as _english rather than the documented _english_
   (and likewise for other languages). Do not assume the intended stop list loads.
2. light_{language} is not universally supported: light_danish and light_dutch
   are not listed stemmer algorithms. Select a supported algorithm per language.
3. keyword_marker follows lowercase but protected terms are mostly mixed/uppercase,
   with ignore_case omitted (default false). Protection may therefore not apply as
   intended. The marker is only in the whitespace analyzer, not the main text analyzer.

References: [stop filter](https://www.elastic.co/docs/reference/text-analysis/analysis-stop-tokenfilter),
[stemmer algorithms](https://www.elastic.co/docs/reference/text-analysis/analysis-stemmer-tokenfilter),
[keyword marker](https://www.elastic.co/docs/reference/text-analysis/analysis-keyword-marker-tokenfilter),
[refresh](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/refresh-parameter).

[Boolean query scoring](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-bool-query)

## Prefix and shingles

“Analyzer issues with punctuation, such as a-m versus a m, motivated separate
representations. The prefix field supplies its own matching signal, with and without
fuzziness.”

search_as_you_type is a valid alternative: it supports configurable analysis and
creates shingle/prefix subfields automatically. Punctuation or long names alone
are not reasons it cannot work. If it was not evaluated, say so plainly.

“Word shingles are adjacent tokens: progema fastighets is a two-word example.
They supply an ordered phrase signal alongside individual words.”

Do not claim a measured shingle improvement without a comparison. A shingle match
can affect ranking; it does not guarantee a particular company will rank first.

## Freshness and architecture

“PostgreSQL remains the source of truth. Company search uses asynchronously
updated, country-specific Elasticsearch indexes. We accepted a fifteen-minute
freshness budget, which gave the indexing pipeline room for buffering.”

The diagrams describe Datastream events in an append-only BigQuery history, not
BigQuery merge-mode state application. Source-to-search delay can include CDC
delivery, the read buffer, polling/queues, indexing, and refresh. Do not attribute
the whole delay to Elasticsearch or claim measured stage timings without evidence.
Show the application still reading/writing transactional data in PostgreSQL.

## MRR and results

The result table reports MRR conditional on finding a relevant result within top k;
misses are excluded from that average and reported separately as Not found. Each
engine may have a different found-only subset. The definition slide illustrates
standard MRR (misses contribute zero), not the conditional result-table denominator.

“The first relevant result at rank 1 scores 1, at rank 2 scores one half, and absent
from the top 20 scores zero. Average across queries: this example gives MRR@20 0.50.”

Validation started with generated query variations using NLPAUG, then historical
customer-query replay. The precise augmenter configuration is not yet supplied;
do not claim specific augmentation operators or rates.

For backtesting, only the customer queries were taken from history, not the companies
customers selected in the funnel. Each query was run against both setups, and both
ordered top-20 lists were shared with a few domain experts. Experts voted for the
result list they expected/wanted to see. Blinding, randomization, reviewer count,
and vote aggregation are not yet confirmed. List preference does not provide the
per-result relevance labels needed to calculate MRR.

Use the same query set, relevance labels, and cutoff for any paired MRR evaluation.
The displayed human preference result
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

## Deployment research: do not overstate the restriction

Checked official Elasticsearch documentation. Serverless supports a subset of
settings and has an update-settings API: "settings cannot be updated in place" is
too broad. Static versus dynamic settings and analyzer definitions versus field
mappings are different things. On standard Elasticsearch, adding an analyzer to an
existing index uses a close/define/reopen workflow. Changing an existing field's
index-time analyzer through update-mapping is not supported; already indexed
terms are not retroactively rewritten. Reindexing may therefore still be required
on a managed cluster. Verify the exact alternative, setting, version, and operation
before presenting this as the reason for the deployment choice.

## Punctuation example

Tokenizer-only behavior, derived from official tokenization rules:
standard: a-m -> [a, m], a m -> [a, m]
whitespace: a-m -> [a-m], a m -> [a, m]
keyword: a-m -> [a-m], a m -> [a m]

The illustrative normalized keyword uses lowercase only, so it retains punctuation
and spacing. A production char filter or other normalization may erase that
distinction. The supplied OR-style query can match both forms through other clauses;
preserving a field representation does not guarantee different final results.
search_as_you_type accepts custom analysis, so this example alone does not establish
that the alternative could not work. No live production analyzer was tested.
Tokenizer-only _analyze requests have been added to the examples.

## References

- [Supported Serverless index settings](https://www.elastic.co/docs/reference/elasticsearch/index-settings/serverless)
- [Dynamic and static index settings](https://www.elastic.co/docs/reference/elasticsearch/index-settings)
- [Serverless update-settings API](https://www.elastic.co/docs/api/doc/elasticsearch-serverless/operation/operation-indices-put-settings)
- [Existing field analyzer restrictions](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/analyzer)
- [Standard tokenizer](https://www.elastic.co/docs/reference/text-analysis/analysis-standard-tokenizer)
- [Whitespace tokenizer](https://www.elastic.co/docs/reference/text-analysis/analysis-whitespace-tokenizer)
- [Keyword tokenizer](https://www.elastic.co/docs/reference/text-analysis/analysis-keyword-tokenizer)

- Selection scope: 11 initial options were filtered to three general-purpose
  full-text/fuzzy-search candidates. The restored comparison table describes this
  shortlist, not the entire initial pool. Amir supplied the initial list:
  Typesense, Elasticsearch, Meilisearch, Faiss, pgvector, Weaviate, Redis, Milvus,
  Qdrant, Pinecone, and Annoy.
  Evaluation covered clustering, full-text search, fuzzy search, data-size handling,
  ease of use, future vector search, community, deployment, PostgreSQL integration
  and ease of building a replica, typical use cases, and implementation languages.
  PostgreSQL integration was a criterion, not a claim that all tools offer native
  replication. Implementation language was context, not a performance benchmark.
  Its capability summary was checked in September 2026; it is not evidence that
  every feature was available in the evaluated versions at the time of selection.
- [Typesense HA and full-dataset replication](https://typesense.org/docs/guide/high-availability.html)
- [Typesense search weights and typo controls](https://typesense.org/docs/30.0/api/search.html)
- [Meilisearch Enterprise sharding and replication](https://www.meilisearch.com/docs/resources/self_hosting/sharding/overview)
- [Meilisearch ranking rules](https://www.meilisearch.com/docs/resources/internals/ranking)
- [Elasticsearch shard allocation](https://www.elastic.co/docs/deploy-manage/distributed-architecture/shard-allocation-relocation-recovery)
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
