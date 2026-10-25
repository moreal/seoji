# seoji

국립중앙도서관 **국가서지 LOD**와 **ISBN 서지정보(Seoji) API**로 한국 도서 정보 데이터베이스를 만드는 도구입니다.
설계 배경은 [`docs/plans/02-plan-b-lod-seed-postgres.md`](docs/plans/02-plan-b-lod-seed-postgres.md), API 조사는 [`reports/`](reports/)에 있습니다.

```
LOD 덤프·SPARQL ─┐                      ┌─ silver.edition (ISBN-13 단위, 필드별 출처 기록)
                 ├─> bronze (원본 그대로) ─┤
Seoji API ───────┘                      └─> gold.search_doc (pg_bigm 한국어 부분일치 검색)
```

- **bronze**: LOD 리소스와 Seoji 응답을 원본 그대로, 해시로 변경 감지하며 보관합니다.
- **silver**: ISBN마다 소스별 후보를 만들고 필드 우선순위 규칙으로 병합합니다. 언제든 bronze만으로 다시 만들 수 있습니다(`seoji silver rebuild`).
- **gold**: 제목·저자·출판사·총서·권차·주제로 검색 문서를 만들고 pg_bigm으로 색인합니다.

### 왜 bronze / silver / gold인가

데이터 엔지니어링에서 흔히 쓰는 **메달리온 아키텍처(medallion architecture)** 용어입니다(Databricks가 퍼뜨린 이름). 데이터를 가공 단계에 따라 세 층으로 나누고, 동 → 은 → 금으로 갈수록 더 정제된 데이터라는 뜻입니다.

| 층 | 스키마 | 들어 있는 것 | 다시 만들 수 있나 |
|---|---|---|---|
| bronze | `bronze.*` | 받은 원본 그대로(`lod_resource`, `api_payload`, `source_record`)와 수집 진행 위치 | 아니요. 다시 받아야 합니다 |
| silver | `silver.*` | ISBN-13 단위로 정규화·병합한 책(`edition`), 저자, 세트, 주제, 필드별 출처 | 예. bronze만으로 `seoji silver rebuild` |
| gold | `gold.*` | 검색 문서(`search_doc`)와 `search_books()` | 예. silver만으로 `seoji gold rebuild` |

이렇게 나누면 다음과 같은 이점이 있습니다.

- **API를 다시 부르지 않고 규칙을 고칠 수 있습니다.** 병합 규칙이 틀렸으면 bronze에서 silver를 다시 계산하면 됩니다. 예를 들어 Seoji 세트 레코드 처리와 숫자 범위 검사를 고친 뒤, 590만 건을 재수집 없이 다시 만들었습니다.
- **문제가 생긴 단계를 가를 수 있습니다.** 원본이 원래 이상한지(bronze), 병합이 잘못됐는지(silver), 검색용 가공이 잘못됐는지(gold) 나눠서 봅니다.

CLI의 `seoji silver …`는 "병합 계산", `seoji gold …`는 "검색 색인"이라고 읽으면 됩니다.

## 설치

```bash
uv sync
docker compose up -d --build db     # PostgreSQL 17 + pg_bigm (포트 55432)
uv run seoji db migrate
```

설정은 환경변수나 저장소 루트의 `.env`에서 읽습니다(`.env.example` 참고). `.env`는 git에 올라가지 않습니다.

```
DATABASE_URL=postgresql://seoji:seoji@localhost:55432/seoji
SEOJI_CERT_KEY=발급받은키
```

## 데이터 넣기

### 1. LOD (키 불필요)

전체 덤프는 [LOD 데이터셋 다운로드](https://lod.nl.go.kr/home/dataset/datadownload.do)에서 받습니다. 받기 전에 소속·사용 목적을 적는 폼을 제출해야 합니다. 일반도서(전자책 포함)는 약 398만 건, TTL 약 1 GB입니다.

```bash
uv run seoji lod load 일반도서.ttl --format ttl --dump-date 2026-10-08
# 다음 덤프부터는 사라진 리소스를 tombstone 처리
uv run seoji lod load 일반도서.ttl --format ttl --dump-date 2027-01-08 --mark-missing
```

덤프 없이 몇 건만 시험하려면 SPARQL로 받습니다.

```bash
uv run seoji lod fetch KJU201703899 -o almond.rdf
uv run seoji lod load almond.rdf --format rdfxml
uv run seoji lod count          # SPARQL 기준 bibo:Book 수
```

### 2. Seoji API (키 필요)

[국립중앙도서관 Open API](https://www.nl.go.kr/NL/contents/N31101010000.do)에서 회원가입 → 인증키 신청 → 담당자 승인을 거쳐 키를 받습니다.

```bash
uv run seoji harvest --all                                 # 전체 (약 592만 건, 약 2.5시간), 중단 후 재실행하면 이어서
uv run seoji harvest --all --max-pages 100                 # 100페이지(10만 건)만 받고 멈춤
uv run seoji harvest --all --restart                       # 저장된 커서를 무시하고 처음부터
uv run seoji harvest --from 2022-05-09 --to 2022-05-09    # 발행예정일 기준, 하루씩 수집
uv run seoji harvest --window daily                        # [오늘-30, 오늘+90]
uv run seoji harvest --window weekly                       # [오늘-365, 오늘-31]
```

`--all`은 날짜 필터 없이 `sort=INPUT_DATE&order_by=ASC`, page_size 1000으로 끝까지 넘깁니다. 페이지마다 원본과 진행 위치(`bronze.harvest_cursor`)를 한 트랜잭션으로 커밋하므로, 중간에 끊겨도 다시 실행하면 마지막으로 커밋한 페이지부터 이어 받습니다. 새로 등록된 레코드는 정렬상 끝에 붙기 때문에, 다 받은 뒤 `--all`을 다시 실행하면 마지막 페이지부터만 확인해 새 등록분을 가져옵니다. 이미 받은 레코드의 수정(`UPDATE_DATE`)까지 반영하려면 주기적으로 `--restart`로 다시 훑습니다.

초당 1요청, 10초 타임아웃, 5xx는 1·2·4초 백오프로 재시도합니다. 오류 013(쪽당 출력건수 제한)이면 page_size를 절반으로 줄입니다. 저장되는 요청 파라미터에는 인증키가 들어가지 않습니다.

### 3. 병합과 검색

```bash
uv run seoji silver rebuild      # 전체 재계산 (gold 포함)
uv run seoji silver refresh      # 마지막 빌드 이후 바뀐 bronze만 반영
uv run seoji search "아몬드"
uv run seoji search "코난 46" --korean-only
uv run seoji report              # 소스 커버리지, 병합 이슈, 필드 채움률
```

SQL에서는 `SELECT * FROM gold.search_books('질의', 20, false);`로 검색합니다.

정기 실행 예시는 [`ops/crontab.example`](ops/crontab.example)에 있습니다.

## 조회 서버 (웹 · REST API · MCP)

`seoji serve` 하나로 웹 화면, REST API, MCP 서버가 함께 뜹니다. 세 경로 모두 `seoji.query` 모듈 하나를 거치므로 공개 정책도 한 곳에서 적용됩니다.

```bash
uv run seoji serve --port 8000          # http://localhost:8000
```

| 경로 | 내용 |
|---|---|
| `/` | 검색 화면 (HTML 한 장과 바닐라 JS, 빌드 단계 없음) |
| `GET /api/v1/search?q=…&limit=20&offset=0&korean_only=false` | 검색. `limit` 1~50, `offset` 0~1000, 다음 페이지가 있으면 `has_more: true`. 검색어 전체가 유효한 ISBN-10·13이면(하이픈·공백 허용) 그 책만 정확히 찾습니다 |
| `GET /api/v1/books/{isbn}` | 책 한 권. ISBN-10·13, 하이픈 허용 |
| `GET /api/v1/sets/{isbn}` | 세트와 소속 권 |
| `GET /api/v1/meta` | 출처 표시, 안내문, 게시중단 연락처, 마지막 빌드 시각 |
| `/api/openapi.json` | OpenAPI 스키마 (Swagger UI는 CDN 스크립트를 써서 CSP와 맞지 않아 끄고 스키마만 냅니다) |
| `/mcp` | MCP (Streamable HTTP, stateless). 도구: `search_books`, `get_book`, `get_book_set` |

Claude Code에 MCP를 붙이는 예시는 다음과 같습니다.

```bash
claude mcp add --transport http seoji http://localhost:8000/mcp
```

오류는 `{"error": {"code": "...", "message": "..."}}` 형태로 옵니다. 주요 상태 코드는 다음과 같습니다.
- 400: 잘못된 요청, 정책 범위를 넘은 요청 (검색어 100자·8단어 초과, 제어 문자 포함 등)
- 404: 없는 책
- 429: 요청 수 초과 또는 동시 요청 초과. `Retry-After` 헤더가 함께 옵니다
- 503: 검색 시간 초과, 서버가 바쁨(연결 대기 2초 초과), DB 오류

### 공개 정책

[`reports/서지 데이터 재배포 가능성.md`](reports/서지%20데이터%20재배포%20가능성.md)의 조사에 따라 다음과 같이 정했습니다.

- **사실 필드만 공개합니다.** `query.PUBLIC_EDITION_FIELDS` 허용 목록에 있는 필드만 밖으로 나갑니다. LOD 값은 CC0이고, Seoji 값은 국립중앙도서관이 공공데이터로 "이용허락범위 제한 없음"을 공표했으므로 영리 목적을 포함해 공개할 수 있다고 봅니다(아래 "라이선스·약관" 참고).
- **책소개·목차·서평·초록은 기본으로 막습니다.** 출판사·저자·평론가의 저작물일 수 있고, 공공데이터법도 제3자 권리가 담긴 정보는 "제한 없음"의 범위에서 뺍니다(제17조①2). 권리자의 이용 허락을 확인한 뒤에만 `SEOJI_PUBLIC_RICH_TEXT=true`와 GRANT로 엽니다.
- **표지는 원본 URL로만 연결합니다.** `http`는 `https`로 바꾸고, 사설·로컬 주소는 뺍니다. 이미지를 내려받거나 다시 올리지 않습니다.
- **대량 수집을 막습니다.** 요청당 최대 50건, offset 최대 1,000, IP별 분당 요청 수 제한을 둡니다. 서버 부하와 남용을 막기 위한 것이고, 데이터베이스제작자 권리에 대한 보수적 대응도 겸합니다.
- **게시중단 절차를 둡니다.** `seoji takedown add ISBN --reason "…"`으로 등록한 책은 웹·API·MCP 어디에도 나오지 않습니다. `seoji takedown list`, `seoji takedown remove ISBN`도 있습니다. 요청을 받을 연락처는 `SEOJI_CONTACT`로 지정하면 화면 하단과 `/api/v1/meta`에 표시됩니다.

### 보안 설정

별도 보안 검토(서브에이전트)를 거쳐 다음을 적용했습니다.

- **DB 권한을 최소로 줍니다.** 서버는 SELECT 권한만 가진 `seoji_public` 역할로 동작합니다(마이그레이션 010).
  - 권한은 조회 계층이 읽는 테이블에만 있습니다. `bronze.*`, 필드별 출처 기록, 책소개·목차·서평 테이블은 읽을 수 없습니다.
  - 그 위에 읽기 전용 트랜잭션과 `statement_timeout = 3s`를 겁니다.
  - 운영에서는 `seoji_public`에 로그인 권한을 주고 그 계정으로 접속하세요. `SET ROLE` 방식보다 강합니다. 세션이 원래 역할로 되돌아갈 수 없기 때문입니다.
    ```sql
    ALTER ROLE seoji_public LOGIN PASSWORD '…';
    ```
    그리고 `SEOJI_PUBLIC_DATABASE_URL=postgresql://seoji_public:…@host/seoji`을 설정합니다. 설정하지 않으면 `DATABASE_URL`로 접속한 뒤 연결마다 `SET ROLE seoji_public`을 합니다.
  - 책소개 등을 공개하려면 `SEOJI_PUBLIC_RICH_TEXT=true`와 함께 아래를 실행해야 합니다. 두 단계를 모두 거쳐야 열립니다.
    ```sql
    GRANT SELECT ON silver.edition_rich_text TO seoji_public;
    ```
- **검색 비용에 상한을 둡니다.**
  - 검색어는 NFKC 정규화한 뒤 100자·8단어 이하만 받고, 제어 문자는 거부합니다.
  - 순위를 매기는 후보는 최대 2만 건입니다. 이 덕분에 "이" 같은 한 글자 질의가 4.5초에서 0.1초로 줄었습니다.
  - 풀에서 연결을 2초 안에 못 얻으면 503으로 답합니다.
- **요청 수를 제한합니다.**
  - 대상 경로는 `/api/`, `/mcp`, `/healthz`입니다. 클라이언트마다 분당 요청 수(`SEOJI_RATE_LIMIT_PER_MINUTE`)와 동시 요청 4개로 제한합니다.
  - IPv6는 `/64` 단위로 묶습니다.
  - 이 제한은 프로세스 메모리 안에서 동작합니다. 여러 프로세스나 서버로 운영하면 리버스 프록시에서도 제한을 거세요.
- **Host와 Origin을 검증합니다.**
  - `SEOJI_ALLOWED_HOSTS`(기본 `localhost,127.0.0.1`)에 없는 Host는 400을 받습니다. MCP의 DNS rebinding 방어도 같은 목록을 씁니다.
  - 공개 배포 때는 실제 도메인을 넣으세요. 와일드카드(`*.example.org`)는 웹·API에서는 동작하지만 MCP에서는 정확히 일치해야 해서 421이 납니다.
- **CORS는 기본으로 꺼져 있습니다.** 다른 사이트의 방문자 브라우저가 이 API를 대신 긁어 가는 것을 막기 위해서입니다. 다른 웹 앱이 브라우저에서 이 API를 부르게 하려면 `SEOJI_CORS_ORIGINS`에 그 Origin을 적으세요. 서버 대 서버 호출에는 CORS가 필요 없습니다.
- **보안 헤더는 모든 응답에 붙습니다.** 400·429 응답도 포함됩니다.
  - CSP는 `script-src 'self'`(인라인 금지), `img-src 'self' https://www.nl.go.kr https://nl.go.kr`, `frame-ancestors 'none'`입니다.
  - 그 밖에 `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`를 붙입니다.
- **표지 URL은 허용 목록으로 거릅니다.** `www.nl.go.kr`과 `nl.go.kr`만 남기고, `https`로 바꾸고, 사용자 정보나 비표준 포트가 붙은 URL은 버립니다.
- **프록시 뒤에서 운영할 때**는 `SEOJI_TRUST_FORWARDED_FOR=true`로 두고 `seoji serve --forwarded-allow-ips <프록시 IP>`로 실행합니다. `*`는 쓰지 마세요. HSTS는 프록시에서 설정합니다.

| 환경변수 | 기본값 | 설명 |
|---|---|---|
| `SEOJI_PUBLIC_DATABASE_URL` | 없음 | `seoji_public`으로 로그인하는 접속 URL (권장) |
| `SEOJI_PUBLIC_RICH_TEXT` | `false` | 책소개·목차·서평·초록 공개 여부 (GRANT도 필요) |
| `SEOJI_CONTACT` | 없음 | 게시중단·정정 요청 연락처 |
| `SEOJI_RATE_LIMIT_PER_MINUTE` | `60` | 클라이언트별 분당 요청 수 |
| `SEOJI_ALLOWED_HOSTS` | `localhost,127.0.0.1` | 허용 Host 목록 (쉼표 구분) |
| `SEOJI_CORS_ORIGINS` | 없음 | 브라우저 교차 출처 호출을 허용할 Origin 목록 |
| `SEOJI_TRUST_FORWARDED_FOR` | `false` | 리버스 프록시의 `X-Forwarded-For` 신뢰 |

## 병합 규칙 요약

| 필드 | 우선순위 |
|---|---|
| 제목·책임표시·저자·출판사·KDC·쪽수·총서 등 | LOD → Seoji |
| 가격·부가기호·형태·전자책 여부·표지 URL·납본 여부·판형 | Seoji → LOD |
| 발행일 | Seoji 납본(Y)이고 LOD와 연도가 같으면 Seoji(일 단위), 아니면 LOD(연 단위), LOD가 없으면 Seoji 예정일 |

빈 값, `"0"`, 범위를 벗어난 값은 다음 순위로 넘어갑니다. 모든 후보 값은 `silver.field_provenance`에, 채택된 출처는 `silver.edition.provenance`에 남습니다. ISBN이 다른 레코드는 절대 합치지 않습니다.

## 라이선스·약관

> 법률 자문이 아닙니다. 근거와 판단 과정은 [`reports/서지 데이터 재배포 가능성.md`](reports/서지%20데이터%20재배포%20가능성.md)에 있습니다(2026-10-25 개정).

| 데이터 | 이용 조건 | 이 저장소의 처리 |
|---|---|---|
| 국가서지 LOD | 공공누리 제1유형 + CC0 1.0. 영리 이용·재배포 자유, 출처 표시 권장 | 사실 필드를 자유롭게 공개 |
| Seoji 서지 사실 필드 (ISBN, 서명, 저자, 출판사, 가격, 부가기호, 세트, 형태, 발행일 등) | 국립중앙도서관이 공공데이터로 등록, [data.go.kr 3078982](https://www.data.go.kr/data/3078982/openapi.do) 이용허락범위 **"제한 없음"** | 출처("국립중앙도서관 ISBN 서지정보")를 표시해 공개 |
| Seoji 책소개·목차·서평, LOD 목차·초록 | 출판사·저자·평론가 등 제3자 저작물일 수 있음 | `silver.edition_rich_text`에 `redistributable=false`로 분리, 공개 서버 역할은 읽기 권한 없음 |
| 표지 이미지 | 일러스트·사진 등 제3자 저작물 | URL만 저장하고 원 서버로 핫링크. 이미지를 내려받거나 다시 올리지 않음 |

**Seoji 사실 필드를 공개해도 된다고 보는 근거**
- 「공공데이터의 제공 및 이용 활성화에 관한 법률」 제3조④: 공공기관은 다른 법률에 특별한 규정이 있거나 제28조①의 제공중단 사유에 해당하는 경우를 빼고는 **"공공데이터의 영리적 이용인 경우에도 이를 금지 또는 제한하여서는 아니 된다."**
- 같은 법 제3조③은 공개된 공공데이터의 접근 제한 같은 이용저해행위를 금지하고, 제4조는 다른 법률에 특별한 규정이 없으면 이 법을 따르라고 정합니다.
- API 키를 받을 때 동의하는 국립중앙도서관 통합회원 약관에는 영리 이용·제3자 제공에 사전 승낙을 요구하는 조항이 있습니다. 하지만 약관은 "법률"이 아니라 제3조④의 예외가 될 수 없다고 봅니다.

**남는 한계**
- 제3자 저작물은 "제한 없음"에 포함되지 않습니다(제17조①2). 그런 줄 알면서 이용하면 제36조③의 면책도 받지 못합니다.
- 기관 업무에 상당한 지장을 줄 만큼 무리하게 수집하면 제공이 중단될 수 있습니다(제28조①). 수집은 초당 1회 수준으로 천천히 합니다.
- 국립중앙도서관 디지털정보기획과(02-590-0548)의 서면 확인은 필수가 아닙니다. 회원 약관과의 충돌까지 정리하고 싶을 때 받습니다.
- 정보나루·카카오·KPIPA 등 다른 소스는 이 DB에 섞지 않습니다.

## 알려진 한계

- LOD에는 만화 시리즈처럼 **리소스 하나에 ISBN 수십 개**인 묶음 레코드가 많습니다. ISBN마다 edition을 만들고 권차 한정어(`(4)`, `(제4권)`)를 `volume_label`로 쓰지만, 발행연도·쪽수는 묶음 전체의 값(예: `2006-2014`의 시작 연도, `15책`)이라 권별로 정확하지 않습니다. Seoji 레코드가 있으면 발행일은 보정됩니다.
- LOD는 "한국 도서"가 아니라 "국중 소장 자료"라 외국 ISBN도 들어 있습니다. `is_korean`(접두 978-89, 979-11)과 `--korean-only`로 거릅니다.
- 국가서지 데이터에는 체크섬이 틀린 ISBN이 실제로 있습니다(세트 ISBN 오타, `97811…` 등). 이런 값은 버리지 않고 `silver.merge_issue(kind='invalid_isbn')`에 남깁니다.

## 컨테이너 이미지

main에 push하면 GitHub Actions(`.github/workflows/images.yml`)가 이미지 두 개를 GHCR에 올립니다.

| 이미지 | 태그 | 용도 |
|---|---|---|
| `ghcr.io/moreal/seoji` | `latest`, `sha-<7자리>` | CLI와 서버. 기본 명령은 `seoji serve --host 0.0.0.0`이고, `harvest …`나 `db migrate`처럼 인자를 주면 그 하위 명령을 실행합니다 |
| `ghcr.io/moreal/seoji-postgres` | `17-latest`, `17-sha-<7자리>` | CloudNativePG용 PostgreSQL 17 + pg_bigm(`docker/postgres-cnpg/`). 로컬 개발용 `docker/postgres/`와 같은 pg_bigm 빌드입니다 |

```bash
docker build -t seoji .
docker run --rm -e DATABASE_URL=postgresql://seoji:seoji@host.docker.internal:55432/seoji seoji db migrate
```

## 개발

```bash
uv run pytest            # Docker의 db가 떠 있어야 합니다 (테스트마다 임시 DB 생성)
uv run ruff check && uv run ruff format --check
bash scripts/fetch_lod_fixtures.sh   # LOD 테스트 픽스처 다시 받기
```

`tests/fixtures/nlseoji/page_*.json`·`error_*.json`은 수집 동작(페이징, 오류 코드, 잘못된 ISBN)을 시험하는 **합성 데이터**이고, `real_20220509_sample.json`은 **실제 Seoji 응답에서 고른 8건**입니다(책소개·목차·서평 본문은 지웠습니다).

## 검증 기록

**2026-10-22, 키·덤프 없이 SPARQL 실데이터로 종단 검증**

- SPARQL로 한국 ISBN(`97911`/`97889` 접두) 리소스 200건씩 5번 받음 → 중복 제외 947개 리소스.
- `seoji lod load` → `bronze.lod_resource` 947행.
- `seoji silver rebuild` 4.2초 → 후보 10,790개, edition 10,731개, 이슈 87건(`invalid_isbn` 49, `multi_lod` 38).
- `seoji search` 아몬드·역사·헌터·수학·"코난 46" 모두 기대한 결과가 나왔고, 실행 계획에서 `search_doc_bigm` 인덱스가 쓰였습니다.
- 채움률: 제목·출판사·발행일·KDC 100%, 권차 91.8%, 쪽수 1.9%(묶음 레코드 영향). 가격·부가기호·표지는 0%(Seoji 미수집).

**2026-10-22, 실제 Seoji API**

- `seoji harvest --from 2022-05-09 --to 2022-05-09` → 8번 요청(page_size 100)으로 721건을 받았습니다. 응답 엔벌로프는 `{"PAGE_NO", "TOTAL_COUNT", "docs": [...]}`이고, 저장된 응답과 요청 파라미터 어디에도 인증키가 없었습니다.
- 실제 응답에서 발견해 반영한 것:
  - `EA_ISBN`이 비고 `SET_ISBN`만 있는 레코드(그날 51건)는 **세트 자체**의 레코드입니다. `SET_EXPRESSION`("전6권")은 이 레코드에만 있고 개별 권에는 없습니다. 세트 ISBN의 edition으로 만들고 `book_set.total_volumes`를 여기서 채웁니다.
  - 명세에 없는 `REAL_PUBLISH_DATE`(실제 발행일)가 있으면 발행예정일보다 우선합니다.
  - `FORM`에 "오디오북"이 있어 `binding='audio'`로 분류합니다.
  - 역할어 "삽화가(그림작가)"를 그림으로 인식합니다.
  - `PRE_PRICE`에 "비매품/무료", "연재가" 같은 문자열이 옵니다(가격 없음으로 처리). `BOOK_SIZE`에 "0*0"이 옵니다(무시).
  - 그날 `KDC`·`DDC`·`CONTROL_NO`는 전부 비어 있었고, `SUBJECT`는 KDC 대분류 한 자리 숫자였습니다.
- 한도와 전체 규모:
  - `page_size` 200·500·1000 모두 오류 013 없이 동작했습니다.
  - **날짜 필터 없이도 조회되며 전체는 5,918,366건**입니다. `sort=INPUT_DATE&order_by=ASC`, `page_size=1000`으로 5,918번째 페이지까지 1.5초 안팎에 응답했습니다. 즉 약 5,919번 요청(초당 1회 기준 약 2.5시간)으로 전체를 받을 수 있습니다.
  - 발행예정일에는 `00010101`, `1000xxxx` 같은 오입력이 있습니다. 1990년부터 날짜 구간으로 훑으면 이런 레코드를 놓치므로, 초기 적재는 `seoji harvest --all`(필터 없는 전체 페이징)로 합니다.
  - 같은 깊은 페이지(2000번째)를 두 번 요청하면 순서까지 같았고, 이웃 페이지와 겹치는 레코드는 없었습니다. `--all --max-pages 2`로 2,000건을 2.9초에 받았습니다.

## 전체 덤프를 받은 뒤 할 일

LOD 덤프를 적재한 뒤 `uv run seoji lod count`와 `SELECT count(*) FROM bronze.lod_resource`를 대조합니다(덤프 표기 3,980,216건 ±1%).
