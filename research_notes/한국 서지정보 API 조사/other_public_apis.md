# Korean public-sector book and bibliographic data APIs and bulk datasets other than NLK's own catalog APIs (as of Oct 2026)

Scope note: 도서관 정보나루 (data4library.kr) is operated by 국립중앙도서관 (NLK). It is included because the assignment lists it explicitly, and it is a separate product from NLK's catalog and ISBN APIs. Its terms name "국립중앙도서관(이하 "도서관")이 운영하는 도서관 빅데이터 분석플랫폼" as the operator ([data4library 이용약관](https://www.data4library.kr/newSub01_01)). NLK's own ISBN 서지정보 and 소장자료 APIs are left to other researchers. They appear here only as cross-references ([data.go.kr 3078982 ISBN서지정보](https://www.data.go.kr/data/3078982/openapi.do), [culture.go.kr 도서 API 목록](https://www.culture.go.kr/data/openapi/openapiList.do?category=F)).

## Q1. Service-by-service inventory: endpoints, parameters, fields, authentication, quotas, license, bulk access

### Takeaway
도서관 정보나루 is by far the richest non-catalog public source. It has 19 REST endpoints in XML or JSON, a new MCP server, and 1,678 monthly per-library holdings/loan datasets. The daily cap is 30,000 calls when a server IP is registered and roughly 500 calls without one. Its terms restrict copying, redistributing and commercially using cover images. KPIPA, NANET, RISS and local governments offer narrower APIs, and each has tighter approval or license rules.

### Cited Findings

#### A. 도서관 정보나루 (data4library.kr) Open API

**General**
- The official API manual downloads as a 70-page PDF stamped "v20260620", so it is the June 2026 edition. Its table of contents lists 19 APIs plus a code appendix: 1 정보공개 도서관 조회, 2 도서관별 장서/대출 데이터 조회, 3 인기대출도서 조회, 4 마니아를 위한 추천도서, 5 다독자를 위한 추천도서, 6 도서 상세 조회, 7 도서 키워드 목록, 8 도서별 이용 분석, 9 도서관/지역별 인기대출 도서, 10 도서관별 대출반납추이, 11 도서관별 도서 소장여부 및 대출 가능여부, 12 대출 급상승 도서, 13 도서 소장 도서관 조회, 14 도서관별 통합정보, 15 도서관별 인기대출도서 통합, 16 도서 검색, 17 이달의 키워드, 18 지역별 독서량/독서율, 19 신착도서 조회, 20 코드 — [data4library API manual (PDF, v20260620)](https://www.data4library.kr/downloadApiManual)
- The base URL is `http://data4library.kr/api/{endpoint}`, and every call needs `authKey`. The manual's examples all use plain `http://` — [API manual](https://www.data4library.kr/downloadApiManual); [Open API 활용방법](https://www.data4library.kr/apiUtilization)
- Responses default to XML. `format=json` returns JSON on every endpoint. JSON was added on 2017-07-10 — [notice cn=93](https://data4library.kr/noticeV?cn=93); [API manual](https://www.data4library.kr/downloadApiManual)
- Getting a key takes four steps: 회원가입, then 인증키 신청, then 인증키 발급, then API use. The page says only that "인증키는 발급 신청 후, 사용 가능합니다" — [Open API 활용방법](https://www.data4library.kr/apiUtilization)

**Quotas**
- From 2017-04-10, a client making more than 500 calls/day must register three things: its calling server IP, its organization name, and its purpose (up to 200 characters). "IP가 등록되지 않은 1일 500건 이상 API 호출은 제한이 됩니다." New users register at application time; existing users register in 마이페이지 — [notice cn=88 (2017-03-29)](https://data4library.kr/noticeV?cn=88)
- From 2023-11-20, IP-registered users are capped at "1일 30,000건". They previously had no daily cap. The stated reason is server overload from excessive calls. The notice describes no process for requesting more — [notice cn=194 (2023-11-10)](https://www.data4library.kr/noticeV?cn=194)
- Third-party confirmation: one open-source project configures 정보나루 at 30,000/day and blocks itself at 28,500 — [chanyong1027/checkbook PR #39](https://github.com/chanyong1027/checkbook/pull/39)

**Endpoints**

All parameters are listed in addition to `authKey` and `format`. The source for every row is the [API manual v20260620](https://www.data4library.kr/downloadApiManual).

| # | Endpoint | Key request params | Response fields (exact tag names) | Notes |
|---|---|---|---|---|
| 1 | `libSrch` | libCode, region, dtl_region, pageNo, pageSize (default 10) | pageNo, pageSize, numFound, resultNum, libs/lib: libCode, libName, address, tel, fax, latitude, longitude, homepage, closed, operatingTime, BookCount | BookCount = number of volumes held |
| 2 | `itemSrch` (도서관별 장서/대출) | **libCode (required)**; either `type=ALL` or startDt/endDt (these filter by **registration date**, yyyy-mm-dd); isbn13 (up to 5, `;`-separated); kdc; dtl_kdc; pageNo; pageSize (**default 100**) | libNm, numFound, resultNum, docs/doc: bookname, authors, publisher, publication_year, isbn13, set_isbn13, bookImageURL, addition_symbol, vol, class_no, class_nm, callNumbers/callNumber: separate_shelf_code, separate_shelf_name, book_code, shelf_loc_code, shelf_loc_name, copy_code; reg_date | Only endpoint giving per-library call numbers and copy (복본) codes; the main bulk path |
| 3 | `loanItemSrch` (인기대출도서) | startDt, endDt, gender, from_age/to_age or age, region, dtl_region, book_dvsn (big=large print / oversea=foreign), addCode, kdc, dtl_kdc, pageNo, pageSize (default 200) | resultNum, numFound, docs/doc: no, ranking, bookname, authors, publisher, publication_year, isbn13, addition_symbol, vol, class_no, class_nm, bookImageURL, bookDtlUrl, loan_count | Aggregated by ISBN; **maximum 5,000 titles**; endDt alone defaults startDt to 2014-01-01 |
| 4/5 | `recommandList` (type=mania default / type=reader) | isbn13 (10 or 13 digits, up to 5 `;`-separated) | resultNum, docs/book: no, bookname, authors, publisher, publication_year, isbn13, addition_symbol, vol, class_no, class_nm, bookImageURL | Uses 36 months of loans; up to 200 titles |
| 6 | `srchDtlList` (도서 상세) | isbn13 (10 or 13 digits), loaninfoYN (Y/N, default N), displayInfo (gender/age/region) | detail/book: no, bookname, authors, publisher, publication_date, publication_year, isbn, isbn13, addition_symbol, vol, class_no, class_nm, description, bookImageURL; loanInfo: Total(ranking, name, loanCnt), regionResult/region, ageResult/age, genderResult/gender (each ranking, name, loanCnt) | Loan info covers the last 90 days, top 1,000 per condition |
| 7 | `keywordList` | isbn13, additionalYN | resultNum, items/item: word, weight; additionalItem: bookname, authors, publisher, publication_year, isbn13, vol | Up to 50 keywords per book |
| 8 | `usageAnalysisList` | isbn13 (10 or 13 digits) | book: bookname, authors, publisher, publication_year, isbn13, addition_symbol, vol, class_no, class_nm, description, bookImageURL, loanCnt; loanHistory/loan: month, loanCnt, ranking; loanGrps/loanGrp: age, gender, loanCnt, ranking; keywords/keyword: word, weight; coLoanBooks, maniaRecBooks, readerRecBooks (each book: bookname, authors, publisher, publication_year, isbn13, vol) | 12-month monthly loan history; loan groups over 30 days; co-loans over 36 months, up to 10; `recBooks` was removed after 2023-03-31 |
| 9 | `loanItemSrchByLib` | one of libCode, region or dtl_region (required); same filters as #3; pageSize default 200 | libNm/regionNm/dtlregionNm, resultNum, docs/doc: no, ranking, bookname, authors, publisher, publication_year, isbn13, addition_symbol, vol, class_no, class_nm, bookImageURL, bookDtlUrl, loan_count | Maximum 200; per-library queries give rank only, without loan_count; at least 3 months of range is recommended |
| 10 | `usageTrend` | libCode, type (D=weekday / H=hour) | libNm, results/result: dayOfWeek or hour, loan, return (relative %) | 30-day window |
| 11 | `bookExist` | libCode, isbn13 | result: hasBook, loanAvailable | loanAvailable reflects **the previous day's** status |
| 12 | `hotTrend` | searchDt (yyyy-mm-dd) | results/result: date, docs/doc: no, difference, baseWeekRank, pastWeekRank, bookname, authors, publisher, publication_year, isbn13, addition_symbol, vol, class_no, class_nm, bookImageURL, bookDtlUrl | Covers 3 days, top 5 per day |
| 13 | `libSrchByBook` | isbn, region (required), dtl_region, pageNo, pageSize | libs/lib: libCode, libName, address, tel, fax, latitude, longitude, homepage, closed, operatingTime | Libraries holding a given ISBN |
| 14 | `extends/libSrch` | libCode, region, dtl_region, pageNo, pageSize | libInfo (as #1, including BookCount), loanByhours, loanByDayofWeek, newBooks (bookname … set_isbn13 … reg_date) | 10 newest arrivals per library |
| 15 | `extends/loanItemSrchByLib` | libCode | loanBooks, age0Books, age6Books, age8Books, age14Books, age20Books (book: no, ranking, bookname, authors, publisher, publication_year, isbn13, addition_symbol, vol, class_no, class_nm, bookImageURL, bookDtlUrl) | Top 20 per age group, last 30 days |
| 16 | `srchBooks` | title, author, isbn13, keyword (`;` multi), publisher (AND-combined), sort (title/author/pub/pubYear/isbn/loan; default loan), order (asc/desc), exactMatch, pageNo, pageSize (default 20) | numFound, docs/doc: bookname, authors, publisher, publication_year, isbn13, addition_symbol, vol, class_no, class_nm, bookImageURL, bookDtlUrl, loan_count | With no criteria, searches all loan data; keyword search is exact-match only |
| 17 | `monthlyKeywords` | month (yyyy-mm) | keywords/keyword: word, weight | 100 TF-IDF keywords; available up to the previous month |
| 18 | `readQt` | region, dtl_region, year (2016 to last year), month | results/result: age, quantity, rate | Reading volume and reading rate by region |
| 19 | `newArrivalBook` | libCode, searchDt (yyyy-mm) | libNm, numFound, docs/doc: bookname, authors, publisher, publication_year, isbn13, set_isbn13, bookImageURL, addition_symbol, vol, class_no, class_nm, reg_date | New in this manual edition |

**Codes (manual appendix)**
- gender: 0 남, 1 여, 2 미상 — [API manual](https://www.data4library.kr/downloadApiManual)
- age: 0, 6, 8, 14, 20, 30, 40, 50, 60, -1, plus a8/a10/a12 (school grades) and a14/a17 — [API manual](https://www.data4library.kr/downloadApiManual)
- ISBN 부가기호 (addCode/addition_symbol): 0 교양, 1 실용, 2 여성, 4 청소년, 5 학습참고서1(중고), 6 학습참고서2(초등), 7 아동, 9 전문 — [API manual](https://www.data4library.kr/downloadApiManual)
- kdc 대주제 0–9 and dtl_kdc 2-digit 세부주제 (00 총류 … 99), plus region and dtl_region codes — [API manual](https://www.data4library.kr/downloadApiManual)

**License, terms and the cover-image restriction**
- Every book-returning endpoint carries this rule: "bookImageURL 은 비영리 서비스의 화면 표시에 한하여 이용 가능하며, 영리적 목적의 이용과 복사저장재배포 및 AI 입력학습 등 그 밖의 활용을 금함" — [API manual v20260620](https://www.data4library.kr/downloadApiManual)
- Terms of use, 제12조①5, list as grounds for restriction: "서비스를 통해 얻은 정보를 도서관의 사전 승낙 없이 서비스 이용 외의 목적으로 복제하거나, 이를 출판 및 방송 등에 사용하거나, 제3자에게 제공하는 행위". 제11조③ forbids third parties from reusing 도서관-owned content on other sites without permission. The terms have been in effect since 2019-07-17. The previous operator was KISTI — [data4library 이용약관](https://www.data4library.kr/newSub01_01)
- No 공공누리 (KOGL) license type appears on the API page or the data pages. The footer reads "© National Library of Korea. All rights reserved." — [openDataL](https://www.data4library.kr/openDataL)
- The platform describes itself as serving "사서, 연구(기획)자, 민간사업자" for analysis and new services. It provides 회원·장서·대출 data with personal and sensitive data excluded — [도서관 정보나루 소개](https://www.data4library.kr/openCenter)

**MCP server (new)**
- data4library now publishes an "MCP 활용방법" page and an MCP manual. It lists 16 tools: search_libraries, get_popular_loans, get_book_recommendations, get_book_full_profile, get_book_keywords, get_book_analysis, check_book_availability, and others. auth_key is injected by the client. The page states that holdings data "월 단위로 갱신되어 실시간 재고와 시차가 있을 수 있습니다" — [MCP 활용방법](https://www.data4library.kr/mcpUtilization)

**Bulk per-library holdings/loan datasets (장서/대출데이터)**
- The 장서/대출데이터 list returned "1,678 건의 데이터". Each row is one library's "장서/대출 데이터" with region, 공개범위 "장서/대출", a "최근 데이터 제공일", and the access types "Text" and "API". Most rows showed a latest provision date of 2026-10-01, which implies a monthly cycle. Some libraries have stopped publishing; for example, one row read "최근 데이터 제공일 2024-10-01 현재는 Data가 공개되지 않는 도서관 입니다." Observed 2026-10-22 via the page's own `/openDataL/search` call — [openDataL](https://www.data4library.kr/openDataL)
- Downloading requires login and an issued 인증키. Each dataset then needs an "추가 이용신청", which sits in "승인대기" until approved. Library-list download goes through `/libDataDownload` — [common-data.js](https://www.data4library.kr/resources/js/common-data.js)
- The 참여 도서관 list can be filtered by region, sub-region and library type (공공 / 작은), and has a download button — [libDataL](https://www.data4library.kr/libDataL)

#### B. 한국출판문화산업진흥원 (KPIPA) 출판유통통합전산망 (bnk.kpipa.or.kr) Open API
- An Open API exists, governed by the "출판유통통합전산망 Open API 서비스 이용약관". It was enacted 2022-06-24 and amended 2022-09-30, 2023-01-25, 2023-12-27, 2024-10-30 and 2025-08-01, with the last amendment effective 2025-08-11 — [KPIPA Open API 약관](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)
- **Scope:** The API covers publisher-registered metadata (도서 정보), "그 중에서 Open API 서비스 제공에 동의한 출판사의 도서 정보에 한한다" — [KPIPA Open API 약관 제2조③](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi). Only titles with a publication date on or after 2021-09-29 whose publisher opted in are delivered — [KPIPA newsletter 2023-08-14](https://bnkkpipa.stibee.com/p/12)
- **Data model:** Metadata is entered through an ONIX 3.0-based form. It is pushed to linked bookstores and distributors every 5 minutes, and it is pre-filled from the publisher's ISBN application data — [메타데이터 서비스](https://bnk.kpipa.or.kr/home/v3/center/centerGuideServiceMetaData)
- **Key issuance and approval:** Applicants join the 통합전산망 and apply for a key. The 통합전산망 운영위원회 reviews the application and may reject it. Publishers using their own data, libraries, and system operators who send data to the network can be fast-tracked. Applicants must be over 14. Keys last 1 year and are renewable yearly; renewal must be requested 30 days before expiry and is decided within 15 days. The application form (별표1) requires a company profile, a contact person, a use category (비영리 / 영리 / 자사데이터), a use type (web, app, academic, contest, other), a detailed service description, and a service URL — [KPIPA Open API 약관 제4조, 별표1](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)
- **Commercial use:** Allowed, "다만 상업적인 목적으로 이용하고자 하는 경우에는 서비스 신청 시 제출한 활용 정보 내에서만 활용이 가능". Commercial applications go through committee deliberation — [제5조](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)
- **Redistribution and display:** Users may not copy, publish or broadcast the data, or give it to third parties, for profit or not, without prior consent (제8조③2). Users must "다른 정보와 혼합하지 않고 독립적으로 노출" and clearly attribute the 통합전산망 as the source (제8조⑤). KPIPA may limit scope, hours or call counts with notice (제6조①). There is no warranty of accuracy or continuity (제10조) — [KPIPA Open API 약관](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)
- KPIPA's public site also shows sales, reader, loan-popularity and 정가변경 statistics pages (adiStatsCtgSaleRank, adiStatsSaleReader, adiNetprcPublicList, and others) and 신간 / 출간예정 lists. The site itself does not say whether these are reachable by API — [KPIPA sitemap](https://bnk.kpipa.or.kr/home/v3/center/centerGuideSiteMap)
- On data.go.kr, KPIPA publishes only small files: 청소년 유해간행물 목록 (XLSX), 세종도서 선정목록, 기관별 추천도서. Through culture.go.kr linked data it adds 이달의읽을만한책, 대학신입생추천도서, 세종도서-학술 and 손안애서. There is no book-metadata dump — [data.go.kr search "한국출판문화산업진흥원"](https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword=%ED%95%9C%EA%B5%AD%EC%B6%9C%ED%8C%90%EB%AC%B8%ED%99%94%EC%82%B0%EC%97%85%EC%A7%84%ED%9D%A5%EC%9B%90)

#### C. 국회도서관 (NANET) Open API
- The API is served only through data.go.kr. The user joins data.go.kr and applies there, and the key is the data.go.kr `ServiceKey`. A development account gets about 10,000 calls/day; an operating account gets up to 100,000/day — [NANET OpenAPI 가이드 S1001](https://openapi.nanet.go.kr/S1001.html)
- There are four REST endpoints, all GET, UTF-8 and XML — [S2001](https://openapi.nanet.go.kr/S2001.html):
  - `http://apis.data.go.kr/9720000/searchservice/basic` (통합검색)
  - `http://apis.data.go.kr/9720000/searchservice/detail` (상세검색)
  - `http://apis.data.go.kr/9720000/detailinfoservice/detail` (상세정보)
  - `http://apis.data.go.kr/9720000/detailinfoservice/toc` (목차)
- **basic** takes `pageno`, `displaylines` (1–100), and `search` in the form "category,검색키워드[|category,키워드]". Categories are 전체, 자료명, 저자, 발행자, 키워드, 청구기호, AND-combined. The response is `total` plus repeated `record/item` entries with **name/value pairs**, for example 제어번호 KDMT1200305094, 자료명/저자사항, 자료실, 청구기호, 학위, 학위년도, 목차 Y, DB — [S3002_01_01](https://openapi.nanet.go.kr/S3002_01_01.html)
- **detail** adds `dbname` (fixed) and `option` (publication-year range, plus 원문유무 1/0) — [data.go.kr 15098174 swagger](https://www.data.go.kr/data/15098174/openapi.do). **toc** takes `controlno`, for example MONO1201027232, and returns resultCode, resultMsg, toc — [data.go.kr 15098175](https://www.data.go.kr/data/15098175/openapi.do)
- **License:** "공공저작물 : 출처표시 (제 1유형)", which is KOGL Type 1 (attribution; commercial use and modification allowed). Approval is listed as 심의승인 on 15098174. On 15098175 the development stage is auto-approved and the operating stage is reviewed. Updates are real time and the service is free — [data.go.kr 15098174](https://www.data.go.kr/data/15098174/openapi.do); [15098175](https://www.data.go.kr/data/15098175/openapi.do)
- **Error codes:** 22 = daily limit exceeded, 30 = unregistered key, 31 = expired key, 32 = unregistered IP — [S4001](https://openapi.nanet.go.kr/S4001.html)
- A one-off CSV file dataset, "국회도서관_국가학술정보 데이터셋", was last updated 2019-11-14. It covers academic fusion data, committee minutes and researcher/keyword analysis rather than book metadata — [data.go.kr search "국회도서관"](https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword=%EA%B5%AD%ED%9A%8C%EB%8F%84%EC%84%9C%EA%B4%80)

#### D. RISS (한국교육학술정보원 KERIS) 단행본 API
- RISS offers 8 search API types: 학위논문, 국내/해외학술논문, 단행본, 연구보고서, 학술지, 공개강의, CALIS. The 단행본 API "국내 대학도서관이 보유하고 있는 단행본 서지정보를 제공". The stated target is non-profit institutions (universities) that embed RISS search in their own sites; applications go through `/openAPI/OpenApiRegister.do` — [RISS 검색 API 소개](https://www.riss.kr/apicenter/apiSearchIntro.do)
- **Request:** `http://www.riss.kr/openApi?key=…&version=1.0&type=U&keyword=…` with title, author, subject, publisher, isbn, toc, spubdate, epubdate, stype (ab=books / nb=non-book / eb=e-book), lang, sort (T/A/Y), asc, rsnum, and rowcount (up to 100) — [RISS 단행본 API](https://www.riss.kr/apicenter/apiSearchBook.do)
- **Response (XML):** totalcount, riss.type, title, author, publisher, pubdate, mtype, abstract/toc/image flags, **holdings, holdings_code**, url — [RISS 단행본 API](https://www.riss.kr/apicenter/apiSearchBook.do)
- **Approval and license:** "심사 후 승인"; license **BY-NC-ND**, meaning no commercial use and no derivatives — [RISS 단행본 API](https://www.riss.kr/apicenter/apiSearchBook.do)

#### E. 공공데이터포털 (data.go.kr) and 문화공공데이터광장 (culture.go.kr): book-related datasets
- A data.go.kr search for "도서관 장서" returned 227 datasets: 204 file, 12 Open API and 11 linked. They are mostly per-library or per-municipality, for example 경상북도교육청구미도서관 도서정보 (3068857), 제주공공도서관 장서현황 (15058935), 제주 도서검색 (15057476), 둔산도서관 도서현황 (15108153) and 용인시 도서대출 순위 (3038397) — [data.go.kr search](https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword=%EB%8F%84%EC%84%9C%EA%B4%80+%EC%9E%A5%EC%84%9C)
- A search for "장서 대출목록" returned 27 datasets. None are a nationwide NLK or 정보나루 holdings dump; they are local lists such as 서울도서관 인기대출 100선 (15051849), 마포중앙도서관 상위 500 (15119989), and 울산광역시_도서_정보 (15098019, including loan status) — [data.go.kr search](https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword=%EC%9E%A5%EC%84%9C+%EB%8C%80%EC%B6%9C%EB%AA%A9%EB%A1%9D)
- 전국도서관표준데이터 (15013109) holds facility and operations data with only **aggregate** counts (도서/연속간행물/비도서 자료수), not title-level records. It comes from 303 providers, is updated annually, and is available as CSV, XLS, XML, JSON, RDF or API — [data.go.kr 15013109](https://www.data.go.kr/data/15013109/standard.do)
- The culture.go.kr "도서" category lists 32 APIs. Ones relevant to books: 국립어린이청소년도서관 사서추천도서 (id 674, ISBN included), 국립세종도서관 새로들어온책 (652), 한국문학번역원 번역 전문도서관 소장자료 (609) and 번역출간 도서정보 (608), and 국립중앙도서관 소장자료 (468). No license type is shown per API — [culture.go.kr 도서 API](https://www.culture.go.kr/data/openapi/openapiList.do?category=F)
- 경기도서관 has an e-book Open API: `https://ebook.library.kr/api/open-search/ebook`. Parameters are ServiceKey, pageNo, numOfRows, sort, ebookType (ebook/audiobook), searchType and searchKeyword. Fields are PK, TITLE, AUTHOR, PUBLISHER, PUBLISH_DATE, ISBN, OWNER_NAME (distributor), COVER_URL, L_CATEGORY_NAME and M_CATEGORY_NAME. It is free and restricted to 경기도서관 members — [경기도서관 전자책 오픈API](https://ebook.library.kr/info/open-search)

### Inferences
- data4library's `itemSrch` with `type=ALL`, paged by libCode, is the only public route to title-level holdings, with KDC class and call number, across about 1,500+ public and small libraries. At 30,000 calls/day and 100+ rows per call, a full crawl of one large library is feasible in a day, but the whole country would take many days. The monthly Text dumps in openDataL are the better bulk path, subject to per-dataset approval.
- `itemSrch` startDt/endDt filter by **registration date (reg_date)**. That supports incremental "new acquisitions since X" harvesting per library. Deletions and weeding cannot be detected incrementally, so periodic full refreshes are needed.
- data4library has no KOGL label, and its terms forbid copying or third-party provision without prior consent. Commercial redistribution of its bibliographic or loan data, and any use of cover images beyond non-commercial display, is risky without written approval from NLK (libdata@korea.kr). The explicit "AI 입력학습" ban on images is new and notable.
- NANET via data.go.kr is the most permissive license (KOGL 1), but its data is NANET's own catalog, strong in theses and articles, and its name/value response shape needs custom parsing.
- KPIPA is the only source of publisher-supplied, ONIX-based, pre-publication commercial metadata. Coverage is opt-in and limited to publications from 2021-09-29 on. Access needs a committee-reviewed application, and redistribution is restricted.

### Gaps
- I found no official current number for the unregistered daily cap beyond the 2017 notice. That notice implies ≤500/day without IP registration; I found no newer confirmation.
- I did not verify the exact column list or format of the openDataL "Text" dumps, because download requires login and approval. Developer recollection suggests CSV/TSV with columns similar to itemSrch, but this is unverified.
- KPIPA's Open API endpoint URLs, request parameters, response fields and rate limits are not public. They are presumably given after approval. I could not access the member-only docs.
- RISS: I found no stated rate limit. Whether individuals can get keys is unclear; the page targets institutions.
- 국가전자도서관 (dlibrary.go.kr): I found no current Open API documentation and no confirmation that the service was discontinued. I could not verify its status.
- 책나루 / 책이음 (books.nl.go.kr) are NLK-run and were not investigated in depth.

## Q2. Which services provide unique data not found in commercial APIs (Aladin, Kakao, Naver)?

### Takeaway
Loan statistics, holdings by library, KDC classification, call numbers, co-loan recommendations and reading-rate data come only from 도서관 정보나루. University-library holdings come from RISS, and thesis/article catalog data from NANET. Commercial book APIs offer none of these.

### Cited Findings
- 정보나루 returns `class_no`/`class_nm` (KDC), `loan_count`, monthly loan history, loan groups by age and gender, co-loaned books, mania/reader recommendations, keyword weights, holdings flags (`hasBook`, `loanAvailable`), lists of libraries holding an ISBN, per-library call numbers and shelf codes (`callNumber`, `separate_shelf_code`, `shelf_loc_code`, `copy_code`, `reg_date`), and regional reading volume and rate (`readQt`) — [API manual v20260620](https://www.data4library.kr/downloadApiManual)
- The platform's data comes from "전국 공공도서관에서 수집한 회원·장서·대출 데이터" — [도서관 정보나루 소개](https://www.data4library.kr/openCenter)
- RISS 단행본 responses include `holdings` and `holdings_code` for Korean university libraries — [RISS 단행본 API](https://www.riss.kr/apicenter/apiSearchBook.do)
- NANET results include 청구기호 and 학위논문 metadata, and a separate TOC endpoint — [S3002_01_01](https://openapi.nanet.go.kr/S3002_01_01.html); [S2001](https://openapi.nanet.go.kr/S2001.html)
- KPIPA metadata is ONIX 3.0, entered by publishers, and covers upcoming titles (출간예정). Its sales and reader statistics are shown on its site — [메타데이터 서비스](https://bnk.kpipa.or.kr/home/v3/center/centerGuideServiceMetaData); [KPIPA sitemap](https://bnk.kpipa.or.kr/home/v3/center/centerGuideSiteMap)
- 정보나루 provides an ISBN 부가기호 code (`addition_symbol`) as a separate field, which allows audience/genre segmentation such as 아동 = 7 — [API manual](https://www.data4library.kr/downloadApiManual)

### Inferences
- For a bibliographic product, 정보나루 can enrich ISBN records with KDC class, a popularity signal and an availability signal. NLK or commercial APIs should still serve as the primary bibliographic source, because 정보나루's bibliographic fields are thin: there are no page counts, no prices, and no TOC except via `description`.

### Gaps
- I found no data-quality comparison between 정보나루's `class_no` and NLK's official KDC.

## Q3. Which services allow full bulk download, and which are per-query only?

### Takeaway
Only 정보나루 (monthly per-library dumps behind approval) and scattered local-government file datasets on data.go.kr offer real bulk files. NANET, RISS and KPIPA are per-query only, with paging capped at 100 per page and daily quotas of 10,000 to 100,000.

### Cited Findings
- 정보나루 openDataL lists 1,678 per-library 장서/대출 datasets in "Text" and "API" form, refreshed monthly (latest 2026-10-01) — [openDataL](https://www.data4library.kr/openDataL). Each needs a separate 이용신청 approval — [common-data.js](https://www.data4library.kr/resources/js/common-data.js)
- `itemSrch` `type=ALL` returns a library's whole collection, paged at a default of 100; startDt/endDt filter by registration date — [API manual](https://www.data4library.kr/downloadApiManual)
- Ranking endpoints have hard caps: `loanItemSrch` 5,000, `loanItemSrchByLib` 200, `hotTrend` top 5 × 3 days — [API manual](https://www.data4library.kr/downloadApiManual)
- NANET: displaylines max 100; development account about 10,000/day, operating account up to 100,000/day; no dump of book records — [S1001](https://openapi.nanet.go.kr/S1001.html); [S3002_01_01](https://openapi.nanet.go.kr/S3002_01_01.html)
- RISS: rowcount max 100; licensed BY-NC-ND — [RISS 단행본 API](https://www.riss.kr/apicenter/apiSearchBook.do)
- data.go.kr has 204 file datasets under "도서관 장서", per library or municipality, in CSV, JSON or XML — [data.go.kr search](https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword=%EB%8F%84%EC%84%9C%EA%B4%80+%EC%9E%A5%EC%84%9C)
- KPIPA terms let it limit call counts and forbid third-party redistribution without consent, so no bulk dump is offered publicly — [KPIPA Open API 약관](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)

### Inferences
- A practical national ISBN-to-holdings/KDC table can be built by unioning the 정보나루 monthly per-library dumps, after approval, and deduplicating by isbn13. Licensing for redistribution of the derived table is unclear under the 정보나루 terms.

### Gaps
- I did not verify the dump file size, encoding or whether the dumps contain the loan count per item.

## Q4. Practical gotchas: approval process, data quality, ISBN formats

### Takeaway
Plan for these: server-IP registration to get past 500 calls/day, a 30,000/day hard cap, http-only documented URLs, XML by default, mixed 10- and 13-digit ISBN handling, holdings that lag by up to a month, the cover-image usage ban, and committee approval for KPIPA keys (one-year expiry) and RISS keys.

### Cited Findings
- More than 500 calls/day needs registered server IP, organization and purpose, entered at application time or later in 마이페이지 — [notice cn=88](https://data4library.kr/noticeV?cn=88). IP-registered users are capped at 30,000/day — [notice cn=194](https://www.data4library.kr/noticeV?cn=194)
- `isbn13` accepts 10- or 13-digit ISBNs in `recommandList`, `srchDtlList`, `keywordList` and `usageAnalysisList`. Up to 5 `;`-separated ISBNs are accepted in `recommandList` and `itemSrch`; beyond 5, only the first 5 are used. `libSrchByBook` uses the parameter `isbn`, not `isbn13`. `set_isbn13` appears separately for sets — [API manual](https://www.data4library.kr/downloadApiManual)
- Loan rankings aggregate by ISBN. hotTrend counts only libraries participating at the reference date — [API manual](https://www.data4library.kr/downloadApiManual)
- `loanAvailable` reflects the previous day's status — [API manual](https://www.data4library.kr/downloadApiManual). Holdings refresh monthly, so they lag live inventory — [MCP 활용방법](https://www.data4library.kr/mcpUtilization)
- Libraries drop out of publishing; for example, one row's last data is from 2024-10-01 with "현재는 Data가 공개되지 않는 도서관" — [openDataL](https://www.data4library.kr/openDataL)
- Manual quirks: srchBooks says "페이지당 20 개 키워드" when it means books; one example uses "IoaninfoYN" (capital I) for `loaninfoYN`; `recBooks` was renamed `maniaRecBooks` and removed after 2023-03-31 — [API manual](https://www.data4library.kr/downloadApiManual)
- The 2017 JSON notice's example links point to `dlib.data4library.kr`, while the text says `data4library.kr` — [notice cn=93](https://data4library.kr/noticeV?cn=93)
- KPIPA keys expire after 1 year, renewal must be requested 30 days ahead, and approval needs committee review — [KPIPA 약관 제4조](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)
- The RISS 단행본 parameter table is internally inconsistent: the `isbn` row's description reads as 초록 — [RISS 단행본 API](https://www.riss.kr/apicenter/apiSearchBook.do)
- NANET error 32 (UNREGISTERED IP) and 22 (daily limit) are the common data.go.kr failure modes — [S4001](https://openapi.nanet.go.kr/S4001.html)

### Inferences
- Normalize ISBNs to 13 digits client-side before joining across sources. Keep `set_isbn13` and `vol` to disambiguate multi-volume sets, which share bibliographic data but have different volume numbers.
- Use HTTPS cautiously. The manual documents only `http://`, so check whether `https://data4library.kr/api/` works before relying on it.

### Gaps
- I found no developer blog with verified JSON samples newer than 2023. A velog post was found showing `loanItemSrch` JSON with bookname, authors, isbn13 and class_no, but I only saw it in a search snippet and did not verify it ([velog juner1103](https://velog.io/@juner1103/%EB%8D%B0%EC%9D%B4%ED%84%B0-%EC%88%98%EC%A7%91jsonxml%ED%81%AC%EB%A1%A4%EB%A7%81)).
- I could not confirm the typical approval turnaround times for 정보나루 dataset requests, KPIPA keys or RISS keys.
