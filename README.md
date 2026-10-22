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
uv run seoji harvest --from 2022-05-09 --to 2022-05-09    # 발행예정일 기준, 하루씩 수집
uv run seoji harvest --window daily                        # [오늘-30, 오늘+90]
uv run seoji harvest --window weekly                       # [오늘-365, 오늘-31]
```

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

## 병합 규칙 요약

| 필드 | 우선순위 |
|---|---|
| 제목·책임표시·저자·출판사·KDC·쪽수·총서 등 | LOD → Seoji |
| 가격·부가기호·형태·전자책 여부·표지 URL·납본 여부·판형 | Seoji → LOD |
| 발행일 | Seoji 납본(Y)이고 LOD와 연도가 같으면 Seoji(일 단위), 아니면 LOD(연 단위), LOD가 없으면 Seoji 예정일 |

빈 값, `"0"`, 범위를 벗어난 값은 다음 순위로 넘어갑니다. 모든 후보 값은 `silver.field_provenance`에, 채택된 출처는 `silver.edition.provenance`에 남습니다. ISBN이 다른 레코드는 절대 합치지 않습니다.

## 라이선스·약관 주의

- LOD는 공공누리 제1유형 + CC0 1.0입니다.
- Seoji의 목차·책소개·서평과 LOD의 초록은 제3자 저작물일 수 있어 `silver.edition_rich_text`에 `redistributable=false`로 따로 둡니다. 재배포할 때는 빼세요.
- 표지는 URL만 저장합니다(핫링크).
- 정보나루·카카오 등 다른 소스는 이 DB에 섞지 않습니다.

## 알려진 한계

- LOD에는 만화 시리즈처럼 **리소스 하나에 ISBN 수십 개**인 묶음 레코드가 많습니다. ISBN마다 edition을 만들고 권차 한정어(`(4)`, `(제4권)`)를 `volume_label`로 쓰지만, 발행연도·쪽수는 묶음 전체의 값(예: `2006-2014`의 시작 연도, `15책`)이라 권별로 정확하지 않습니다. Seoji 레코드가 있으면 발행일은 보정됩니다.
- LOD는 "한국 도서"가 아니라 "국중 소장 자료"라 외국 ISBN도 들어 있습니다. `is_korean`(접두 978-89, 979-11)과 `--korean-only`로 거릅니다.
- 국가서지 데이터에는 체크섬이 틀린 ISBN이 실제로 있습니다(세트 ISBN 오타, `97811…` 등). 이런 값은 버리지 않고 `silver.merge_issue(kind='invalid_isbn')`에 남깁니다.

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
  - 발행예정일에는 `00010101`, `1000xxxx` 같은 오입력이 있습니다. 1990년부터 날짜 구간으로 훑으면 이런 레코드를 놓치므로, 초기 적재는 필터 없는 전체 페이징이 낫습니다(아직 구현 안 됨).

## 전체 덤프를 받은 뒤 할 일

LOD 덤프를 적재한 뒤 `uv run seoji lod count`와 `SELECT count(*) FROM bronze.lod_resource`를 대조합니다(덤프 표기 3,980,216건 ±1%).
