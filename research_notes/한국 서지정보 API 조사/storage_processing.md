# 한국 서지정보 저장·가공: 아키텍처와 데이터 처리 기법 (2026-10 기준)

> Scope: how to store and process Korean book metadata aggregated from NLK 서지정보유통지원시스템(Seoji/ISBN), 도서관 정보나루, Kakao, Naver, and Aladin. API specifics (endpoints, quotas, fields) are covered by other researchers. These notes cover modeling, ISBN handling, merging, storage, pipelines, enrichment, and prior art.
>
> Citation convention: "[fetched]" means the page was retrieved and read this session. URLs marked "(canonical, not fetched this session)" point to well-known standard documents that were not re-verified. Treat their exact wording as unverified.

## 1. Data modeling: bibliographic models and a pragmatic relational schema

### Takeaway
All mature models split the abstract **work** from the concrete **edition/manifestation**: FRBR/LRM, BIBFRAME (Work/Instance/Item), Open Library (work/edition/author), and schema.org (`workExample`/`exampleOfWork`). ISBN identifies a manifestation, not a work. A Korean book DB should key `edition` rows by ISBN-13, attach a nullable `work_id` that is filled in later by clustering, and keep contributors, series/sets, classification, and raw payloads in separate tables.

### Cited Findings
- **Open Library** separates works (e.g., "Moby Dick") from editions. Editions link to works, and works link to authors, through record references (`/type/edition`, `/type/work`, `/type/author`). JSON schemas for the three types are in `openlibrary-client/olclient/schemata`. The official schema page is marked out of date and points to those client schemata. — [Open Library schema page](https://openlibrary.org/about/schema); [openlibrary-client schemata](https://github.com/internetarchive/openlibrary-client/tree/master/olclient/schemata)
- An Open Library dump-loading project stores the JSON in PostgreSQL **JSONB** across three tables (author, work, edition). It then extracts join tables such as `edition_work` and `work_author`. This "raw JSONB + extracted relations" pattern transfers directly to Korean sources. — [Bookdata-tools openlib doc (mirror)](https://www.dagshub.com/gopalsinghal/Bookdata-tools/src/master/docs/data/openlib.md)
- Each Open Library dump row has 5 columns: `type`, `key`, `revision`, `last_modified`, `JSON`. Every record therefore carries a revision and a last-modified timestamp, which serves as a built-in change-tracking model. [fetched] — [Open Library dumps](https://openlibrary.org/developers/dumps)
- **schema.org**: `workExample` is "an example/instance/realization of a work" (paperback, first edition, e-book), and its inverse is `exampleOfWork`. `Book` has the Text properties `bookEdition` and `isbn`. The official example nests one `Book` per edition, each with its own publisher, date, and ISBN, under a work via `workExample`. — [schema.org/workExample](https://schema.org/workExample); [bib.schema.org/exampleOfWork](https://bib.schema.org/exampleOfWork)
- **NLK set rule**: each volume of a set gets an individual ISBN (개별번호), and the set gets its own set ISBN (세트번호). Both come from consecutive serial numbers. The set's 부가기호 matches its volumes except that digit 2 changes from 3 to 4 (example: 03820 → 04820). The set's 부가기호 field is marked "(전 00권)" when the volume count is fixed, or "(세트)" when the count is open-ended or the set mixes media. Implication: model sets as a **separate entity linked many-to-many to editions**, not as a flag. [fetched] — [NLK 부가기호/ISBN 구성 안내](https://nl.go.kr/seoji/contents/S20101050000.do)
- Kakao book search does not return binding/format (제본형태). A developer request to add it on Kakao DevTalk notes that NLK's ISBN system distinguishes 종이책 and 전자출판물 (전자책, 오디오북). The format field therefore has to come from NLK (or be inferred from 부가기호 digit 2 = 5). — [Kakao DevTalk: 제본형태 추가요청](https://devtalk.kakao.com/t/topic/133442)
- The Korean National Bibliography holds over 4 million records, and its released national bibliographic metadata is available for reuse (IFLA profile, from a search snippet; the page returned 403 on fetch). — [IFLA: Korean National Bibliography](https://www.ifla.org/node/10970)
- Reference models (canonical, not fetched this session): BIBFRAME 2.0 Work/Instance/Item — [LoC BIBFRAME](https://www.loc.gov/bibframe/); IFLA LRM (successor to FRBR: Work–Expression–Manifestation–Item) — [IFLA LRM](https://www.ifla.org/g/bcm-rg/lrm/); KORMARC is the Korean MARC variant used by NLK — [NLK 서지표준](https://www.nl.go.kr/seoji/).

### Inferences
Pragmatic schema (PostgreSQL syntax; also maps to SQLite):

- `work(id, canonical_title, original_title, original_language, first_pub_year, cluster_confidence, created_at)`: optional, filled in by clustering. FRBR "expression" is folded in here or into `edition.translation_of_work_id`. For a small project, a separate expression table is over-engineering. Translations matter in Korea (9,663 translated titles in 2025, see §4), so add `edition.original_isbn` / `work.original_title` instead.
- `edition(isbn13 PK CHAR(13), isbn10, work_id NULL, title, subtitle, title_normalized, volume_label, edition_statement, publisher_id, pub_date DATE, pub_date_precision ENUM(day,month,year), page_count, size_cm, binding ENUM(paper,ebook,audio,mixed), ea_add_code CHAR(5), reader_code, form_code, content_code, kdc, ddc, price_list INT, language, status(active,out_of_print,…), first_seen_at, last_seen_at, updated_at)`.
- `contributor(id, name, name_normalized, name_hanja, name_original, birth_year, external_ids JSONB)` and `edition_contributor(isbn13, contributor_id, role ENUM(author,translator,illustrator,editor,photographer,original_author,…), role_raw TEXT, ordinal)`. Keep `role_raw` (지은이/글/그림/옮김/엮음/감수) for lossless round-tripping.
- `publisher(id, name, name_normalized, publisher_prefix TEXT)`. The prefix (발행자번호) is derivable from ISBN ranges, which makes it a strong publisher key.
- `set_isbn(set_isbn13 PK, title, total_volumes NULL, is_open_ended BOOL)` and `set_member(set_isbn13, isbn13, volume_no)`.
- `series(id, name, publisher_id)` and `edition_series(isbn13, series_id, series_no)`: 총서/시리즈 are not the same as 세트 ISBN.
- `subject(edition_isbn13, scheme(kdc|ddc|aladin_cat|kakao|nlk_subject|llm), code, label, source, confidence)`.
- `cover(isbn13, source, url, width, height, sha256, stored_key NULL, fetched_at)`.
- `price_observation(isbn13, source, price_list, price_sale, currency, observed_at)`: Aladin `priceSales` "can change at any time" (see §6), so keep it time-series, not on `edition`.
- `raw_payload(source, source_key, fetched_at, request_params JSONB, http_status, body JSONB/BLOB, body_sha256)`: the bronze layer.
- `field_provenance(isbn13, field, source, raw_value, chosen BOOL, observed_at)`: or a JSONB `provenance` column on `edition`. See §3.

### Gaps
- The exact NLK Seoji API response field list (EA_ADD_CODE, SET_ISBN, SET_ADD_CODE, KDC, etc.) was not verified this session. Searches did not surface the spec page; check with the API researcher's notes.
- No authoritative mapping from KORMARC tags to these columns was retrieved.

## 2. ISBN handling: conversion, validation, set vs individual, 부가기호 decoding, Korean prefixes

### Takeaway
Normalize everything to ISBN-13 (strip hyphens and spaces, validate the check digit). Store ISBN-10 only as a derived alias, and only for 978- numbers, because 979-11 has no ISBN-10. Decode the 5-digit 부가기호 into three columns (독자대상, 발행형태, 내용분류 KDC main class/division). Treat 발행형태 digit 2 = 4 as the set/series signal.

### Cited Findings
- Korean ISBN structure: prefix 978 or 979 (assigned by EAN International), then the group (country) code: **89 under 978** and **11 under 979**. Next comes a 2–6 digit publisher number assigned by the national ISBN center. The serial number fills the remaining digits so that publisher + serial = 7 digits, followed by 1 check digit. NLK says the check digit is computed automatically when an ISBN is applied for, but does not describe the method. [fetched] — [NLK ISBN 구성](https://nl.go.kr/seoji/contents/S20101050000.do)
- **부가기호 = 5 digits**: digit 1 = 독자대상기호, digit 2 = 발행형태기호, digits 3–5 = 내용분류기호 (KDC-based). In 내용분류, digit 3 is the KDC main class, digit 4 the division, and digit 5 is always 0. [fetched] — [NLK 부가기호](https://nl.go.kr/seoji/contents/S20101050000.do)
  - 독자대상: 0 교양 (general readers, specialized topics for non-specialists), 1 실용 (job, practical, adult exam prep), 4 청소년 (middle and high school, excluding 학습참고), 5 중·고등 학습참고서, 6 초등 학습참고서, 7 아동 (preschool and elementary, excluding 학습참고), 9 전문 (scholarly/professional). Codes 2, 3, 8 are unassigned on that page.
  - 발행형태: 0 문고본 (≤15 cm), 1 사전 (dictionaries and encyclopedias, any size), 2 신서판 (<18 cm), 3 단행본 (≥18 cm), 4 전집·총서·다권본·시리즈, 5 전자출판물 (PDF/EPUB/XML e-books, CD, DVD, CD-ROM), 6 도감, 7 그림책·만화, 8 혼합자료 (mixed media, braille, e-books on CD-ROM, microforms).
  - 내용분류 digit 3: 0 총류, 1 철학·심리·윤리, 2 종교, 3 사회과학, 4 자연과학, 5 기술과학, 6 예술, 7 언어, 8 문학, 9 역사·지리·관광. The full digit-4 subdivision lists are on the same page.
- Set vs individual: the set ISBN and its volume ISBNs are consecutive serial numbers, and the set's 부가기호 differs only in digit 2 (3→4). [fetched] — [NLK](https://nl.go.kr/seoji/contents/S20101050000.do)
- Algorithms (canonical, not fetched this session): the ISBN-13 check digit uses weights 1,3,1,3,… and check = (10 − Σ mod 10) mod 10. The ISBN-10 check uses weights 10..2, check = (11 − Σ mod 11) mod 11 with 10 = "X". 10→13 conversion prepends 978, drops the old check digit, and recomputes. Only 978-prefixed ISBN-13s can be converted back to ISBN-10. — [ISBN International Users' Manual](https://www.isbn-international.org/content/isbn-users-manual)

### Inferences
- Validation pipeline: `raw → strip [^0-9Xx] → if len 10: validate mod-11 → convert to 13 → validate mod-10 → reject/flag invalid`. Kakao's `isbn` field commonly packs "ISBN10 ISBN13" separated by a space (widely reported by developers; verify with the API notes). Split it, then prefer the 13-digit value.
- Korean-ness test: `isbn13 LIKE '97889%' OR '97911%'`. Hyphenation (where the publisher number ends) requires the ISBN International range file (RangeMessage.xml), not fixed offsets, because publisher numbers are 2–6 digits.
- 부가기호 is **publisher-declared and weakly controlled**, so treat it as a hint. Use digit 1 for audience facets (아동/청소년/학습), digit 2 for format (e-book = 5, comic/picture book = 7, set = 4), and digits 3–4 as a coarse KDC fallback when NLK has no KDC.
- Ready-made libraries exist in most languages (e.g., Python `isbnlib`, JS `isbn3`), but the logic is about 20 lines. Self-implementing avoids a dependency.

### Gaps
- I did not verify whether NLK's API exposes a separate set 부가기호 field, or how it encodes "(전 N권)" and "(세트)".
- Whether any 978-89 range is still being allocated in 2026, versus only 979-11, was not verified.

## 3. Entity resolution and merging across sources

### Takeaway
Use ISBN-13 as the hard join key across all five sources. Track provenance at the field level, and resolve conflicts with per-field source-precedence rules instead of per-record overwrite. Work-level deduplication (editions → work) is fuzzy and should be done offline with normalized-title + normalized-author blocking, then similarity scoring, with results stored separately from the source facts.

### Cited Findings
- NLK distinguishes paper books from electronic publications (e-books, audiobooks), and Kakao does not expose binding. Format precedence should therefore favor NLK and 부가기호. — [Kakao DevTalk](https://devtalk.kakao.com/t/topic/133442)
- Aladin `categoryId` is "one representative category" chosen from multiple internal classification systems. Store it as `scheme=aladin_cat` and do not treat it as KDC. `priceStandard` = 정가. `priceSales` = Aladin selling price, which can change at any time. [fetched] — [Aladin OpenAPI guide](https://www.aladin.co.kr/ttb/apiguide.aspx)
- Korean morphological analyzers (nori, mecab-ko-dic) split compounds in configurable ways: `none` keeps 가거도항 whole, `discard` (the default) gives 가곡역 → 가곡 + 역, and `mixed` keeps both. The same tooling is useful for title tokenization in dedup blocking. [fetched] — [Elastic nori_tokenizer](https://www.elastic.co/docs/reference/elasticsearch/plugins/analysis-nori-tokenizer)
- Bigram matching handles Korean particles: "대한민국" matches "대한민국은/의". Built-in `to_tsquery('simple','대한민국')` fails against "대한민국은". This argues for character n-gram similarity (bigram Jaccard or `bigm_similarity`) over word tokens when comparing Korean titles. [fetched] — [AWS 기술 블로그: Aurora pg_bigm + pgvector](https://aws.amazon.com/ko/blogs/tech/aurora-postgresql-pg-bigm-pgvector-korean-hybrid-search/)
- Unicode normalization forms NFC/NFKC (canonical, not fetched this session). NFC composes Hangul jamo sequences into precomposed syllables, which matters for text from macOS (NFD filenames) or pasted text. NFKC also folds full-width ASCII and compatibility characters such as ① and ㈜. — [UAX #15](https://unicode.org/reports/tr15/)
- Naver book search returns `title`/`author` with `<b>` highlight tags around matched terms. These must be stripped, and HTML entities unescaped, before storage (canonical, not fetched this session). — [Naver 책 검색 API](https://developers.naver.com/docs/serviceapi/search/book/book.md)

### Inferences
**Normalization recipe (apply to every text field before comparison; keep the raw value as well):**
1. HTML: strip tags (`<b>`, `</b>`) and `html.unescape` (Naver, sometimes Aladin descriptions).
2. Unicode: NFC for storage/display. Build a separate `*_normalized` key with NFKC, casefold, collapse whitespace, unify middle dots (· ・ ㆍ), unify brackets and quotes, and remove punctuation.
3. 한자 병기: titles like "논어(論語)" or authors like "홍길동(洪吉童)". Extract the parenthesized Han-script run into `name_hanja`/`title_hanja` with regex `\(([\p{Han}]+)\)`, and drop it from the comparison key. Lucene's `nori_readingform` filter (hanja→hangul reading) is an option inside ES (not verified this session).
4. Volume/edition markers: pull `제?\d+권`, `상/중/하`, `개정판`, `\d+판`, `특별판`, `리커버`, `(양장)` into `volume_label`/`edition_statement`, and remove them from the work-matching key.

**Author-string parsing** for NLK/Kakao/Aladin-style strings like `"홍길동 지음 ; 김철수 옮김"` or `"홍길동 글, 김영희 그림"`:
- Split responsibility statements on `;`, then split names within a statement on `,` / `·` / `&`. The trailing role word maps through a dictionary: 지음/지은이/저/글/著 → author, 옮김/옮긴이/역/譯 → translator, 그림/그린이/일러스트 → illustrator, 엮음/편/편저 → editor, 감수 → supervisor, 사진 → photographer, 원작 → original_author.
- Kakao returns `authors` and `translators` as separate arrays, which makes it the best source for translator splitting (verify in the API notes). Aladin packs everything into one `author` string with "(지은이), (옮긴이)" suffixes.
- Foreign names: keep the transliteration as the display name and add `name_original` when available (e.g., from Aladin `subInfo` or LLM extraction).

**Precedence rules (example default; make them configurable per field):**

| Field | 1st | 2nd | 3rd | Notes |
|---|---|---|---|---|
| title/subtitle | NLK | Aladin | Kakao/Naver | NLK is closest to the title page |
| contributors+roles | NLK (parsed) | Kakao arrays | Aladin string | |
| pub_date | NLK | Aladin (`pubDate`) | Kakao (`datetime`) | store precision |
| 부가기호/KDC/set ISBN | NLK only | 정보나루 (KDC) | — | |
| description/TOC | Aladin | Kakao `contents` (truncated) | Naver | licensing caveat, §6 |
| cover | Aladin Big | Kakao `thumbnail` | Naver `image` | |
| price (list) | NLK/Aladin `priceStandard` | Kakao `price` | | sale price → time series |
| loan popularity | 정보나루 | — | | |

- Implementation: a `merge(field, candidates[]) → (value, source)` function driven by a precedence table plus validity predicates (non-empty, valid date, not obviously truncated). Write the winner into `edition` and every candidate into `field_provenance`. Recompute from raw payloads at any time, so merge rules can change without re-fetching.
- **Edition → work clustering**: block on (`normalized_title_without_volume`, first-author normalized). Within each block, score with bigram Jaccard on titles plus exact original-title/ISBN-of-original matches. Auto-merge above a high threshold and queue the middle band for manual review. Sets, volumes (1권/2권), 개정판, and e-book versions of the same text all belong to the same work. Bilingual or translated editions belong to the same work only if the original-work identity is known.
- Never auto-merge across different ISBNs into a single edition. ISBN reuse by publishers (rare, but it happens) should be flagged when title similarity across sources for the same ISBN is very low.

### Gaps
- No Korean-specific published benchmark for book title deduplication was found.
- Whether NLK's API returns structured contributor fields, or only a 책임표시 string, was not verified.

## 4. Storage options, trade-offs, and data volume

### Takeaway
At Korean scale (roughly 65k print 신간/yr counted by 출협, a national bibliography of 4M+ records, and far more ISBNs once e-books are included), the data fits comfortably on one machine. **SQLite** works for personal use, **PostgreSQL + pg_bigm (+ pgvector)** is the sweet spot for a service, and **Elasticsearch/OpenSearch with nori** or **Meilisearch** is an optional search sidecar. The hard part is Korean search quality, not size.

### Cited Findings
**Volume**
- 출협 "2025년 기준 출판생산 통계" (published 2026-05-29) reports **64,491** new titles in the article body, or **64,991** in the subheadline and other outlets (a typo in one source; ±1.1% YoY), and 73,028,500 copies printed. Average list price ₩19,897 (+1.9%). Translated titles: 9,663 (−5.8%, the first year under 10k in a decade). 5,766 publishers submitted (납본) to 출협, out of 85,689 registered publishers. Share of titles: 문학 22.4%, 사회과학 18.9%, 아동 12.3%, 기술과학 10.7%, 만화 8.5%. Basis: books deposited with 출협 only, so this undercounts total ISBNs. [fetched] — [Newsis 2026-05-29](https://www.newsis.com/view/NISX20260529_0003649654); conflicting figure 6만4991 in [아시아경제](https://view.asiae.co.kr/article/2026052916413614584), [헤럴드](https://www.heraldk.com/article/2026052919351768803)
- In a study of 2012–2022 electronic publications, **e-books account for 96.2% of ISBNs issued** for e-publications, with issuance peaking in 2020–2022. ISBN-assigned online materials must be deposited (납본) with NLK within 30 days under 도서관법 §21, but top issuers' deposit rates are low. — [KBIBLIA journal 35(1):127](https://www.accesson.kr/kbiblia/assets/pdf/42257/journal-35-1-127.pdf)
- Korean National Bibliography: over 4 million records (IFLA snippet). — [IFLA](https://www.ifla.org/node/10970)
- NLK publishes quarterly 발행자번호 배정내역 (publisher-number assignments; the latest file is 2026 Q2) as open data. I could not open the file this session. — [NLK 정보공개 목록](https://nl.go.kr/NL/contents/N50803050000.do)
- For comparison, Open Library's global dumps: editions about 9.2 GB compressed, works about 2.9 GB, authors about 0.5 GB, all types about 12.4 GB, generated monthly. [fetched] — [Open Library dumps](https://openlibrary.org/developers/dumps)

**SQLite / FTS5**
- The FTS5 trigram tokenizer matches arbitrary substrings. Query substrings **shorter than 3 Unicode characters match no rows**, and LIKE/GLOB patterns without a run of 3+ non-wildcard characters fall back to a full table scan. Options: `case_sensitive`, `remove_diacritics`. Custom tokenizers are pluggable via `xCreateTokenizer_v2`. [fetched] — [SQLite FTS5](https://sqlite.org/fts5.html)
- unicode61 treats L*/N* category characters as token characters and everything else as separators. Hangul runs therefore become whole space-delimited eojeol tokens with particles attached ("대한민국은"), so prefix queries (`대한민국*`) are needed (inference from the documented rules). — [SQLite FTS5](https://sqlite.org/fts5.html)

**PostgreSQL**
- pg_bigm is a 2-gram GIN index (`gin_bigm_ops`) for LIKE/similarity on CJK text without a dictionary. It is supported on Amazon RDS since 2021-04 and on Aurora PostgreSQL ≥12.9. On 100k Korean Wikipedia docs, "대한민국" returned 27,846 docs with pg_bigm vs 14,465 with tsvector, and across 100 everyday words pg_bigm found about 304% more matches. The hybrid design ranks pg_bigm (`bigm_similarity`, title weighted ×2) together with pgvector HNSW (`vector_cosine_ops`, m=16, ef_construction=128, ef_search 100–200) through RRF (k=60, weights 0.4 keyword / 0.6 semantic). [fetched] — [AWS 기술 블로그](https://aws.amazon.com/ko/blogs/tech/aurora-postgresql-pg-bigm-pgvector-korean-hybrid-search/); [pg_bigm GitHub](https://github.com/pgbigm/pg_bigm); [AWS What's New 2021](https://aws.amazon.com/about-aws/whats-new/2021/04/amazon-rds-for-postgresql-supports-pg-bigm-extension-for-faster-full-text-search)
- Built-in tsvector with the 'simple' config does not handle Korean particles (`to_tsquery('simple','대한민국')` misses "대한민국은"). — [AWS 기술 블로그](https://aws.amazon.com/ko/blogs/tech/aurora-postgresql-pg-bigm-pgvector-korean-hybrid-search/)
- Morphological alternatives inside PostgreSQL: textsearch_ko (mecab-ko, ships as a Docker image), the `kor_search` PGXN extension (claims Korean/English search without external APIs and RDS compatibility), and PGroonga. — [postgres-textsearch_ko Docker](https://hub.docker.com/r/karoid/postgres-textsearch_ko); [kor_search on PGXN](https://pgxn.org/dist/kor_search/doc/kor_search.html); [Mattermost CJK search guide](https://docs.mattermost.com/administration-guide/configure/enabling-chinese-japanese-korean-search)

**Search engines**
- Elasticsearch `analysis-nori` is a plugin wrapping the Lucene nori module, using the mecab-ko-dic dictionary. It must be installed on every node, followed by a restart. Tokenizer options: `decompound_mode` (none / discard [default] / mixed), `discard_punctuation` (default true), `user_dictionary` or inline `user_dictionary_rules` (custom NNG nouns with optional segmentation), and `lenient`. Tokens carry posType, leftPOS, rightPOS, morphemes, and reading attributes for downstream filters. [fetched] — [Elastic nori plugin](https://www.elastic.co/docs/reference/elasticsearch/plugins/analysis-nori); [nori_tokenizer](https://www.elastic.co/docs/reference/elasticsearch/plugins/analysis-nori-tokenizer)
- Meilisearch (Charabia tokenizer) lists Korean as dedicated support with **"lindera KO dictionary segmentation"** plus decomposition-based normalization. Korean support was added by a community contributor in v1.0. One older docs page groups Korean only under non-Latin scripts, so the docs are somewhat inconsistent. [fetched] — [Meilisearch language support](https://www.meilisearch.com/docs/learn/resources/language); [Meilisearch v1.0 blog](https://blog.meilisearch.com/whats-new-in-v1-0/)

### Inferences
| Option | Fit | Korean search | Pros | Cons |
|---|---|---|---|---|
| SQLite + FTS5 | personal / CLI / static site | trigram (≥3 chars) or unicode61 + prefix. 2-char Korean words (e.g., "역사", "철학") **can't use the trigram index**: workaround is an extra bigram column or LIKE scan | zero-ops, single file, easy backup, ships with Python | single writer, weak Korean ranking |
| DuckDB + Parquet | bronze/silver lake, analytics, one-off dedup jobs | none built-in | reads JSON/CSV/Parquet directly, great for re-deriving silver from bronze, columnar compression | not an OLTP store |
| PostgreSQL + JSONB + pg_bigm (+pg_trgm, +pgvector) | small team / production default | bigram LIKE/similarity, good recall, no dictionary; add pgvector for semantic search | one system for raw, normalized, search, and vectors; available on RDS/Aurora | ranking is cruder than BM25 with morphology; pg_bigm availability varies by host |
| Elasticsearch/OpenSearch + nori | production search with facets | best morphological analysis, user dictionary for 신조어/고유명사, BM25 | facets, highlighting, synonyms | JVM ops burden, second source of truth to sync |
| Meilisearch | small-team instant search | lindera ko-dic | trivial ops, typo tolerance, good DX | less tunable Korean analysis |
| Typesense | similar to Meilisearch | not verified | | Korean support not verified (gap) |

- **Size estimate (inference)**: 4M bibliographic rows at about 2–5 KB normalized each is 8–20 GB of heap. Adding raw JSON payloads from 3–5 sources per ISBN multiplies that by about 3–5. Compressed in Parquet/zstd, this is small. Even "all Korean ISBNs ever" fits on a single small Postgres instance or one SQLite file in the tens of GB. Covers are the dominant storage cost if copied (roughly 4M × 50–150 KB ≈ 200–600 GB at Big size).
- Hosted options (not fetched this session; check current limits). Supabase is managed Postgres with pgvector and pg_trgm; check whether pg_bigm is on its extension list (gap). Cloudflare D1 is SQLite-based, so FTS5 limits apply. Cloudflare R2 has no egress fees and suits the bronze payload archive and cover copies. Turso/libSQL is SQLite-compatible and embedded-replica friendly.

### Gaps
- No authoritative annual ISBN-assignment count (including e-books) from NLK was retrieved. The 2026 Q2 publisher-number file was not opened. The 출협 count (~65k) covers print books deposited with 출협 only, so total ISBN issuance including e-books is likely several times higher, but **no verified figure** was found.
- Supabase/Neon pg_bigm availability, D1/Turso FTS5 tokenizer specifics, Typesense Korean handling, and the OpenSearch nori bundling status were not verified this session.

## 5. Pipeline design: bronze/silver/gold, idempotency, incremental harvest, orchestration

### Takeaway
Store every API response verbatim (bronze), derive normalized editions deterministically from bronze (silver), and build search/aggregate views on top (gold). Make every step idempotent: keys are (source, source_key, content hash), and writes are upserts. Harvest incrementally by publication-date windows from NLK, enrich per ISBN from commercial APIs under per-source rate-limit budgets, and start orchestration with cron or GitHub Actions.

### Cited Findings
- Open Library's model of full JSON per record plus `revision` and `last_modified`, released as monthly dumps (with separate `redirects` and `deletes` dumps), is a proven change-tracking pattern: merges become redirects, and removals become explicit tombstones. [fetched] — [Open Library dumps](https://openlibrary.org/developers/dumps)
- DuckDB can query the Open Library compressed TSV dumps directly with `read_csv` and pull fields with `json_extract`. This is the "query bronze in place" pattern. [fetched] — [Open Library dumps](https://openlibrary.org/developers/dumps)
- Aladin OpenAPI: 5,000 calls/day cap (contact ttb@aladin.co.kr for more). Output is XML (default) or JSON. Lookups by itemId or ISBN. (The guide is dated 2007-09-01, so verify current terms.) [fetched] — [Aladin OpenAPI guide](https://www.aladin.co.kr/ttb/apiguide.aspx)
- Bulk-load tip for Postgres indexing: temporarily raise `maintenance_work_mem` during bulk loads before building GIN/HNSW indexes. [fetched] — [AWS 기술 블로그](https://aws.amazon.com/ko/blogs/tech/aurora-postgresql-pg-bigm-pgvector-korean-hybrid-search/)

### Inferences
- **Bronze**: `raw_payload(source, endpoint, source_key, request_params, fetched_at, status, body, body_sha256)`. Append-only. Skip the insert when `body_sha256` is unchanged for the same key, and only bump `last_seen_at`. Store it as JSONB in Postgres, or as gzipped JSONL/Parquet partitioned by `source/date=YYYY-MM-DD/` in local disk or R2/S3. This allows merge-logic changes without re-calling rate-limited APIs.
- **Silver**: a pure function `normalize(source, body) → candidate rows` plus `merge(candidates) → edition`. Run `INSERT … ON CONFLICT (isbn13) DO UPDATE … WHERE edition.content_hash IS DISTINCT FROM excluded.content_hash` so unchanged rows aren't rewritten (Postgres; SQLite supports the same UPSERT syntax).
- **Gold**: a search index (pg_bigm/FTS/ES), work clusters, and category rollups. Rebuild them fully when cheap.
- **Harvest strategy** (inference):
  1. *Discovery*: NLK Seoji by publication-date window (e.g., daily windows over the past N days, re-scanned with overlap because 납본/registration lags), plus 정보나루 new-arrival/popularity lists. These give the ISBN universe.
  2. *Enrichment queue*: a per-ISBN job table `(isbn13, source, status, attempts, next_attempt_at, last_error)`. A worker pulls jobs subject to per-source token buckets (e.g., Aladin ≤5,000/day; Kakao/Naver quotas per the API notes).
  3. *Refresh policy*: re-fetch volatile fields (price, status, covers) on a decaying schedule: weekly for recent titles, monthly or quarterly for old ones. Bibliographic core is re-fetched rarely.
  4. *Retry*: exponential backoff with jitter on 429/5xx, cap the number of attempts, dead-letter after that. Respect `Retry-After`. Treat "0 results" as a valid cached negative with a TTL, not an error.
- **Change tracking**: either an `edition_history` table (SCD type 2: valid_from/valid_to) or simply diffing successive bronze payloads by hash. Model merges as redirects and removals as tombstones, as Open Library does.
- **Orchestration ladder**:
  - Personal: cron/launchd + one Python script + SQLite. Or GitHub Actions scheduled workflow, committing a SQLite/Parquet artifact, or pushing to R2. Watch Actions' run-time limits and the secret handling for API keys.
  - Small team: a single worker container plus a Postgres job queue (e.g., `SELECT … FOR UPDATE SKIP LOCKED`), scheduled by cron.
  - Production: Dagster (asset-oriented, maps naturally onto bronze/silver/gold "assets" with partitions by date and source), Prefect (lightweight Python flows), or Airflow (heaviest). Choose only if there are many sources, backfills, and the need for lineage UI.

### Gaps
- No Korean-specific published case study of a bronze/silver/gold book pipeline was found.
- Current Kakao/Naver/NLK/정보나루 quotas were not verified here (other researchers' scope).

## 6. Enrichment: covers, embeddings, LLM classification, KDC→category mapping

### Takeaway
Hotlink covers by default and cache them only under explicit terms. Licensing for covers and descriptions is unclear in the public API guides found. Embeddings (title + description + subjects) in pgvector or Meilisearch hybrid search add semantic search cheaply. A KDC main class/division (from NLK, 정보나루, or the 부가기호 digits 3–4 fallback) gives a deterministic baseline category tree, with LLM classification only for gaps.

### Cited Findings
- The Aladin OpenAPI guide offers cover sizes via `Cover=Big|Mid(default)|Small|Mini|None`, returns a `cover` URL and a `link` to the item page, but **states no rules** on cover reuse, attribution, commercial use, or caching (the page dates from 2007). [fetched] — [Aladin OpenAPI guide](https://www.aladin.co.kr/ttb/apiguide.aspx)
- A web search for Aladin cover-image licensing terms returned nothing relevant. — (search, no usable source)
- 부가기호 digits 3–4 encode a KDC-based class/division (digit 3: 0 총류 … 9 역사), which serves as a fallback classification for every Korean ISBN even without a cataloged KDC. [fetched] — [NLK 부가기호](https://nl.go.kr/seoji/contents/S20101050000.do)
- Hybrid search recipe: Titan Embeddings V2 (1024-d) + pgvector HNSW, fused with pg_bigm via RRF. Chunk long text at 500–1,000 characters. [fetched] — [AWS 기술 블로그](https://aws.amazon.com/ko/blogs/tech/aurora-postgresql-pg-bigm-pgvector-korean-hybrid-search/)
- Meilisearch supports hybrid search with a multilingual embedder plus localized attributes for multilingual datasets. [fetched] — [Meilisearch language](https://www.meilisearch.com/docs/learn/resources/language)

### Inferences
- **Covers**:
  - *Hotlink*: zero storage, but URLs break, CDNs may block referers, and you depend on the vendor.
  - *Copy*: stable and allows resizing (WebP/AVIF), but cover art is copyrighted by publishers or designers.
  - Middle ground: store the URL and sha256, proxy-cache with a TTL, and copy only for personal/non-public use.
  - Cover images are generally copyrighted works. Using them in a public service relies on API terms or publisher permission. Get legal confirmation before copying at scale.
  - Prefer sources whose terms explicitly allow display with a link-back. NLK-provided cover images (if the API supplies them) may have clearer public-sector terms (verify).
- **Descriptions/TOC** from commercial vendors (Aladin/Kakao/Naver) are vendor- or publisher-authored text with the same licensing caveats. Keep them in bronze, and gate their display on terms. LLM-generated summaries derived from them are a gray area.
- **Embeddings**: embed `title + subtitle + authors + KDC label + description[:N]` per edition, then average or take the representative per work. Store a model-name/version column so the index can be rebuilt. Multilingual models that handle Korean (e.g., OpenAI text-embedding-3, Cohere multilingual, BGE-M3, multilingual-e5) all work. Pick by cost and self-hostability (not benchmarked here).
- **LLM tasks** worth automating: author-string parsing fallback when regex fails, original-title/original-author extraction for translations, audience/genre tagging, KDC suggestion for missing KDC (validate against the 부가기호 digit 3 class), and dedup adjudication for mid-confidence pairs. Always store the outputs as `source='llm:<model>'` with a confidence score, never overwriting authoritative fields.
- **KDC→category mapping**: maintain a small table `kdc_prefix → app_category`. For example, 8xx 문학 splits by digit 2 into 81x 한국문학 … and 89x 기타 문학; 아동 is detected via 부가기호 digit 1 = 7, not KDC; 만화 via 부가기호 digit 2 = 7 or KDC 657 (verify the KDC edition). Bridge to Aladin categories with an observed co-occurrence mapping (count KDC × Aladin categoryId over ISBNs that have both).

### Gaps
- Explicit, current cover and description reuse terms for Aladin/Kakao/Naver were not found in the sources fetched.
- Whether NLK Seoji provides cover images (and under which license, e.g., 공공누리 type) was not verified.
- No published KDC↔Aladin category crosswalk was found.

## 7. Open-source prior art

### Takeaway
Public Korean prior art consists mostly of **thin API clients and plugins** (Obsidian plugins, MCP servers) built on Aladin or Kakao. I found no open-source, multi-source Korean book database with entity resolution. Open Library remains the best architectural reference: work/edition/author split, revisions, redirects, and monthly dumps.

### Cited Findings
- `mcp-aladin-books-server` (Node.js MCP server) wraps the Aladin API: ISBN detail lookup, bestseller and new-release lists. It requires a TTB key. — [Glama: TeeDDub/mcp-aladin-books-server](https://glama.ai/mcp/servers/@TeeDDub/mcp-aladin-books-server/blob/0d1ddb0576c5519e416d62aa782b689bcb47c59b/README.md)
- The Obsidian "Kakao Book Search" plugin uses the Kakao REST API key. — [Obsidian community: kakao-book-search](https://community.obsidian.md/plugins/kakao-book-search)
- The Obsidian "Korean Book Search" plugin (lazerfit) uses the Aladin Open API. — [obsidianstats: korean-book-search](https://www.obsidianstats.com/plugins/korean-book-search); repo github.com/lazerfit/korean-book-search
- The Obsidian "KR Book Info" plugin is another Korean book metadata plugin (source not inspected). — [Obsidian: kr-book-info-plugin](https://community.obsidian.md/plugins/kr-book-info-plugin)
- `ImranR98/ISBN-Lookup` queries multiple sources (Google Books, Open Library), a minimal multi-source ISBN aggregator. — [GitHub ISBN-Lookup](https://github.com/ImranR98/ISBN-Lookup)
- Open Library: monthly dumps; a LibrariesHacked guide for loading them into PostgreSQL; DuckDB direct querying; a GraphQL proxy (DiFronzo/OpenLibrary-GraphQL); schemata in openlibrary-client. [fetched] — [Open Library dumps](https://openlibrary.org/developers/dumps)
- The NLK 한국고문헌종합목록 (KORCIS) OpenAPI guide is for old and rare books, not modern ISBN titles, so don't confuse it with Seoji. — [NLK KORCIS OpenAPI guide](https://www.nl.go.kr/korcis/openAPIGuide/contents.do)

### Inferences
- Lessons to borrow from Open Library: keep revisions/last_modified per record, model merges as redirects (so old IDs keep resolving), publish deletes explicitly, and distribute periodic dumps.
- The gap in Korean prior art (no open, merged, provenance-tracked catalog) is itself an opportunity. Licensing of vendor-sourced fields (descriptions, covers) is the main reason such a public dump is hard. An open dump could restrict itself to NLK-derived fields (national bibliography data is described as reusable) and leave vendor fields as links.

### Gaps
- A GitHub-wide search for Python/Go collectors of the NLK Seoji API did not return a notable project in this session's searches. A direct GitHub code search (e.g., `seoji` `EA_ADD_CODE`) is recommended.
- No Korean developer blog post-mortems on running a multi-source book DB were found.
