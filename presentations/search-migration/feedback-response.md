# Concise feedback reply

Draft only; do not mark the pending facts below as fixed.

Thanks for the detailed feedback. One clarification: the original search used
pg_trgm, not pgvector.

1. Fixed—11-option pool, three-candidate shortlist, and comparison table clarified.
2. Fixed—split slides, padded trigrams, query example, and domain context.
4. Fixed.
5. Fixed—before/after roles added.
6. Managed by Elastic; deployment and index settings corrected.
7. Fixed.
8. One worker per indexer partition (1:1); total count pending.
9. Speaker notes added for lag, checkpointing, and partition ownership.
10. Elasticsearch multi-fields.
11. Analyzer differences such as a-m versus a m motivated separate field representations.
12. Fixed—analyzer assignments and a complete example mapping added.
13. Adjacent word tokens, e.g. “progema fastighets”.
14. Fixed.
15. Found-only MRR and Not found columns prepared; figures pending.
16. Fixed duration removed; the slide now explains the buffered CDC read without presenting it as an SLA or completeness guarantee.
17. Fixed—used the existing readable latency comparison.
18. Lessons slide removed.
19. PostgreSQL remains the source of truth; Elasticsearch serves country-specific search indexes.
20. Fixed.

Style: reduced density and standardized bullet punctuation.
