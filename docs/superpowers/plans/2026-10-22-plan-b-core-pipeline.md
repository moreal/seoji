# Plan B 핵심 파이프라인 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** LOD 국가서지와 Seoji API 데이터를 bronze에 원본 그대로 쌓고, ISBN-13 단위로 정규화·병합한 silver와 pg_bigm 검색용 gold를 PostgreSQL 한 대에서 만드는 CLI `seoji`를 만든다.

**Architecture:** Python 패키지 `seoji`(src 레이아웃)가 수집기(LOD 파일/SPARQL, Seoji HTTP), 순수 함수 정규화·매핑·병합 모듈, DB 빌더(bronze → `silver.candidate` → silver → gold)로 나뉜다. 매핑과 병합은 DB 없이 테스트하는 순수 함수이고, DB 계층은 Docker의 PostgreSQL 17 + pg_bigm에 대해 통합 테스트한다. silver는 언제든 bronze에서 전부 다시 만들 수 있다.

**Tech Stack:** Python ≥3.12, uv, psycopg 3, httpx, pyoxigraph 0.5, pytest, ruff, PostgreSQL 17 + pg_bigm(PGDG apt 패키지) + pg_trgm, Docker Compose.

**Spec:** `docs/plans/02-plan-b-lod-seed-postgres.md` (근거: `research_notes/한국 서지정보 API 조사/`)

## 범위

이 계획은 Plan B의 M1~M6, M7 중 Seoji 증분 윈도우, M8 중 채움률 리포트를 다룬다. 아래는 **후속 계획으로 미룬다** (스펙 대비 의도적 축소):
- `silver.publisher`, `silver.series`, `silver.contributor` 엔티티 테이블 → 이번에는 `edition`/`edition_contributor`에 문자열 컬럼으로 둔다. KAC/KSH 권위 연결(M9)과 함께 엔티티화한다.
- `bronze.record_history`(SCD2), `silver.subject_heading`, `gold.work_cluster`, pgvector 임베딩, LOD 덤프 갱신일 자동 감지.
- `BookInformationService_v2` 대체 경로.

## Global Constraints

- PostgreSQL 16+ 확장: `pg_bigm`, `pg_trgm`. (pgvector는 이번 범위 아님)
- 스키마 3개: `bronze`, `silver`, `gold`. silver/gold는 bronze만으로 재생성 가능해야 한다 — API 재호출 금지.
- edition 키는 ISBN-13(`char(13)`). **ISBN이 다른 레코드를 하나의 edition으로 합치지 않는다.**
- 텍스트 저장은 NFC. 비교 키는 NFKC → casefold → 공백·가운뎃점·괄호 통일 → 구두점 제거.
- Seoji 호출: 초당 1요청, 타임아웃 10초, 오류 013이면 page_size를 절반으로 줄여 재시도, 010/011/012면 즉시 중단. `request_params`에 `cert_key`를 저장하지 않는다.
- Seoji 엔드포인트: `https://www.nl.go.kr/seoji/SearchApi.do`, 날짜 파라미터 `start_publish_date`/`end_publish_date`(yyyymmdd).
- LOD SPARQL: `https://lod.nl.go.kr/sparql`, 키 불필요. 큰 OFFSET 질의는 60초에 504가 나므로 소량(≤200 리소스/질의)만 쓴다.
- `nlon:datePublished`는 변경 감지에 쓰지 않는다. 변경 감지는 본문 해시만 쓴다.
- 제3자 저작물일 수 있는 필드(목차, 책소개, 서평, 초록)는 `silver.edition_rich_text`에 `redistributable=false`로 분리한다. 표지는 URL만 저장(핫링크).
- 정보나루·Kakao 등 다른 소스는 이 DB에 섞지 않는다.

## 실데이터에서 확인한 사실 (2026-10-22 SPARQL 샘플 500건)

스펙의 M1(매핑 명세)에 해당한다. 매핑 코드는 이 사실을 전제로 한다.
- 리소스는 `rdf:type`이 `nlon:Book`, `nlon:OfflineMaterial`, `bibo:Book` 3개이고 blank node는 없다. 덤프·질의 결과 모두 주어별로 연속된다.
- **한 리소스가 여러 ISBN을 갖는 경우가 흔하다** (만화 시리즈 1개 리소스에 ISBN 64개). `bibo:isbn` 값에는 권차 한정어가 붙는다: `"9788925273112 (4)"`, `"9788925268736 (세트)"`, `"9788961596749 (set)"`, `"9788925807164 (제4권)"`, `"9791155971611 (32(완결))"`, `"9787534063671 (上、下)"`, `"9791155091166 (Vol. 06)"`. ISBN-10(`"895298143X (5)"`)도 섞인다.
- 외국 ISBN(978-7 중국, 978-957/986 대만)도 있다. 국가서지 LOD는 "한국 도서"가 아니라 "국중 소장 자료"다.
- `rdfs:label`은 `"표제 / 책임표시"` 형태이고 역할어는 여기만 있다(`dc:creator`는 이름만). 예: `"신의 물방울 / 글: Tadashi Agi ; 그림: Shu Okimoto ;역자: 설은미"`, `"요츠바랑!. / 아즈마 키요히코 저 ; 금정,김동욱 역"`.
- `bibframe:extent`는 항상 다중값: `"263 p"`, `"20 cm"`, `"삽화, 도표"`, `"15책"`, `"27cm"`, `"485p"`.
- `dcterms:issued` 예: `"2017"`, `"2010-2015"`, `"民國82[1993]"`. `nlon:issuedYear`도 있다.
- `dcterms:title`이 둘 이상인 리소스가 있다(150건 중 14건).
- ISBN 없는 `bibo:Book`도 있다(예: `CMO000000001`).
- 그 밖에 관측된 술어: `nlon:kdc`, `nlon:editionOfKDC`, `nlon:ddc`, `nlon:classificationNumberOfNLK`, `nlon:itemNumberOfNLK`, `nlon:remainderOfTitle`, `nlon:titleOfSeries`, `nlon:volumeOfSeries`, `bibo:volume`, `bibo:edition`, `nlon:publicationPlace`, `dc:publisher`, `dcterms:subject`(KSH URI), `dcterms:creator`(KAC URI), `dcterms:tableOfContents`, `dcterms:description`, `dcterms:language`, `bibframe:language`, `nlon:titleOfTranslation`, `nlon:typeOfData`(`dt_gm`, `dt_ca`, `dt_hr`), `owl:sameAs`.

## Review Focus

1. **ISBN 한정어·형식 변형** (`(세트)`, `(set)`, `(제4권)`, `(32(완결))`, ISBN-10 `X`, 하이픈, 체크섬 오류) → 숫자만 정확히 뽑고 한정어는 권차 라벨로, 세트 표시는 세트 ISBN으로, 체크섬 오류는 `merge_issue('invalid_isbn')`로. Task 2·5의 테스트.
2. **한 LOD 리소스에 ISBN 수십 개** → ISBN마다 edition이 생기고, 각 edition의 `volume_label`은 자기 한정어, 세트 ISBN은 `book_set`으로 가고 나머지는 그 세트의 멤버. Task 5·8의 테스트.
3. **같은 입력을 두 번 적재/수집** (같은 덤프 재적재, 같은 날짜 재수집) → bronze 행 수와 `changed_at`이 변하지 않는다. Task 4·6의 테스트.
4. **짧은 한국어 질의** (1~2글자 "역사", 조사 붙은 본문 "아몬드를") → pg_bigm으로 찾힌다. Task 9의 테스트.
5. **외국 ISBN·ISBN 없는 레코드** → 외국 ISBN도 edition으로 들어가되 `is_korean=false`, ISBN 없는 리소스는 `manifestation_no_isbn`. Task 5·8의 테스트.

---

## File Structure

```
pyproject.toml                       # uv 프로젝트, [project.scripts] seoji = "seoji.cli:main"
compose.yaml                         # db 서비스 (포트 55432)
docker/postgres/Dockerfile           # postgres:17 + postgresql-17-pg-bigm
.env.example                         # DATABASE_URL, SEOJI_CERT_KEY
migrations/001_bronze.sql
migrations/002_silver.sql
migrations/003_gold.sql
src/seoji/
  config.py        # 환경변수 → Settings
  db.py            # connect, migrate
  cli.py           # argparse 서브커맨드
  model.py         # CandidateRecord 등 공용 데이터클래스
  normalize/
    isbn.py  text.py  addcode.py  authors.py  physical.py  dates.py
  lod/
    parse.py       # RDF 스트리밍 → 리소스 묶음
    load.py        # bronze.lod_resource 적재
    sparql.py      # SPARQL 소량 조회
    mapping.py     # 리소스 → CandidateRecord
  nlseoji/
    client.py      # Seoji HTTP 클라이언트
    harvest.py     # 날짜 윈도우 수집 → bronze
    mapping.py     # Seoji doc → CandidateRecord
  merge/
    rules.py       # 필드 우선순위·유효성
    merge.py       # ISBN 하나의 후보들 → MergedEdition
  silver/build.py  # candidate 생성, silver 전체/증분 빌드
  gold/build.py    # search_doc 재생성
  report.py        # 채움률·이슈 리포트
scripts/fetch_lod_fixtures.sh
tests/conftest.py
tests/fixtures/lod/*.rdf
tests/fixtures/nlseoji/*.json
tests/...           # 모듈별 test_*.py
README.md
```

---

### Task 1: 프로젝트 골격, Postgres 이미지, 마이그레이션 러너, bronze 스키마

**Files:**
- Create: `pyproject.toml`, `compose.yaml`, `docker/postgres/Dockerfile`, `.env.example`, `.gitignore`, `src/seoji/__init__.py`, `src/seoji/config.py`, `src/seoji/db.py`, `src/seoji/cli.py`, `migrations/001_bronze.sql`, `tests/conftest.py`, `tests/test_db.py`
- `.gitignore`에 `research_notes/`·`reports/`는 넣지 않는다(커밋 대상).

**Interfaces:**
- Produces:
  - `Settings(database_url: str, seoji_cert_key: str | None)`, `load_settings() -> Settings` — `DATABASE_URL`(기본 `postgresql://seoji:seoji@localhost:55432/seoji`), `SEOJI_CERT_KEY`.
  - `connect(url: str) -> psycopg.Connection` (autocommit=False, `row_factory=dict_row`)
  - `migrate(conn, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]` — `public.schema_migrations(version text primary key, applied_at timestamptz)`에 없는 `NNN_*.sql`을 이름순 적용하고 적용한 파일명 리스트 반환.
  - `tests/conftest.py`의 fixture `db` — 세션당 임시 DB `seoji_test_<hex>`를 만들고 migrate, 테스트마다 bronze/silver/gold 모든 테이블 `TRUNCATE ... RESTART IDENTITY CASCADE`. 접속 URL은 `SEOJI_TEST_ADMIN_URL`(기본 `postgresql://seoji:seoji@localhost:55432/postgres`).
  - CLI: `seoji db migrate`.
- `001_bronze.sql`: 스펙 §4의 `bronze.lod_dump`, `bronze.lod_resource`, `bronze.api_payload`, `bronze.source_record` 그대로에 다음을 추가한다: `lod_resource.changed_at timestamptz NOT NULL`, `source_record.changed_at timestamptz NOT NULL`, 인덱스 `lod_resource(changed_at)`, `source_record(changed_at)`, `source_record(isbn13)`. 확장 `CREATE EXTENSION IF NOT EXISTS pg_bigm; ... pg_trgm;`와 `CREATE SCHEMA IF NOT EXISTS` 3개도 여기서.

- [ ] **Step 1: Dockerfile·compose 작성 후 DB 기동**
  - Dockerfile: `FROM postgres:17` + `apt-get install -y postgresql-17-pg-bigm`, `shared_preload_libraries`는 불필요(pg_bigm은 CREATE EXTENSION만으로 동작).
  - compose: user/password/db `seoji`, 포트 `55432:5432`, 볼륨 `pgdata`.
  - Run: `docker compose up -d --build db && docker compose exec db psql -U seoji -c "CREATE EXTENSION pg_bigm; SELECT likequery('a%b');"`
  - Expected: `a\%b` 출력.
- [ ] **Step 2: 실패하는 테스트 작성** — `tests/test_db.py`
  - `test_migrate_applies_all_then_nothing(db_url)`: 빈 DB에 `migrate()` → `["001_bronze.sql"]`, 다시 호출 → `[]`.
  - `test_extensions_and_schemas(db)`: `pg_extension`에 `pg_bigm`, `pg_trgm`; `information_schema.schemata`에 bronze/silver/gold.
- [ ] **Step 3: `uv run pytest tests/test_db.py -v`** → FAIL (모듈 없음)
- [ ] **Step 4: `config.py`, `db.py`, `cli.py`(`db migrate`), `001_bronze.sql`, conftest 구현**
- [ ] **Step 5: `uv run pytest tests/test_db.py -v && uv run ruff check`** → PASS
- [ ] **Step 6: Commit** — `chore: scaffold seoji project with postgres+pg_bigm and bronze schema`

---

### Task 2: ISBN·텍스트 정규화

**Files:**
- Create: `src/seoji/normalize/__init__.py`, `src/seoji/normalize/isbn.py`, `src/seoji/normalize/text.py`
- Test: `tests/normalize/test_isbn.py`, `tests/normalize/test_text.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) IsbnValue(isbn13: str, qualifier: str | None, is_set: bool, raw: str)`
  - `parse_isbn_value(raw: str) -> IsbnValue | None` — 앞쪽의 ISBN 토큰(하이픈·공백 허용, 10자리는 마지막 `X/x` 허용)과 그 뒤 괄호 한정어를 분리. 체크섬이 틀리면 `None`. 한정어가 `세트`/`set`(대소문자 무시)이거나 `세트`를 포함하면 `is_set=True`, 이때 `qualifier=None`.
  - `isbn10_to_13(isbn10: str) -> str`, `is_valid_isbn13(s: str) -> bool`, `is_valid_isbn10(s: str) -> bool`
  - `is_korean_isbn(isbn13: str) -> bool` — 접두 `97889` 또는 `97911`.
  - `split_isbn_list(raw: str) -> list[str]` — 공백·쉼표·세미콜론으로 나뉜 여러 ISBN 문자열을 토큰 리스트로(Seoji `RELATED_ISBN` 원문 보존용).
  - `clean_text(s: str | None) -> str | None` — HTML 태그 제거, `html.unescape`, NFC, 연속 공백 1개, 양끝 strip, 빈 문자열이면 `None`.
  - `compare_key(s: str | None) -> str` — Global Constraints의 비교 키 규칙(가운뎃점 `·`/`ㆍ`/`･`는 공백으로, 모든 괄호류는 제거하되 내용은 유지, 구두점 제거, 공백 제거).
  - `strip_hanja(s: str) -> tuple[str, str | None]` — `"戰國 전국 스트레이즈"` → `("전국 스트레이즈", "戰國")`. 한자만으로 된 문자열은 그대로 두고 두 번째 값 `None`.

- [ ] **Step 1: 실패하는 테스트 작성**
  - `parse_isbn_value("9788925273112 (4)") == IsbnValue("9788925273112", "4", False, ...)`
  - `parse_isbn_value("9788925268736 (세트)").is_set is True` 그리고 `.qualifier is None`
  - `parse_isbn_value("9788961596749 (set)").is_set is True`
  - `parse_isbn_value("9791155971611 (32(완결))").qualifier == "32(완결)"`
  - `parse_isbn_value("895298143X (5)").isbn13 == "9788952981438"`
  - `parse_isbn_value("978-89-364-3426-7").isbn13 == "9788936434267"`
  - `parse_isbn_value("9788936434268") is None` (체크섬), `parse_isbn_value("세트") is None`
  - `is_korean_isbn("9788936434267")`, `is_korean_isbn("9791160979053")`, `not is_korean_isbn("9787520124560")`
  - `clean_text("<b>아몬드</b> &amp; 친구") == "아몬드 & 친구"`, `clean_text("  ") is None`, 조합형 `"가"` → `"가"`
  - `compare_key("(소년탐정) 김전일!") == compare_key("소년탐정 김전일")`, `compare_key("스킵·비트!") == compare_key("스킵 비트")`, `compare_key("ＡＢＣ") == "abc"`
- [ ] **Step 2: `uv run pytest tests/normalize -v`** → FAIL
- [ ] **Step 3: 구현** — 체크섬: ISBN-13 가중치 1,3 교대 합 mod 10 = 0; ISBN-10 가중치 10..1 합 mod 11 = 0(`X`=10).
- [ ] **Step 4: `uv run pytest tests/normalize -v`** → PASS
- [ ] **Step 5: Commit** — `feat: add ISBN and text normalization`

---

### Task 3: 부가기호·저자·형태사항·발행일 파싱

**Files:**
- Create: `src/seoji/normalize/addcode.py`, `authors.py`, `physical.py`, `dates.py`
- Test: `tests/normalize/test_addcode.py`, `test_authors.py`, `test_physical.py`, `test_dates.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) AddCode(code: str, reader: str, form: str, kdc_class: str, kdc_division: str)`; `decode_add_code(code: str | None) -> AddCode | None` — 정확히 숫자 5자리일 때만. `kdc_division`은 3~4번째 자리(2글자).
  - `READER_LABELS = {"0":"교양","1":"실용","4":"청소년","5":"중·고 학습참고","6":"초등 학습참고","7":"아동","9":"전문"}` (2·3·8 미배정 — 정보나루 표의 "2=여성"은 쓰지 않는다), `FORM_LABELS = {"0":"문고본","1":"사전","2":"신서판","3":"단행본","4":"전집·총서·시리즈","5":"전자출판물","6":"도감","7":"그림책·만화","8":"혼합자료"}`.
  - `@dataclass(frozen=True) Contributor(name: str, role: str, role_raw: str | None)`; `parse_responsibility(stmt: str | None) -> list[Contributor]`.
    - role 값: `author`, `translator`, `illustrator`, `editor`, `original_author`, `supervisor`, `photographer`, `other`.
    - 역할어 사전(접두 `역할: 이름` 형과 접미 `이름 역할` 형 모두): 지은이·지음·저·저자·글·글쓴이·著·撰·작가 → author; 옮김·옮긴이·역·역자·번역·譯 → translator; 그림·그린이·그림작가 → illustrator; 엮음·엮은이·편·편저·編·편집 → editor; 원작 → original_author; 감수 → supervisor; 사진 → photographer. `글·그림`/`글그림` → 같은 이름으로 author와 illustrator 두 행.
    - 구분: `;`로 역할 묶음을 나누고, 묶음 안의 이름은 `,`로 나눈다. `...등`·`[外]`·`[편]` 같은 꼬리는 이름에서 뗀다. 역할어가 없으면 role `author`, `role_raw=None`.
  - `@dataclass(frozen=True) Physical(page_count: int | None, height_cm: float | None, volumes: int | None)`; `parse_extent(values: list[str]) -> Physical` — `"263 p"`, `"xii, 263 p."`, `"485p"`, `"263쪽"` → 263; `"20 cm"`, `"27cm"` → 20.0/27.0; `"15책"` → `volumes=15`이고 `page_count=None`.
  - `parse_book_size(s: str | None) -> tuple[int | None, int | None]` — `"183*235"` → `(183, 235)`(폭, 세로 mm), 그 외 `(None, None)`.
  - `parse_issued(s: str | None) -> tuple[date | None, str | None]` — `"2017"` → `(date(2017,1,1), "year")`; `"2010-2015"` → 시작 연도, `"year"`; `"民國82[1993]"` → 대괄호 안 4자리 연도; `"20220509"`/`"2022-05-09"` → `"day"`; `"202205"` → `"month"`; 1400~2100 밖이거나 파싱 불가면 `(None, None)`.

- [ ] **Step 1: 실패하는 테스트 작성** (실데이터 문자열을 그대로 쓴다)
  - `decode_add_code("03810") == AddCode("03810","0","3","8","81")`, `decode_add_code("0381") is None`, `decode_add_code("") is None`
  - `parse_responsibility("지은이: 손원평") == [Contributor("손원평","author","지은이")]`
  - `parse_responsibility("글: Tadashi Agi ; 그림: Shu Okimoto ;역자: 설은미")` → author Tadashi Agi, illustrator Shu Okimoto, translator 설은미 (순서 유지)
  - `parse_responsibility("아즈마 키요히코 저 ; 금정,김동욱 역")` → author 아즈마 키요히코, translator 금정, translator 김동욱
  - `parse_responsibility("글·그림: Hisaya Nakajo ; 옮긴이: 정효진")` → Hisaya Nakajo가 author·illustrator 두 행, 정효진 translator
  - `parse_responsibility("胡廣...等纂修")[0].name == "胡廣"`
  - `parse_responsibility("[이퍼블릭 편]") == [Contributor("이퍼블릭","editor","편")]`
  - `parse_extent(["263 p", "20 cm"]) == Physical(263, 20.0, None)`, `parse_extent(["15책", "19 cm"]) == Physical(None, 19.0, 15)`, `parse_extent(["삽화, 도표"]) == Physical(None, None, None)`
  - `parse_book_size("183*235") == (183, 235)`
  - `parse_issued("民國82[1993]") == (date(1993,1,1), "year")`, `parse_issued("2010-2015") == (date(2010,1,1), "year")`, `parse_issued("20220509") == (date(2022,5,9), "day")`, `parse_issued("미상") == (None, None)`
- [ ] **Step 2: `uv run pytest tests/normalize -v`** → FAIL
- [ ] **Step 3: 구현**
- [ ] **Step 4: `uv run pytest tests/normalize -v`** → PASS
- [ ] **Step 5: Commit** — `feat: parse add codes, responsibility statements, extent and dates`

---

### Task 4: LOD 파싱과 bronze 적재, SPARQL 소량 조회

**Files:**
- Create: `src/seoji/lod/__init__.py`, `parse.py`, `load.py`, `sparql.py`, `scripts/fetch_lod_fixtures.sh`, `tests/fixtures/lod/*.rdf`
- Modify: `src/seoji/cli.py` (`lod load`, `lod fetch`, `lod count`)
- Test: `tests/lod/test_parse.py`, `tests/lod/test_load.py`

**Interfaces:**
- Consumes: `connect`, fixture `db` (Task 1)
- Produces:
  - `@dataclass LodResource(uri: str, body: dict[str, list[str | dict]])` — body 키는 술어 전체 IRI, 값 리스트는 정렬된 상태. 리터럴은 `str`(언어 태그가 있으면 `{"@value": v, "@language": l}`), IRI는 `{"@id": iri}`.
  - `iter_resources(path: Path, fmt: Literal["ttl","nt","rdfxml","jsonld"]) -> Iterator[LodResource]` — `pyoxigraph.parse(path=..., format=...)` 스트리밍, 주어가 바뀔 때 묶음 방출(메모리에 전체를 올리지 않는다). 같은 주어가 비연속으로 다시 나오면 별도 묶음으로 방출하고 적재 단계가 합친다.
  - `body_hash(body: dict) -> bytes` — `json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",",":"))`의 sha256.
  - `@dataclass LoadStats(dump_id: int, resources: int, inserted: int, changed: int, unchanged: int, tombstoned: int)`
  - `load_dump(conn, path: Path, *, dataset: str, fmt: str, dump_date: date | None, mark_missing: bool = False, batch_size: int = 5000) -> LoadStats` — `lod_dump` 행 생성(파일 sha256 포함) → 배치마다 임시 테이블에 `COPY` → `INSERT ... ON CONFLICT (resource_uri) DO UPDATE`. 같은 덤프 안에서 비연속으로 다시 나온 주어는 술어별로 값을 합친다(합집합, 정렬). 해시가 같으면 `last_dump_id`만 갱신, 다르면 `body`·`body_sha256`·`changed_at=now()` 갱신. 새로 나타난 리소스는 `deleted_at=NULL`로 되살린다. `mark_missing=True`면 이번 `dump_id`에 안 나온 같은 dataset 리소스에 `deleted_at=now()`, `changed_at=now()`.
  - `sparql_construct(uris: list[str], *, endpoint: str = SPARQL_ENDPOINT, timeout: float = 70) -> bytes` (RDF/XML), `sparql_count_books() -> int`.
  - CLI: `seoji lod load PATH --dataset book --format ttl [--dump-date YYYY-MM-DD] [--mark-missing]`, `seoji lod fetch URI... -o FILE`, `seoji lod count`.
- 픽스처(`scripts/fetch_lod_fixtures.sh`가 `seoji lod fetch`와 같은 CONSTRUCT를 curl로 호출해 저장):
  - `sample_kr.rdf`: `KJU201703899`(아몬드), `KJU201108521`(ISBN 1개 + `(세트)`), `KJU201211257`(KSH 주제 + 세트 + 7 ISBN), `KJU201208224`(`(set)`), `KJU200801614`(`(제4권)`), `KJU200607571`(`(32(완결))`), `KJU200803205`(한정어 없는 ISBN 2개), `CMO202503241`, `CMO000000001`(ISBN 없음).
  - `sample_foreign.rdf`: `batch_0` 질의(`LIMIT 150 OFFSET 0`)에서 앞쪽 5개 리소스.

- [ ] **Step 1: 픽스처 받기** — Run: `bash scripts/fetch_lod_fixtures.sh` → Expected: 두 파일 생성, `grep -c 'rdf:about' tests/fixtures/lod/sample_kr.rdf`가 `9`.
- [ ] **Step 2: 실패하는 테스트 작성**
  - `test_iter_resources_groups_by_subject`: `sample_kr.rdf` → 리소스 9개, `KJU201703899` body의 `http://purl.org/ontology/bibo/isbn == ["9788936434267"]`, `http://purl.org/dc/terms/subject`가 `{"@id": ...KSH2002030019}` 포함.
  - `test_body_hash_is_order_independent`: 값 순서·키 순서만 다른 두 body의 해시가 같다.
  - `test_load_dump_counts(db)`: 첫 적재 → `inserted=9, changed=0`; `bronze.lod_resource` 9행.
  - `test_reload_same_dump_is_noop(db)`: 같은 파일 재적재 → `inserted=0, changed=0, unchanged=9`, 모든 행의 `changed_at` 불변.
  - `test_changed_body_updates_changed_at(db)`: `dcterms:title` 하나를 바꾼 임시 N-Triples 파일 적재 → 그 리소스만 `changed=1`.
  - `test_mark_missing_tombstones(db)`: 리소스 8개짜리 파일을 `mark_missing=True`로 적재 → `tombstoned=1`, 그 행 `deleted_at IS NOT NULL`; 다시 9개 파일 적재 → `deleted_at IS NULL`.
- [ ] **Step 3: `uv run pytest tests/lod -v`** → FAIL
- [ ] **Step 4: 구현**
- [ ] **Step 5: `uv run pytest tests/lod -v`** → PASS
- [ ] **Step 6: Commit** — `feat: stream LOD RDF into bronze with hash-based change tracking`

---

### Task 5: 공용 후보 모델과 LOD 매핑

**Files:**
- Create: `src/seoji/model.py`, `src/seoji/lod/mapping.py`
- Test: `tests/lod/test_mapping.py`

**Interfaces:**
- Consumes: Task 2·3의 정규화 함수, `LodResource`(Task 4)
- Produces (`model.py`):
  - `FIELDS: tuple[str, ...]` = `title, remainder_of_title, title_hanja, volume_label, edition_statement, responsibility_stmt, publisher, publication_place, pub_date, pub_date_precision, extent_raw, page_count, height_cm, width_mm, height_mm, volumes, binding, form, ea_add_code, kdc, kdc_edition, ddc, nlk_call_no, language, original_title, series_title, series_no, price_planned, price_real, cover_url, deposit_yn, cip_control_no, related_isbn_raw`
  - `@dataclass CandidateRecord(source: Literal["lod","nlseoji"], source_key: str, isbn13: str, fields: dict[str, Any], contributors: list[Contributor], subjects: list[tuple[str, str, str | None]], rich_text: dict[str, str], set_isbn13: str | None, set_add_code: str | None, set_expression: str | None, observed_at: datetime | None)` — `fields`에는 `FIELDS`의 키만, 값이 없으면 키를 넣지 않는다. `subjects` 원소는 `(scheme, code, label)`, scheme은 `kdc|ddc|add_code|ksh|nlk_keyword|seoji_subject`. `rich_text` 키는 `toc|introduction|summary|abstract`.
  - `CandidateRecord.to_json() -> dict` / `CandidateRecord.from_json(d) -> CandidateRecord` — `date`/`datetime`은 ISO 문자열로 왕복.
  - `@dataclass NoIsbnRecord(resource_uri: str, title: str | None, responsibility_stmt: str | None, publisher: str | None, issued_year: int | None, kdc: str | None)`
  - `@dataclass InvalidIsbn(source: str, source_key: str, raw: str)`
- Produces (`lod/mapping.py`):
  - `map_lod_resource(res: LodResource) -> tuple[list[CandidateRecord], NoIsbnRecord | None, list[InvalidIsbn]]`
  - 규칙:
    - 유효한 ISBN마다 후보 1개. `source_key = res.uri`. `is_set` ISBN은 후보를 만들되(세트 자체도 edition), 같은 리소스의 다른 후보들의 `set_isbn13`을 그 값으로 채운다. 세트 ISBN이 여럿이면 첫 번째만.
    - `volume_label`: ISBN 한정어 → 없으면 `bibo:volume` → 없으면 없음.
    - `title`: `rdfs:label`의 `" / "` 앞부분과 `compare_key`가 같은 `dcterms:title`, 없으면 정렬 후 첫 `dcterms:title`. `strip_hanja`로 `title_hanja` 분리. `remainder_of_title` ← `nlon:remainderOfTitle`.
    - `responsibility_stmt` ← `rdfs:label`의 첫 `" / "` 뒷부분, `contributors` ← 그것을 `parse_responsibility`; label에 책임표시가 없으면 `dc:creator` 각각을 role `author`, `role_raw=None`.
    - `publisher` ← 첫 `dc:publisher`, `publication_place` ← `nlon:publicationPlace`, `pub_date`/`pub_date_precision` ← `parse_issued(dcterms:issued)`, 실패하면 `nlon:issuedYear`.
    - `extent_raw` ← `bibframe:extent` 값을 `" ; "`로 이은 것, `page_count`/`height_cm`/`volumes` ← `parse_extent`.
    - `kdc` ← 첫 `nlon:kdc`, `kdc_edition` ← `nlon:editionOfKDC`, `ddc` ← `nlon:ddc`, `nlk_call_no` ← `classificationNumberOfNLK + "-" + itemNumberOfNLK`(둘 다 있을 때), `edition_statement` ← `bibo:edition`, `series_title`/`series_no` ← `nlon:titleOfSeries`/`nlon:volumeOfSeries` 첫 값, `original_title` ← `nlon:titleOfTranslation`, `language` ← `bibframe:language` IRI의 마지막 경로(`kor`).
    - `subjects`: `("kdc", kdc, None)`, `("ddc", ddc, None)`, `dcterms:subject` 각각 `("ksh", <KSH id>, None)`, `nlon:keyword` 각각 `("nlk_keyword", kw, kw)`.
    - `rich_text`: `toc` ← `dcterms:tableOfContents`를 `"\n"`로 이음, `abstract` ← `dcterms:description`을 `"\n"`로 이음.
    - 모든 문자열은 `clean_text` 통과.
    - ISBN 술어가 아예 없으면 `NoIsbnRecord`. 술어는 있는데 모두 무효면 `InvalidIsbn`만.

- [ ] **Step 1: 실패하는 테스트 작성** (`sample_kr.rdf`, `sample_foreign.rdf` 사용)
  - 아몬드: 후보 1개, `isbn13="9788936434267"`, `title="아몬드"`, `remainder_of_title="손원평 장편소설"`, `contributors==[Contributor("손원평","author","지은이")]`, `publisher="창비"`, `pub_date==date(2017,1,1)`, `pub_date_precision=="year"`, `page_count==263`, `height_cm==20.0`, `kdc=="813.7"`, `nlk_call_no=="813.7-17-222"`, `("ksh","KSH2002030019",None) in subjects`.
  - `KJU201108521`: 후보 2개, 세트 후보 `isbn13="9791189431907"`, 다른 후보의 `set_isbn13=="9791189431907"`.
  - `KJU201208224`: `(set)` ISBN `9788961596749`가 세트로 인식되어 다른 후보들의 `set_isbn13`.
  - `KJU200801614`: `9788925807164` 후보의 `volume_label=="제4권"`.
  - `KJU201211257`: 후보 7개, 모두 같은 `title`, `volume_label`은 각자 한정어.
  - `CMO000000001`: 후보 0개, `NoIsbnRecord` 반환.
  - 외국 픽스처: 후보가 만들어지고 `is_korean_isbn(c.isbn13)`이 False인 것이 1개 이상.
  - `test_candidate_json_roundtrip`: 아몬드 후보 `from_json(to_json(c)) == c`.
- [ ] **Step 2: `uv run pytest tests/lod/test_mapping.py -v`** → FAIL
- [ ] **Step 3: 구현**
- [ ] **Step 4: `uv run pytest tests/lod/test_mapping.py -v`** → PASS
- [ ] **Step 5: Commit** — `feat: map LOD resources to per-ISBN candidate records`

---

### Task 6: Seoji 클라이언트, 매핑, 날짜 윈도우 수집

**Files:**
- Create: `src/seoji/nlseoji/__init__.py`, `client.py`, `mapping.py`, `harvest.py`, `tests/fixtures/nlseoji/page_20220509_p1.json`, `page_20220509_p2.json`, `error_011.json`, `error_013.json`
- Modify: `src/seoji/cli.py` (`harvest`)
- Test: `tests/nlseoji/test_client.py`, `test_mapping.py`, `test_harvest.py`

**Interfaces:**
- Consumes: 정규화 함수(Task 2·3), `CandidateRecord`(Task 5), fixture `db`
- Produces:
  - `class SeojiError(Exception)` (`code: str`, `message: str`), `class PageSizeTooLarge(SeojiError)` (code `013`), `class FatalSeojiError(SeojiError)` (code `000`/`010`/`011`/`012`).
  - `@dataclass SeojiPage(total_count: int, page_no: int, docs: list[dict[str, str]], raw: dict, params: dict)` — `params`에는 `cert_key`가 없다.
  - `class SeojiClient(cert_key: str, *, base_url: str = SEOJI_URL, http: httpx.Client | None = None, min_interval: float = 1.0, timeout: float = 10.0, sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic)`; `search(**params) -> SeojiPage` — `result_style=json` 고정. 응답이 `{"RESULT":"ERROR","ERR_CODE":...}`이면 코드별 예외. 네트워크 오류·5xx는 지수 백오프(1, 2, 4초) 3회 후 예외. `min_interval` 간격을 `clock`/`sleep`으로 지킨다.
  - `map_seoji_doc(doc: dict[str, str], observed_at: datetime) -> CandidateRecord | InvalidIsbn | None` — 빈 문자열은 없음으로 본다. `EA_ISBN` 무효면 `InvalidIsbn`, 비었으면 `None`.
    - 매핑: TITLE→title(+`strip_hanja`), VOL→volume_label, SERIES_TITLE/SERIES_NO→series_*, AUTHOR→responsibility_stmt + contributors, PUBLISHER→publisher, EDITION_STMT→edition_statement, PRE_PRICE/REAL_PRICE→price_planned/price_real(숫자만, `"0"`이면 없음), KDC/DDC→kdc/ddc + subjects, PAGE→page_count(정수만), BOOK_SIZE→width_mm/height_mm, FORM→form, EBOOK_YN `Y`→binding `ebook`(아니면 부가기호 2번째 자리 `5`→`ebook`, 그 외 `paper`), PUBLISH_PREDATE→pub_date(`day`), EA_ADD_CODE→ea_add_code + `("add_code", code, None)`, SUBJECT→`("seoji_subject", s, s)`, TITLE_URL→cover_url, DEPOSIT_YN→deposit_yn(bool), CONTROL_NO→cip_control_no, RELATED_ISBN→related_isbn_raw, SET_ISBN/SET_ADD_CODE/SET_EXPRESSION→set_*, BOOK_TB_CNT/BOOK_INTRODUCTION/BOOK_SUMMARY→rich_text `toc`/`introduction`/`summary`. `source_key = isbn13`.
  - `@dataclass HarvestStats(days: int, requests: int, records: int, changed: int, invalid: int)`
  - `harvest_range(conn, client: SeojiClient, start: date, end: date, *, page_size: int = 100) -> HarvestStats` — 하루씩 `start_publish_date=end_publish_date=그날`로 모든 페이지 수집. `PageSizeTooLarge`면 page_size 절반(최소 10)으로 그날 처음부터. 페이지마다 `bronze.api_payload`에 `(source='nlseoji', body_sha256)` 충돌 무시 삽입, doc마다 `bronze.source_record` upsert(`record_sha256` 같으면 `last_seen_at`만, 다르면 `record`·`changed_at` 갱신). 하루 단위로 commit.
  - `window_dates(name: Literal["daily","weekly"], today: date) -> tuple[date, date]` — daily `[today-30, today+90]`, weekly `[today-365, today-31]`.
  - CLI: `seoji harvest (--from YYYY-MM-DD --to YYYY-MM-DD | --window daily|weekly) [--page-size N]`. 키가 없으면 "SEOJI_CERT_KEY가 필요합니다" 출력 후 종료 코드 2.
- 픽스처는 **스펙 필드 목록으로 만든 합성 데이터**다(실키 없음). 파일 머리에 `"_synthetic": true`를 넣고, 실키를 받으면 Task 10 Step 4에서 실제 응답으로 교체한다. 엔벌로프: `{"PAGE_NO":"1","TOTAL_COUNT":"3","docs":[...]}`; p1에 2건(하나는 `EA_ISBN` 체크섬 오류), p2에 1건(EBOOK_YN `Y`).

- [ ] **Step 1: 실패하는 테스트 작성** (`httpx.MockTransport`로 픽스처 반환)
  - `test_search_strips_cert_key_from_params`, `test_error_011_raises_fatal`, `test_error_013_raises_page_size`, `test_rate_limit_sleeps_between_calls`(가짜 clock으로 두 번째 호출 전 `sleep(1.0)` 호출 확인), `test_retries_5xx_then_succeeds`.
  - 매핑: 종이책 doc → `price_planned==16800`(PRE_PRICE `"16,800"`), `width_mm==128, height_mm==188`, `pub_date==date(2022,5,9)`, `binding=="paper"`, `("add_code","03810",None) in subjects`, `rich_text["introduction"]` 존재; `EA_ISBN` 무효 → `InvalidIsbn`; EBOOK_YN Y → `binding=="ebook"`.
  - `test_harvest_range_stores_bronze(db)`: 하루 → `requests==2`, `records==2`, `invalid==1`; `bronze.source_record` 2행, `api_payload.request_params`에 `cert_key` 없음.
  - `test_harvest_twice_is_noop(db)`: 같은 범위 재수집 → `changed==0`, `api_payload` 행 수 불변.
  - `test_harvest_shrinks_page_size_on_013(db)`: 첫 응답 013, 이후 정상 → 두 번째 요청의 `page_size==50`.
  - `test_window_dates`: `window_dates("daily", date(2026,10,22)) == (date(2026,9,22), date(2027,1,20))`.
- [ ] **Step 2: `uv run pytest tests/nlseoji -v`** → FAIL
- [ ] **Step 3: 구현**
- [ ] **Step 4: `uv run pytest tests/nlseoji -v`** → PASS
- [ ] **Step 5: Commit** — `feat: add Seoji API client and date-window harvester`

---

### Task 7: 병합 엔진 (순수 함수)

**Files:**
- Create: `src/seoji/merge/__init__.py`, `rules.py`, `merge.py`
- Test: `tests/merge/test_merge.py`

**Interfaces:**
- Consumes: `CandidateRecord`(Task 5), `compare_key`(Task 2), `decode_add_code`(Task 3)
- Produces:
  - `PRECEDENCE: dict[str, tuple[str, ...]]` — 아래 외 모든 `FIELDS`는 `("lod", "nlseoji")`. `("nlseoji", "lod")`: `price_planned, price_real, ea_add_code, form, binding, cover_url, deposit_yn, cip_control_no, width_mm, height_mm, related_isbn_raw`. `pub_date`·`pub_date_precision`은 `choose_pub_date`가 정한다.
  - `is_valid(field: str, value: Any) -> bool` — `None`/빈 문자열/`"0"`/`0` 거부, `page_count`는 1~20000, `pub_date`는 1400-01-01~오늘+2년.
  - `@dataclass ProvenanceRow(field: str, source: str, source_key: str, raw_value: str | None, chosen: bool, rule: str)`
  - `@dataclass MergeIssue(kind: Literal["isbn_conflict","multi_lod"], detail: dict)`
  - `@dataclass MergedEdition(isbn13: str, fields: dict[str, Any], pub_status: Literal["announced","published"], primary_resource_uri: str | None, links: list[tuple[str, str, str]], contributors: list[tuple[Contributor, str]], subjects: list[tuple[str, str, str | None, str]], rich_text: list[tuple[str, str, str]], set_links: list[tuple[str, str | None, str | None]], provenance: list[ProvenanceRow], issues: list[MergeIssue])`
    - `links`: `(source, source_key, link_role)`, link_role `primary|secondary`.
    - `contributors`: 우선순위 1등 소스 하나의 목록 전체(소스 간에 섞지 않는다)와 그 소스.
    - `subjects`: 모든 후보의 `(scheme, code, label, source)` 중복 제거 합집합.
    - `rich_text`: `(kind, source, body)` 모든 후보.
    - `set_links`: 후보들의 `(set_isbn13, set_add_code, set_expression)` 중복 제거.
  - `choose_primary_lod(cands: list[CandidateRecord]) -> CandidateRecord` — 채워진 `fields` 수가 많은 순, 같으면 `source_key` 사전순 최소.
  - `choose_pub_date(lod: CandidateRecord | None, seoji: CandidateRecord | None) -> tuple[date | None, str | None, str]` — 반환 세 번째는 rule 이름. ① seoji `deposit_yn`이 True이고 seoji 날짜 연도 == lod 날짜 연도면 seoji(`day`), rule `seoji_deposited_match` ② lod 날짜가 있으면 lod, rule `lod` ③ seoji 날짜, rule `seoji_announced`.
  - `merge_edition(isbn13: str, cands: list[CandidateRecord]) -> MergedEdition`
    - 필드마다 PRECEDENCE 순으로 `is_valid`인 첫 값을 채택. 모든 후보 값을 `ProvenanceRow`로 남기고 채택 값만 `chosen=True`, rule은 `precedence:<source>`.
    - lod 후보가 2개 이상이면 `choose_primary_lod`로 하나만 필드 후보에 쓰고 나머지는 `secondary` 링크 + `MergeIssue("multi_lod", {"uris": [...]})`.
    - `pub_status`: lod 후보가 있거나 seoji `deposit_yn`이 True면 `published`, 아니면 `announced`.
    - `isbn_conflict`: lod·seoji 후보가 모두 있고, 두 `title`의 `compare_key` 문자 bigram Jaccard < 0.3 이고 `publisher` `compare_key`가 다르면 `MergeIssue("isbn_conflict", {"lod_title", "seoji_title", "lod_publisher", "seoji_publisher"})`. 병합은 그대로 진행한다.
    - `ea_add_code`가 있으면 `fields`에 `add_reader/add_form/add_kdc_class/add_kdc_division`도 넣는다.

- [ ] **Step 1: 실패하는 테스트 작성** (후보는 테스트 안에서 직접 생성)
  - `test_lod_wins_title_seoji_wins_price`: lod title "아몬드", seoji title "아몬드(양장)" + price_real 12000 → title "아몬드", price_real 12000, provenance에 title 2행 중 lod만 chosen.
  - `test_invalid_value_falls_through`: lod page_count 0, seoji 263 → 263.
  - `test_pub_date_rules`: (deposit Y, 2017-03-20 / lod 2017) → `(date(2017,3,20),"day","seoji_deposited_match")`; (deposit N) → lod 날짜, `"year"`; lod 없음 → seoji, `"seoji_announced"`, `pub_status=="announced"`.
  - `test_multi_lod_picks_richer_and_flags`: 필드 5개 vs 2개 lod → 5개짜리가 primary, issue `multi_lod`.
  - `test_isbn_conflict_flagged`: lod "아몬드"/창비 vs seoji "점자 교본"/부산점자도서관 → `isbn_conflict`.
  - `test_contributors_not_mixed`: lod 기여자 1명, seoji 2명 → lod의 1명만.
  - `test_add_code_decoded`: seoji ea_add_code "43810" → `fields["add_reader"]=="4"`, `fields["add_kdc_division"]=="81"`.
- [ ] **Step 2: `uv run pytest tests/merge -v`** → FAIL
- [ ] **Step 3: 구현**
- [ ] **Step 4: `uv run pytest tests/merge -v`** → PASS
- [ ] **Step 5: Commit** — `feat: add field-precedence merge engine with provenance`

---

### Task 8: silver 스키마와 전체·증분 빌드

**Files:**
- Create: `migrations/002_silver.sql`, `src/seoji/silver/__init__.py`, `src/seoji/silver/build.py`
- Modify: `src/seoji/cli.py` (`silver rebuild`, `silver refresh`)
- Test: `tests/silver/test_build.py`

**Interfaces:**
- Consumes: `map_lod_resource`(Task 5), `map_seoji_doc`(Task 6), `merge_edition`(Task 7), `load_dump`·`harvest_range`(Task 4·6, 테스트 준비용)
- `002_silver.sql` 테이블 (스펙 §4 기준, 범위 절의 축소 반영):
  - `silver.candidate(source text, source_key text, isbn13 char(13), body jsonb NOT NULL, PRIMARY KEY (source, source_key, isbn13))` + `candidate(isbn13)` 인덱스 — `CandidateRecord.to_json()`.
  - `silver.edition` — 스펙 컬럼 중 `publisher_id`, `work_id`, `redistributable` 대신 `publisher text`, `publisher_normalized text`, `series_title text`, `series_no text`, `volumes int`, `form text`, `related_isbn_raw text`, `is_korean boolean NOT NULL`. `pub_status` CHECK는 `('announced','published')`. `content_hash bytea NOT NULL`.
  - `silver.edition_record_link`, `silver.manifestation_no_isbn`, `silver.book_set`, `silver.set_member`, `silver.edition_subject`, `silver.edition_rich_text`, `silver.field_provenance`, `silver.merge_issue` — 스펙 그대로. 단 `merge_issue.kind` 값에 `invalid_isbn` 포함, `set_member.isbn13`과 edition 자식 테이블의 FK는 `ON DELETE CASCADE`.
  - `silver.edition_contributor(isbn13 char(13) REFERENCES silver.edition ON DELETE CASCADE, ordinal int, name text NOT NULL, name_normalized text NOT NULL, role text NOT NULL, role_raw text, source text NOT NULL, PRIMARY KEY (isbn13, ordinal))`.
  - `silver.build_state(id serial PRIMARY KEY, kind text, started_at timestamptz, finished_at timestamptz, editions int)`.
- Produces:
  - `@dataclass BuildStats(candidates: int, editions: int, no_isbn: int, issues: int)`
  - `rebuild_silver(conn) -> BuildStats` — silver 전체 TRUNCATE → bronze의 삭제되지 않은 `lod_resource`와 `source_record`(source `nlseoji`)를 서버 측 커서로 스트리밍해 매핑, `candidate`·`manifestation_no_isbn`·`merge_issue(invalid_isbn)`에 COPY → `candidate`를 `isbn13` 순으로 읽어 ISBN마다 `merge_edition` → edition과 자식 테이블에 COPY → `book_set`은 `set_links` 합집합으로 upsert(`total_volumes`는 `set_expression`의 `전N권`에서). `set_member`는 set ISBN과 member ISBN이 모두 edition에 있을 때만. 끝나면 `build_state` 기록.
  - `refresh_silver(conn) -> BuildStats` — 마지막 성공 `build_state.started_at` 이후 `changed_at`이 지난 bronze 행만 다시 매핑: 그 `(source, source_key)`의 기존 candidate·no_isbn을 지우고 새로 넣은 뒤, 지운 것과 새로 넣은 것의 ISBN 합집합만 다시 병합(해당 edition 삭제 후 재삽입, 후보가 없어진 ISBN의 edition은 삭제).
  - CLI: `seoji silver rebuild`, `seoji silver refresh` — 끝에 `BuildStats` 출력.

- [ ] **Step 1: 실패하는 테스트 작성** (LOD 픽스처 + Seoji 합성 픽스처를 bronze에 적재한 뒤)
  - `test_rebuild_creates_editions(db)`: `KJU201211257` 7 ISBN 모두 edition에 있고, 세트 ISBN `9788993171440`이 `book_set`, 나머지 6개가 그 `set_member`.
  - `test_almond_edition(db)`: `9788936434267` edition의 `title=="아몬드"`, `is_korean`, `edition_contributor` 1행, `edition_subject`에 `ksh`.
  - `test_foreign_isbn_not_korean(db)`: 외국 픽스처 ISBN 하나 이상이 `is_korean=false`.
  - `test_no_isbn_resource(db)`: `manifestation_no_isbn`에 `CMO000000001`.
  - `test_invalid_isbn_issue(db)`: Seoji 합성 픽스처의 체크섬 오류가 `merge_issue(kind='invalid_isbn')`.
  - `test_rebuild_is_deterministic(db)`: 두 번 rebuild → edition의 `(isbn13, content_hash)` 집합이 같다.
  - `test_refresh_only_touches_changed(db)`: rebuild 후 아몬드 리소스의 제목만 바꾼 파일 적재 → `refresh_silver().editions == 1`, 아몬드 title 갱신.
  - `test_refresh_removes_tombstoned(db)`: 아몬드를 뺀 파일을 `mark_missing=True`로 적재 → refresh 후 `9788936434267` edition 없음(Seoji 후보가 없을 때).
- [ ] **Step 2: `uv run pytest tests/silver -v`** → FAIL
- [ ] **Step 3: 구현**
- [ ] **Step 4: `uv run pytest tests/silver -v`** → PASS
- [ ] **Step 5: Commit** — `feat: build silver layer from bronze with full and incremental modes`

---

### Task 9: gold 검색 문서와 검색 함수

**Files:**
- Create: `migrations/003_gold.sql`, `src/seoji/gold/__init__.py`, `src/seoji/gold/build.py`
- Modify: `src/seoji/cli.py` (`gold rebuild`, `search`), `src/seoji/silver/build.py` (rebuild/refresh 끝에 gold 갱신 호출 여부를 인자 `with_gold: bool = True`로)
- Test: `tests/gold/test_search.py`

**Interfaces:**
- Consumes: silver 테이블(Task 8)
- `003_gold.sql`:
  - `gold.search_doc(isbn13 char(13) PRIMARY KEY, title text, authors text, publisher text, series_title text, kdc text, add_reader char(1), binding text, pub_year int, is_korean boolean, search_text text NOT NULL)` + `USING gin (search_text gin_bigm_ops)`.
  - `gold.search_key(s text) RETURNS text IMMUTABLE` = `lower(normalize(coalesce(s,''), NFKC))`의 연속 공백 정리.
  - `gold.search_books(q text, lim int DEFAULT 20, korean_only boolean DEFAULT false) RETURNS TABLE(isbn13 char(13), title text, authors text, publisher text, pub_year int, score real)` — `gold.search_key(q)`를 공백으로 나눈 각 단어가 모두 `search_text LIKE likequery(word)`; 정렬 `bigm_similarity(gold.search_key(q), gold.search_key(title)) DESC, pub_year DESC NULLS LAST, isbn13`.
  - `search_text` = `search_key(title || ' ' || title || ' ' || coalesce(remainder_of_title,'') || ' ' || authors || ' ' || publisher || ' ' || series_title || ' ' || 주제 label들)`.
- Produces:
  - `rebuild_search_doc(conn, isbns: list[str] | None = None) -> int` — `None`이면 전체 TRUNCATE 후 `INSERT ... SELECT`, 아니면 그 ISBN만 DELETE/INSERT. `authors`는 `edition_contributor`를 ordinal 순 `", "`로.
  - CLI: `seoji gold rebuild`, `seoji search "질의" [--limit N] [--korean-only]` — 표 형태로 isbn13, title, authors, publisher, pub_year 출력.

- [ ] **Step 1: 실패하는 테스트 작성** (silver를 픽스처로 rebuild한 상태에서)
  - `test_search_exact_title(db)`: `search_books('아몬드')` 첫 행 `9788936434267`.
  - `test_search_two_syllables(db)`: `search_books('재판')` 결과에 `KJU201211257`의 ISBN 포함("좌충우돌 재판이야기").
  - `test_search_substring_with_particle(db)`: `search_text`에 "아몬드를"만 있는 edition을 직접 넣고 `search_books('아몬드')`에 포함.
  - `test_search_author_and_title_terms(db)`: `search_books('손원평 아몬드')` 결과 1건 이상, `search_books('손원평 헌터')` 0건.
  - `test_search_escapes_wildcards(db)`: `search_books('%')` 예외 없이 0건.
  - `test_korean_only_filter(db)`: 외국 픽스처 제목 단어로 검색 → `korean_only=true`면 0건.
- [ ] **Step 2: `uv run pytest tests/gold -v`** → FAIL
- [ ] **Step 3: 구현**
- [ ] **Step 4: `uv run pytest tests/gold -v`** → PASS
- [ ] **Step 5: Commit** — `feat: add pg_bigm search documents and search_books function`

---

### Task 10: 리포트, 운영 문서, 실데이터 종단 검증

**Files:**
- Create: `src/seoji/report.py`, `README.md`, `ops/crontab.example`
- Modify: `src/seoji/cli.py` (`report`)
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: 모든 이전 Task
- Produces:
  - `fill_rates(conn) -> list[tuple[str, int, float]]` — `silver.edition`의 각 `FIELDS` 컬럼별 `(field, non_null, ratio)`.
  - `issue_counts(conn) -> dict[str, int]`, `source_coverage(conn) -> dict[str, int]` — `lod_only`, `nlseoji_only`, `both` edition 수.
  - CLI: `seoji report` — 세 결과를 출력.
  - `ops/crontab.example`: 매일 03:00 `seoji harvest --window daily && seoji silver refresh`, 매주 일 04:00 `seoji harvest --window weekly && seoji silver refresh`, 분기 1일 05:00 전 기간 `seoji harvest --from <M1에서 정한 시작일> --to <오늘+90> && seoji silver refresh`.
  - README: 설치(`uv sync`, `docker compose up -d db`, `seoji db migrate`), 키 신청 경로(NLK Open API 회원가입 → 키 신청 → 담당자 승인), LOD 덤프 받는 곳(`lod.nl.go.kr/home/dataset/datadownload.do`, 다운로드 전 폼 제출)과 `seoji lod load` 예시, 라이선스 주의(Global Constraints의 rich_text·표지 규칙).

- [ ] **Step 1: 실패하는 테스트 작성** — `test_report_on_fixtures(db)`: 픽스처 rebuild 후 `source_coverage`의 합이 edition 수와 같고, `fill_rates`에 `("title", n, 1.0)`.
- [ ] **Step 2: `uv run pytest tests/test_report.py -v`** → FAIL
- [ ] **Step 3: 구현 + README + crontab 예시**
- [ ] **Step 4: 실데이터 종단 검증 (키 없이 가능한 범위)**
  - Run: SPARQL로 한국 ISBN 리소스 1,000개를 200개씩 5번 받는다(`FILTER(STRSTARTS(?i, "97911"))`·`"97889"` + `LIMIT 200 OFFSET 0/200/...`; 실패하면 OFFSET을 줄인다) → 각 파일 `seoji lod load --format rdfxml` → `seoji silver rebuild` → `seoji search 아몬드`, `seoji search 역사`, `seoji report`.
  - Expected: `bronze.lod_resource` 행 수 == 받은 리소스 수, `silver.edition` ≥ 리소스 수, 검색 결과가 나오고, `report`의 `title` 채움률 1.0. 수치를 README "검증 기록"에 적는다.
- [ ] **Step 5: (키·덤프를 받은 뒤 사용자가 실행) 실키·전체 덤프 검증 절차를 README에 기록**
  - `SEOJI_CERT_KEY` 설정 후 `seoji harvest --from 2022-05-09 --to 2022-05-09` → 실제 응답으로 `tests/fixtures/nlseoji/` 합성 픽스처를 교체하고 테스트 재실행; page_size 200/500으로 013 여부, 가장 오래된 `PUBLISH_PREDATE` 확인.
  - 덤프 적재 후 `seoji lod count`와 `bronze.lod_resource` 수(3,980,216 ±1%)를 대조.
- [ ] **Step 6: 전체 테스트·린트** — Run: `uv run pytest -q && uv run ruff check && uv run ruff format --check` → 모두 통과
- [ ] **Step 7: Commit** — `feat: add quality report, ops docs and end-to-end verification`
