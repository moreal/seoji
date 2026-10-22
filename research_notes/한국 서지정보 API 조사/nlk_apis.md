# 국립중앙도서관(NLK) 서지 API와 대량 데이터 현황 (2026-10 기준)

> Research date: 2026-10-22. Sources were read directly: the official guide pages (HTML), the data.go.kr pages with their embedded Swagger specs, and the lod.nl.go.kr pages. "Direct probe" means a request this researcher sent on 2026-10-21/22 (UTC) with no key or an invalid key, plus SPARQL queries, which need no key.

## Q1. NLK API and data service inventory: endpoints, parameters, fields, auth, limits, license

### Takeaway
As of 2026-10 NLK runs three groups of services.
- **Legacy nl.go.kr Open APIs.** These are Seoji/ISBN 서지정보, 소장자료, KOLIS-NET, 사서추천도서, 대한민국 국가서지 and a CIP endpoint that is no longer in the menu. They use an NLK-issued key that a staff member must approve.
- **LOD-based OpenAPIs on data.go.kr (new).** These launched 2026-01-12 and cover 서지, 저자, 주제, 도서관 and 인터링킹. They are served from `apis.data.go.kr/1371029/...` with a data.go.kr serviceKey, and the development account allows 10,000 calls.
- **The 국가서지 LOD (lod.nl.go.kr).** It offers a live SPARQL endpoint and full RDF dumps (TTL/RDF-XML/JSON-LD) under 공공누리 1유형 + CC0 1.0, refreshed 2026-10-08.

KORMARC (MARC) and 목차 bulk data are given only to approved institutions. Individuals are excluded, and the stated purpose is to restrict commercial use.

### Cited Findings

#### Common: NLK Open API keys
- Application steps per NLK: (1) join as an NLK member, (2) apply for a key, (3) a staff member approves it ("발급된 인증키를 활용하기 위해서는 담당자 승인이 필요합니다"), (4) start using it. The protocol is described as XML-based. Errors go to the department named on each API tab. — [NLK Open API 이용안내](https://www.nl.go.kr/NL/contents/N31101010000.do)
- The Open API menu tabs in 2026-10 are 소장자료, 국가자료종합목록, ISBN 서지정보, 인재채용정보, 사서추천도서 and 대한민국 국가서지. The 출판예정도서 (CIP) guide page still exists but is not in the tab list. — [NLK ISBN 서지정보 guide page (menu)](https://www.nl.go.kr/NL/contents/N31101030500.do); [출판예정도서 guide](https://www.nl.go.kr/NL/contents/N31101030800.do)
- The data.go.kr mirror entries ("LINK"-type, which point back to NLK) all say: 무료, 업데이트 주기 실시간, 이용허락범위 "제한 없음", 개발/운영 자동승인, traffic "해당 기관의 정책에 따라 상이". These are 3078982 ISBN서지정보 (2,054 applications, modified 2025-07-16), 3078981 소장자료 and 3036346 국가자료종합목록. The exception is 사서추천도서 (15064371): 공공누리 제1유형 (출처표시), and 운영단계 needs 심의승인. — [data.go.kr ISBN서지정보](https://www.data.go.kr/data/3078982/openapi.do); [소장자료](https://www.data.go.kr/data/3078981/openapi.do); [국가자료종합목록](https://www.data.go.kr/data/3036346/openapi.do); [사서추천도서](https://www.data.go.kr/data/15064371/openapi.do)
- I found no official statement of a daily quota or per-second limit for the legacy NLK Open APIs. One developer doc checked this on 2026-10-09: "공식 가이드·오류 코드표·공공데이터포털 어디에도 호출 횟수 한도가 없다". It also says responses are sometimes slow or cut off and recommends a timeout of about 10 s. — [DeveloperAcademy-POSTECH Five-Guys sources.md](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md)

#### 1. ISBN 서지정보 유통지원시스템 (Seoji) Open API: current and active
- **Endpoint:** `https://www.nl.go.kr/seoji/SearchApi.do`. "미납본 목록 (구:출판예정도서)" is the same endpoint with `deposit_yn=N`. The department is 디지털정보기획과 (02-590-0548). — [NLK guide: ISBN 서지정보](https://www.nl.go.kr/NL/contents/N31101030500.do)
- **The legacy host `https://seoji.nl.go.kr/landingPage/SearchApi.do` still answers.** An invalid key returns HTTP 200 JSON `{"RESULT":"ERROR","ERR_CODE":"011",...}` from the same WAS (cookie `NLSEOJIWAS1`). The response carries `Access-Control-Allow-Origin: *`. — direct probe of [seoji.nl.go.kr/landingPage/SearchApi.do](https://seoji.nl.go.kr/landingPage/SearchApi.do)
- **Request parameters** (exact, from the guide):
  - Required: `cert_key` (String, 인증키); `result_style` (json | xml); `page_no` (Integer, starts at 1); `page_size` (Integer, 쪽당 출력건수).
  - Optional:
    - `isbn` (우절단 = right-truncation, i.e. prefix match)
    - `set_isbn` (우절단)
    - `ebook_yn` (Y/N, exact)
    - `title` (본표제, 형태소+ngram)
    - `start_publish_date` / `end_publish_date` (발행예정일 range, yyyymmdd)
    - `cip_yn` (Y/N)
    - `deposit_yn` (납본유무 Y/N)
    - `series_title`, `publisher`, `author` (형태소+ngram)
    - `form` (종이책, 혼합자료, 전자책, 오디오북, 기타 전자출판물, 다양한 제본형태, 다양한 형식혼합 세트)
    - `sort` (PUBLISH_PREDATE | INPUT_DATE | INDEX_TITLE | INDEX_PUBLISHER)
    - `order_by` (ASC | DESC)
  - Sample: `...SearchApi.do?cert_key=[키]&result_style=json&page_no=1&page_size=10&start_publish_date=20220509&end_publish_date=20220509`
  - — [NLK guide](https://www.nl.go.kr/NL/contents/N31101030500.do)
- **Response fields** (exact, all String):
  - Paging: PAGE_NO (현재 쪽번호), TOTAL_COUNT (전체 출력수).
  - Title and series: TITLE (표제), VOL (권차), SERIES_TITLE (총서명), SERIES_NO (총서편차).
  - ISBN: AUTHOR (저자), EA_ISBN (ISBN), EA_ADD_CODE (ISBN 부가기호), SET_ISBN, SET_ADD_CODE, SET_EXPRESSION (세트표현, e.g. "세트, 전2권.").
  - Publication: PUBLISHER (발행처), EDITION_STMT (판사항), PRE_PRICE (예정가격), KDC, DDC, PAGE (페이지), BOOK_SIZE (책크기), FORM (발행제본형태), PUBLISH_PREDATE (출판예정일), SUBJECT (주제).
  - Flags: EBOOK_YN (Y 전자책/N 인쇄책), CIP_YN, CONTROL_NO (CIP 제어번호).
  - Links: TITLE_URL (표지이미지 URL), BOOK_TB_CNT_URL (목차 파일 URL), BOOK_INTRODUCTION_URL (책소개 파일 URL), BOOK_SUMMARY_URL (서평 파일 URL). The guide marks all three file URLs "21년 2월까지 생성된 데이터 제공". PUBLISHER_URL (출판사 홈페이지).
  - Dates: INPUT_DATE (등록날짜), UPDATE_DATE (수정날짜).
  - Inline text: BOOK_TB_CNT (목차), BOOK_INTRODUCTION (책소개), BOOK_SUMMARY (서평).
  - Other: DEPOSIT_YN (납본여부), REAL_PRICE (재정가), FORM_DETAIL (발행제본형태 상세), BIB_YN (서지유통여부), RELATED_ISBN (연관 ISBN).
  - The guide notes "제공서비스에 따라 출력결과 필드는 제한될 수 있습니다". — [NLK guide](https://www.nl.go.kr/NL/contents/N31101030500.do)
- **JSON envelope:** the records sit in a `docs` array (`body.docs[0].PAGE`, `docs[].EA_ISBN`). — [Jiwook00/moseori client.ts](https://github.com/Jiwook00/moseori/blob/HEAD/src/lib/nl/client.ts); [ted1117/WhatComicsComeNextMonth services.py](https://github.com/ted1117/WhatComicsComeNextMonth/blob/HEAD/comic/services.py)
- **Error codes:** 000 시스템 오류, 010 인증키값 누락, 011 유효하지않은 인증키, 012 필수 파라메터 입력 누락, 013 **쪽당 출력건수 제한** (a page_size cap exists, but the guide gives no number). Errors come back as JSON, e.g. `{"RESULT":"ERROR","ERR_CODE":"010","ERR_MESSAGE":"인증키 정보가 없습니다."}`. — [NLK guide](https://www.nl.go.kr/NL/contents/N31101030500.do); direct probe of [SearchApi.do](https://www.nl.go.kr/seoji/SearchApi.do)
- **page_size=200 works in practice.** A production Celery task calls the API with `page_size: 200`, `ebook_yn`, `start_publish_date`/`end_publish_date` set to next month, and pages through the results. — [ted1117/WhatComicsComeNextMonth](https://github.com/ted1117/WhatComicsComeNextMonth/blob/HEAD/comic/services.py)
- **Key:** the same NLK Open API key works for Seoji and search.do (it is passed as `cert_key` here and `key` elsewhere). — [Five-Guys sources.md](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md); [Calibre-Korea-ISBN-Metadata-Plugin README](https://github.com/ririnto/Calibre-Korea-ISBN-Metadata-Plugin/blob/HEAD/README.md)

#### 2. 소장자료 검색 API (search.do): current
- **Endpoint:** `https://www.nl.go.kr/NL/search/openApi/search.do`. Variants are `systemType=오프라인자료` (구 소장정보), `systemType=온라인자료` (구 디지털화자료) and `govYn=Y` (정부간행물). The department is 정보기술기반과 (02-3483-8843). — [NLK guide: 소장자료](https://www.nl.go.kr/NL/contents/N31101030700.do)
- **Parameters:**
  - Basic: `key` (required); `srchTarget` (total | title | author | publisher | cheonggu); `kwd`; `pageNum` (required); `pageSize` (required, default 10).
  - Filters: `systemType`; `category` (도서, 고문헌, 학위논문, 잡지/학술지, 신문, 기사, 멀티미디어, 장애인자료, 외부연계자료, 웹사이트 수집, 기타, 해외한국관련자료); `lnbTypeName`; `offerDcode2s` (CH4x codes); `licYn` (원문이용 codes S/F/Y/L/N/C/U/T/R/D/A); `govYn`.
  - Sorting and format: `sort` (ititle, iauthor, ipub_year, ipublisher, cheonggu); `order` (asc | desc); `apiType` (xml | json).
  - Detail search (`detailSearch=true&f1=title&v1=..&f2=author&v2=..`) cannot be mixed with `kwd`.
  - ISBN search: `detailSearch=true&isbnOp=isbn&isbnCode=8984993727`.
  - — [NLK guide: 소장자료](https://www.nl.go.kr/NL/contents/N31101030700.do)
- **Response fields:**
  - Query echo: kwd, category, pageNum, pageSize, sort, total.
  - Bibliographic: title_info, type_name, author_info, pub_info, pub_year_info, isbn, call_no, kdc_code_1s, kdc_name_1s.
  - Location: place_info, menu_name, media_name, manage_name.
  - Identifiers and links: control_no, id (종키), type_code, detail_link.
  - Full text and rights: doc_yn, org_link, lic_yn, lic_text.
  - reg_date (비치일).
  - **No page count, size, price or MARC.** — [NLK guide: 소장자료](https://www.nl.go.kr/NL/contents/N31101030700.do); confirmed by [moseori ADR 0004](https://github.com/Jiwook00/moseori/blob/HEAD/docs/adr/0004-%EC%95%8C%EB%9D%BC%EB%94%98%EC%97%90%EC%84%9C-%EC%B9%B4%EC%B9%B4%EC%98%A4%EB%A1%9C.md) ("소장자료 검색(search.do)은 쪽수·크기를 주지 않아 쓰지 않는다")
- **Errors:** 012 "DATA LIMIT 500: 검색결과 이동시 500건 제한 (500건 이후 데이터 조회불가)", which is a hard pagination cap. Also 013 CATEGORY ERROR, 014 PARAMETER VALIDATION, 015 REQUIRED PARAMETER MISSING, 101 SEARCH ERROR. The error JSON shape differs from Seoji: `{"errorCode":"011","errorMsg":"INVALID KEY:..."}`. — [NLK guide: 소장자료](https://www.nl.go.kr/NL/contents/N31101030700.do); direct probe

#### 3. 국가자료종합목록 KOLIS-NET Open API: current
- **Endpoint:** `https://www.nl.go.kr/NL/search/openApi/searchKolisNet.do`. Parameters are key, srchTarget, kwd, pageNum, pageSize, sort, desc and detailSearch f1/v1 pairs. Response fields match search.do minus detail_link. The department is 정보기술기반과 (02-590-6312). — [NLK guide: 국가자료종합목록](https://www.nl.go.kr/NL/contents/N31101030400.do)
- **The guide does not list `apiType`, but the sample URL uses `apiType=xml`.** A direct probe with `apiType=json` still returned an XML `<error>` body. — [NLK guide](https://www.nl.go.kr/NL/contents/N31101030400.do); direct probe
- **The data.go.kr standard dataset "국가자료종합목록" (15096286)** covers 전국 공공도서관 및 행정부처 자료실 소장자료 목록. It is updated 수시, XML, free. — [data.go.kr 15096286](https://www.data.go.kr/data/15096286/standard.do) (summary seen via search snippet only)

#### 4. 대한민국 국가서지 검색 API: current
- **Endpoint:** `https://librarian.nl.go.kr/LI/search/openApi/seojiSearch.do`. Parameters are key, kwd, pageNum, pageSize, sort (ititle_asc/desc, author_asc/desc, pub_asc/desc, pubyear_asc/desc), apiType (xml | json) and detailSearch f1/v1.
- **Response:** kwd, pageNum, pageSize, sort, total, title_info, author_info, pub_info, pub_year_info, category, seoji_year (수록연도), detail_link.
- **Error 012** is the same DATA LIMIT 500.
- — [NLK guide: 대한민국 국가서지](https://www.nl.go.kr/NL/contents/N31101031100.do)

#### 5. 출판예정도서 (CIP) API (cip.do): still answers but is not in the menu
- **Endpoint:** `https://www.nl.go.kr/NL/search/openApi/cip.do`. Parameters are key, srchTarget, kwd, pageNum, pageSize, sort, desc, apiType (xml/json) and searchType.
- **Response fields:**
  - Query echo: kwd, category, pageNum, pageSize, sort, total.
  - Record: Id (CIP키), kdc_code_1s, title_info, author_info, pub_info, exp_date (출판예정일), price, currency_code, isbn, ea_add_code, publisher_key.
  - Thumbnails and links: cover_yn, thumb_path, thumb_file_name, img_path, detail_path.
  - Availability flags: title_page_yn, copyright_page_yn, author_yn, preface_yn, contents_yn, abstract_yn, text_yn, etc_yn.
- **Status:** a direct probe gave JSON error 011, so the endpoint is still live. The Seoji guide now describes "미납본 목록 (구:출판예정도서)" as `SearchApi.do?deposit_yn=N`, which points to Seoji as the replacement.
- — [NLK guide: 출판예정도서](https://www.nl.go.kr/NL/contents/N31101030800.do); [Seoji guide](https://www.nl.go.kr/NL/contents/N31101030500.do)

#### 6. 사서추천도서 API (saseoApi.do): current
- **Endpoint:** `https://nl.go.kr/NL/search/openApi/saseoApi.do`.
- **Parameters:** key, startRowNumApi, endRowNumApi, start_date, end_date, drCode (11 문학, 6 인문과학, 5 사회과학, 4 자연과학).
  - Spelling inconsistencies in the guide: the table says `endRowNemApi` and the sample says `endRowNumApi`; the table says `drCode` and the sample says `drcode`.
- **Response:** totalCount, recom_no, recom_code, decode, recom_title, recom_author, recom_publisher, recom_callno, recom_file_path, recom_mokcha, recom_contents, recom_reg_dt, control_no, publish_year, recom_year, recom_month, mokchFilePath, recome_isbn. The response is XML.
- **License:** 공공누리 제1유형. — [NLK guide: 사서추천도서](https://www.nl.go.kr/NL/contents/N31101030900.do); [data.go.kr 15064371](https://www.data.go.kr/data/15064371/openapi.do)

#### 7. 국가서지 LOD OpenAPIs on data.go.kr: new, launched 2026-01-12
- **Launch:** NLK's press release of 2026-01-12, "국립중앙도서관 데이터, '누구나' 쓰는 공공데이터로 탈바꿈", announced a 국가서지 OpenAPI built on the LOD.
  - About 3,000만 건 in 5 categories: 서지, 저자, 주제 (NLSH), 도서관, 인터링킹.
  - XML/JSON, distributed through data.go.kr.
  - Built under MOIS's 2025 국가중점데이터 개방 지원사업.
  - Stated plan: "AI 학습 및 지능형 서비스 활용을 고려한 데이터 개방을 단계적으로 확대".
  - — [NLK 보도자료 2026-01-12](https://www.nl.go.kr/NL/contents/N50603000000.do?schM=view&id=54867&schBcid=normal0302); [NDL カレントアウェアネス 2026-01-13](https://current.ndl.go.jp/car/269230)
- **The five data.go.kr services and their hosts:**
  - [서지 정보 제공 서비스 15154402](https://www.data.go.kr/data/15154402/openapi.do): host `apis.data.go.kr/1371029/BookInformationService_v2`
  - [저자 15154360](https://www.data.go.kr/data/15154360/openapi.do): `.../1371029/AuthorInformationService` (getPersonList, getOrganizationList)
  - [주제 15154120](https://www.data.go.kr/data/15154120/openapi.do): `.../SubjectInformationService/getSubjectList`
  - [도서관 15154373](https://www.data.go.kr/data/15154373/openapi.do): `.../LibraryInformationService/getLibraryList`
  - [인터링킹 15154270](https://www.data.go.kr/data/15154270/openapi.do): `.../InterlinkingInformationService/getInterlinkingList`
  - The LOD site's OpenAPI page lists these same five links. — [lod.nl.go.kr OpenAPI 개요](https://lod.nl.go.kr/home/openapi/overview.do)
- **15154402 metadata:**
  - Registered 2025-11-26, modified 2026-05-11, 258 applications.
  - REST, JSON+XML, free, updated 실시간, 이용허락범위 "제한 없음".
  - 개발단계 자동승인 / 운영단계 심의승인.
  - **Traffic: 개발계정 10,000**, and 운영계정 can be raised by registering a 활용사례.
  - Gateway error codes include 22 (daily quota exceeded) and 23 (per-second quota exceeded).
  - Based on Dublin Core and BIBO ontologies. MARC-derived offline data and MODS-derived online data are separate.
  - — [data.go.kr 15154402](https://www.data.go.kr/data/15154402/openapi.do)
- **Operations** (from the Swagger embedded in the page):
  - Material lists: getbookList_v2 (도서), getNonbookList_v2 (비도서), getElectronicBookList_v2, getElectronicJournalList_v2, getMultimediaList_v2.
  - Author-relation lists: getOfflineBookAuthorList_v2, getOfflineNonBookAuthorList_v2, getOnlineElectronicBookAuthorList_v2, getOnlineElectronicJournalAuthorList_v2, getOnlineMultimediaAuthorList_v2.
  - Subject-relation lists: the matching *SubjectList_v2 operations.
  - Parameters for the list operations: `serviceKey`, `pageNo`, `numOfRows`, `type` (all required), plus optional `label` (표제명), `controlNumber`, `isbn`, `publisher`, `titleOfSeries`. Relation operations take only `controlNumber`.
  - **There is no date or modified-since parameter.** — [data.go.kr 15154402 Swagger](https://www.data.go.kr/data/15154402/openapi.do)
- **getbookList_v2 response fields** (in `body.items.item`, with body.totalCount/pageNo/numOfRows):
  - Identity and title: BIBLIO_ID (국립중앙도서관제어번호_서지), URI, DCTERMS_title, RDFS_label, DCTERMS_alternative, NLON_remainderOfTitle.
  - Creators and publication: DC_creator, DCTERMS_creator, DC_publisher, NLON_publicationPlace, DCTERMS_issued (발행일), NLON_issuedYear.
  - Identifiers: BIBO_isbn, BIBO_issn, NLON_cip (CIP 제어번호).
  - Description and edition: BIBFRAME_extent (형태사항), BIBO_edition, BIBO_volume.
  - Classification: NLON_kdc, NLON_ddc, NLON_kdcn, NLON_editionOfKDC, NLON_classificationNumberOfNLK, NLON_itemNumberOfNLK (청구기호).
  - Subjects and content: DCTERMS_subject, NLON_keyword, DCTERMS_tableOfContents, DCTERMS_abstract, BIBO_abstract, DCTERMS_description.
  - Series: NLON_titleOfSeries, NLON_volumeOfSeries.
  - Translation: BIBO_translationOf, NLON_translatedAs.
  - Links: OWL_sameAs, RDFS_seeAlso.
  - Holdings: NLON_localHolding, NLON_holdingInstitution.
  - Language: DCTERMS_language, BIBFRAME_language, BIBFRAME_place (발행국부호).
  - Notes: NLON_awardsNote, NLON_audienceNote.
  - Type: NLON_typeOfData, DC_type, RDF_type.
  - Timestamps: NLON_datePublished (데이터발행일시), DCTERMS_created (생성일).
  - About 150 fields in total. **There is no price field and no cover-image field.** — [data.go.kr 15154402 Swagger](https://www.data.go.kr/data/15154402/openapi.do)
- **Author service fields:** AUTHOR_ID, URI, SKOS_prefLabel, SKOS_altLabel, FOAF_name, NLON_isni, NLON_birthYear, NLON_deathYear, SCHEMA_jobTitle, NLON_fieldOfActivity, OWL_sameAs, DCTERMS_modified (최종처리일시), and others.
- **Subject service fields:** SUBJECT_ID, SKOS_prefLabel, SKOS_altLabel, SKOS_broader, SKOS_narrower, SKOS_related, SKOS_closeMatch, NLON_isSubjectOf, and others.
- — [data.go.kr 15154360](https://www.data.go.kr/data/15154360/openapi.do); [15154120](https://www.data.go.kr/data/15154120/openapi.do)

#### 8. 국가서지 LOD (lod.nl.go.kr): SPARQL and dumps, current
- **SPARQL endpoint:** `https://lod.nl.go.kr/sparql`. It accepts GET and POST and returns html, rdf, json, xml, tsv or csv.
  - Built-in prefixes: nlon `http://lod.nl.go.kr/ontology/`, nlk `http://lod.nl.go.kr/resource/`, nlloc, nlfloc, nllib, nlgov, nluv, nlcon, plus bibo, event, rdf, rdfs, owl, xsd, dc, dcterms, foaf, skos, geonames.
  - It needs no key. A direct query on 2026-10-22 returned `COUNT(?s a bibo:Book)` = 3,644,964.
  - — [lod.nl.go.kr/sparql](https://lod.nl.go.kr/sparql); [LOD 서비스 소개](https://lod.nl.go.kr/home/service/introduction.do)
- **Sample record:** a SPARQL lookup by `bibo:isbn "9788936434267"` returned resource `nlk:KJU201703899` (아몬드, 창비) with:
  - bibframe:extent "263 p" and "20 cm"
  - nlon:kdc 813.7, nlon:itemNumberOfNLK
  - dc:creator, dc:publisher, dcterms:issued "2017"
  - dcterms:subject → KSH URIs, dcterms:creator → KAC URI
  - nlon:awardsNote, nlon:translatedAs
  - owl:sameAs → NANET, LIBRIS and OpenLibrary
  - nlon:datePublished "2026-10-11T05:05:20"
  - — direct SPARQL query against [lod.nl.go.kr/sparql](https://lod.nl.go.kr/sparql)
- **Dataset downloads:** the 2026-10 page offers TTL, RDF/XML and JSON-LD/JSON with samples. **All datasets show 데이터 갱신일 2026-10-08.**
  - 오프라인자료: 7,151,860 records (TTL 2,117.1 MB)
  - 온라인자료: 21,236,692 (TTL 4,351.6 MB)
  - 일반도서 (전자책 포함): 3,980,216 (TTL 1,057.9 MB; JSON-LD 883.5 MB)
  - 공공간행물: 652,951
  - 시청각/컴퓨터파일: 1,934,894
  - 연속간행물: 236,381
  - 학위논문: 2,225,440
  - 개인명: 1,859,505
  - 단체명: 156,213
  - 주제명 (NLSH): 257,764
  - 도서관정보: 14,054
  - Downloading requires a short form (소속기관 type: 공공기관/학술기관/기업/개인; 기관명; 사용목적).
  - — [LOD 데이터셋 다운로드](https://lod.nl.go.kr/home/dataset/datadownload.do)
- **License (verbatim gist):** "공공누리 제1유형 및 크리에이티브 커먼즈 라이선스 CC0 1.0 조건에 따라 도서관, 출판산업, 연구 등의 목적으로 누구나 자유롭게 이용할 수 있습니다." — [LOD 데이터셋 다운로드](https://lod.nl.go.kr/home/dataset/datadownload.do)
- **Ontology:** the custom NLON ontology plus BIBO, DC/DCTERMS, BIBFRAME (`id.loc.gov/ontologies/bibframe/extent`), SKOS and FOAF. Statistics as of 2025-04-21:
  - 단행본 5,481,192 records / 179M triples
  - Total 29,617,717 records / 811M triples
  - 10.4M interlinks
  - Note that the 개인명/단체명 counts on this stats page look swapped relative to the download page.
  - — [LOD 데이터 현황](https://lod.nl.go.kr/home/service/dataset.do)
- **Site history:** the site was revamped 2024-01-16 and offered about 2,700만 records at that time. — [wikidocs LOD 분석](https://wikidocs.net/265874)

#### 9. MARC (KORMARC) and 목차 bulk data via KOLIS-NET: restricted
- **Purpose and eligibility:** NLK provides MARC and 목차 data through the KOLIS-NET 구축시스템 to libraries, bookstores, publishers and other related organizations. Verbatim: "MARC 및 목차 데이터의 영리적 이용을 제한하기 위하여 부득이 인증절차를 신청 후 승인된 기관에 한하여 제공 … (단, 개인은 대상에서 제외)".
- **How to apply:** download the 도서관용 or 도서관이외 기관용 form and submit it by FAX 02-590-6335, by post, or by email to kolisnet@korea.kr. Publishers and bookstores must attach a 사업자등록증.
- **Turnaround:** the 인증 확인 통보 comes 신청 후 2일 이내.
- **Contact:** 국가서지과 02-590-0700 (내선 5).
- — [KOLIS-NET 참여방법](https://www.nl.go.kr/kolisnet/contents/procedure.do)

#### 10. Other NLK files
- **대한민국 국가서지:** published as 서지데이터세트 since the 2019년판 (issued 2020). The download page is "서지데이터세트 다운로드 > 2020년 이후 데이터". — [NLK 서지발간](https://www.nl.go.kr/NL/contents/N50107040000.do); [librarian.nl.go.kr 서지데이터세트 다운로드](https://librarian.nl.go.kr/LI/contents/L10507010000.do)
- **ISBN 발행자번호 배정 내역:** a quarterly file download, with "2026년 2분기" the latest at research time. — [NLK 사전정보공표](https://nl.go.kr/NL/contents/N50803050000.do)
- **Other NLK services on data.go.kr:** OAK 학술정보, 인재채용정보, 한국고문헌종합목록, 조선총독부관보 and 사서의 책장. — [data.go.kr search "국립중앙도서관"](https://www.data.go.kr/tcs/dss/selectDataSetList.do?dType=API&keyword=%EA%B5%AD%EB%A6%BD%EC%A4%91%EC%95%99%EB%8F%84%EC%84%9C%EA%B4%80)
- **도서관 정보나루 (data4library):** a separate NLK-operated service with a limit of 1일 30,000건. It is not covered in depth here. — [Five-Guys sources.md](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md)
- **ISBN-labelled CSV on data.go.kr (15134749):** this is a regional government's archive list, not an NLK dataset, so ignore it. — [data.go.kr 15134749](https://www.data.go.kr/biz/dcat/metadata/15134749.do)

### Inferences
- **Seoji is the best fit for a "Korean book DB".** It has trade-oriented fields (PRE_PRICE, EA_ADD_CODE, SET_ISBN, BOOK_SIZE, PAGE, TITLE_URL cover, INPUT_DATE/UPDATE_DATE) and covers future and newly assigned ISBNs.
- **The LOD/BookInformationService_v2 is the best fit for catalog-quality data** on books NLK actually holds: subjects, KDC, authority links, translations, extent. It is also the only source with an explicit CC0/공공누리1 license.
- **search.do, searchKolisNet.do and seojiSearch.do are discovery APIs, not harvest APIs.** Their 500-row cap and thin fields rule them out for bulk work.
- **The CIP endpoint (cip.do) looks deprecated in favour of Seoji `deposit_yn=N`.** It still answers, but new builds should not depend on it.

### Gaps
- No official numeric `page_size` maximum for Seoji. Error 013 exists, and 200 is known to work in practice.
- No official daily or per-second quota for the legacy nl.go.kr APIs.
- No published approval turnaround for the NLK Open API key ("담당자 승인"). A GitHub issue only mentions waiting.
- The `numOfRows` maximum for the data.go.kr LOD APIs is not stated in the Swagger.
- Whether the legacy APIs return KORMARC: none of the guides offers a MARC output option, and all are flat field lists. MARC exists only through the KOLIS-NET institutional route.
- I could not confirm the file format or field structure of the 대한민국 국가서지 서지데이터세트, because the page loads its content dynamically.
- 문화공공데이터광장 (culture.go.kr): I found no NLK bibliographic API documented there in 2026. The search only returned a 2017 article about the portal in general.

## Q2. Which services allow date-range or incremental harvesting for building and maintaining a full DB?

### Takeaway
- **Only Seoji has a documented date-range filter** (`start_publish_date`/`end_publish_date`, which filter 발행예정일). It also sorts by INPUT_DATE and exposes INPUT_DATE/UPDATE_DATE. That makes it the practical way to harvest "all ISBN-registered books in period X".
- **For full snapshots, the LOD dumps are the only true bulk route.** They cover all NLK holdings, are CC0, and were refreshed 2026-10-08. SPARQL can supplement them.
- **Nothing NLK provides is OAI-PMH** or offers a documented modified-since feed.

### Cited Findings
- **Seoji range parameters:** `start_publish_date`/`end_publish_date` (범위검색, yyyymmdd, 발행예정일). It also has `sort=INPUT_DATE|PUBLISH_PREDATE` with `order_by`, and `deposit_yn`/`cip_yn`/`ebook_yn` filters. INPUT_DATE and UPDATE_DATE are returned, but **neither is a request filter**. — [NLK Seoji guide](https://www.nl.go.kr/NL/contents/N31101030500.do)
- **The guide's own sample is a one-day window** (`start_publish_date=20220509&end_publish_date=20220509`). — [NLK Seoji guide](https://www.nl.go.kr/NL/contents/N31101030500.do)
- **A real project harvests one month ahead** with a date window, page_size 200, and dedup on EA_ISBN. — [ted1117/WhatComicsComeNextMonth](https://github.com/ted1117/WhatComicsComeNextMonth/blob/HEAD/comic/services.py)
- **The search-style APIs cap pagination at 500 results:** search.do and seojiSearch.do return "DATA LIMIT 500: 검색결과 이동시 500건 제한(500건 이후 데이터 조회불가)". — [소장자료 guide](https://www.nl.go.kr/NL/contents/N31101030700.do); [국가서지 guide](https://www.nl.go.kr/NL/contents/N31101031100.do)
- **The data.go.kr BookInformationService_v2 cannot filter by date.** It only accepts label, controlNumber, isbn, publisher and titleOfSeries. Its 10,000-call development quota also limits page-through harvesting. — [data.go.kr 15154402](https://www.data.go.kr/data/15154402/openapi.do)
- **LOD dumps are full files** per material type: 일반도서 3,980,216 records, about 1 GB TTL, all updated 2026-10-08. — [LOD 데이터셋 다운로드](https://lod.nl.go.kr/home/dataset/datadownload.do)
- **Each LOD record carries `nlon:datePublished`** (데이터발행일시), and **authors carry `DCTERMS_modified`** (최종처리일시). — [SPARQL probe](https://lod.nl.go.kr/sparql); [data.go.kr 15154360](https://www.data.go.kr/data/15154360/openapi.do)
- **The 2024 LOD revamp** describes data access as "데이터셋으로 다운로드하거나 … SPARQL 질의". — [wikidocs LOD 분석](https://wikidocs.net/265874)

### Inferences
- **Recommended strategy:**
  1. Seed the database from the LOD 일반도서 dump (CC0), keyed by ISBN and BIBLIO_ID.
  2. Sweep Seoji day by day or week by week over `start_publish_date`/`end_publish_date` for new and forthcoming ISBNs. Include past windows to backfill, and re-sweep recent windows to catch UPDATE_DATE changes.
  3. Look up single records by ISBN through Seoji or BookInformationService_v2.
- **Paging Seoji over a large range may hit unknown caps.** Small date windows keep each query's TOTAL_COUNT manageable. This is not verified against the 013 limit.
- **Incremental sync from LOD via SPARQL (FILTER on `nlon:datePublished`) may not work.** The sample record's datePublished (2026-10-11) is far later than its catalog date (2017), which suggests the timestamp is reset when the data is republished. If so, it cannot detect real changes. This is unverified.
- **Seoji covers ISBN-registered and CIP titles, including ones never deposited. LOD covers NLK holdings.** A complete DB needs both, deduplicated on ISBN (EA_ISBN ↔ BIBO_isbn).

### Gaps
- I did not test whether Seoji accepts an empty query with only page_no/page_size (a full scan without filters), or how deep paging can go.
- There is no documented changelog or delta file for the LOD dumps, and the dump refresh cadence is not stated. The only observation is one date, 2026-10-08.
- SPARQL endpoint query timeouts and result-row limits are not documented.

## Q3. Practical gotchas reported by developers

### Takeaway
- **Seoji data is publisher-supplied and pre-publication.** Many fields are empty or provisional: PAGE, BOOK_SIZE and covers are often missing, and PUBLISH_PREDATE is an expected date.
- **Rich-content file URLs stopped in 2021-02.**
- **The legacy APIs are inconsistent in parameter names and error formats,** and some respond slowly.

### Cited Findings
- **Empty fields:** in one developer's sample, about half of the records had PAGE/BOOK_SIZE empty ("표본 절반은 쪽수·크기가 비어 옵니다(오래된 CIP 등록)"; 실측 채움률 ~50%, 22권). — [moseori client.ts](https://github.com/Jiwook00/moseori/blob/HEAD/src/lib/nl/client.ts); [moseori ADR 0004](https://github.com/Jiwook00/moseori/blob/HEAD/docs/adr/0004-%EC%95%8C%EB%9D%BC%EB%94%98%EC%97%90%EC%84%9C-%EC%B9%B4%EC%B9%B4%EC%98%A4%EB%A1%9C.md)
- **BOOK_SIZE format** is `"183*235"`, i.e. 폭*세로 in mm. — [moseori ADR 0004](https://github.com/Jiwook00/moseori/blob/HEAD/docs/adr/0004-%EC%95%8C%EB%9D%BC%EB%94%98%EC%97%90%EC%84%9C-%EC%B9%B4%EC%B9%B4%EC%98%A4%EB%A1%9C.md)
- **Pre-publication values and data quality** (all from one developer doc, [Five-Guys sources.md](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md)):
  - Records are based on pre-publication 납본/CIP. PUBLISH_PREDATE is an 예정일, and PAGE can also be a planned value: 토지 1 has 400 in NLK vs 472 at Aladin.
  - PAGE is often 1–4 pages smaller than retailer counts.
  - FORM is empty for old print books.
  - TITLE_URL (cover) is "대부분 비어 있음".
  - PAGE is empty for many pre-2015 books.
  - The same ISBN can carry another institution's record: 9788936434267 → 발행처 "부산점자도서관", "155 p.".
  - Title search has no relevance ranking.
- **Rich-content file URLs stop at 2021-02:** BOOK_TB_CNT_URL, BOOK_INTRODUCTION_URL and BOOK_SUMMARY_URL are "21년 2월까지 생성된 데이터 제공". Newer records presumably rely on the inline BOOK_TB_CNT/BOOK_INTRODUCTION/BOOK_SUMMARY fields. — [NLK Seoji guide](https://www.nl.go.kr/NL/contents/N31101030500.do)
- **ISBN field names and matching differ by API:**
  - Seoji request parameter `isbn` matches by 우절단 (prefix). The response field is `EA_ISBN`, with `SET_ISBN` for sets and `RELATED_ISBN`. Prefix matching means a short or partial ISBN can return several records. — [NLK Seoji guide](https://www.nl.go.kr/NL/contents/N31101030500.do)
  - search.do uses `isbnOp=isbn&isbnCode=`, and its guide's example is a 10-digit ISBN. — [소장자료 guide](https://www.nl.go.kr/NL/contents/N31101030700.do)
  - LOD/data.go.kr use `isbn` → `BIBO_isbn`. — [data.go.kr 15154402](https://www.data.go.kr/data/15154402/openapi.do)
- **Kakao can return 13-digit non-978/979 codes** (e.g. 2090000157222), so validate before querying NLK. — [Five-Guys sources.md](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md)
- **Encoding:** Korean query strings "반드시 인코딩해야 함" (UTF-8 percent-encoding). Responses are `application/json;charset=UTF-8`. — [소장자료 guide](https://www.nl.go.kr/NL/contents/N31101030700.do); direct probe of the [Seoji endpoint](https://www.nl.go.kr/seoji/SearchApi.do)
- **Inconsistent naming:**
  - Seoji uses snake_case (`cert_key`, `page_no`, `result_style`). The other APIs use camelCase (`key`, `pageNum`, `apiType`).
  - Error JSON differs: Seoji returns `RESULT/ERR_CODE/ERR_MESSAGE`; search.do and cip.do return `errorCode/errorMsg`; KOLIS-NET and saseo return XML `<error><msg/><error_code/>`.
  - The 사서추천 guide misspells `endRowNemApi`.
  - — guides above; direct probes
- **Detail search:** `kwd` and the detail-search fields cannot be combined. When kwd is absent, the request is treated as a detail search. — [소장자료 guide](https://www.nl.go.kr/NL/contents/N31101030700.do)
- **Reliability:** responses are sometimes slow or dropped. Developers use 7–10 s timeouts and treat NLK as a non-blocking supplement. — [Five-Guys sources.md](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md); [moseori client.ts](https://github.com/Jiwook00/moseori/blob/HEAD/src/lib/nl/client.ts)
- **Caching:** developers cache Seoji lookups for 30 days, reasoning that "서지정보는 바뀌지 않으니 오래 캐시합니다". — [moseori client.ts](https://github.com/Jiwook00/moseori/blob/HEAD/src/lib/nl/client.ts)
- **Key handling:** the NLK key has no domain restriction option, so it gets embedded in app bundles. Developers say to keep it server-side or accept the exposure. — [Five-Guys sources.md](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md)
- **Market context (2026):** a 2026-09 ADR says the Aladin TTB API is shutting down ("알라딘 API가 서비스를 종료한다"). That raises the importance of NLK sources for Korean book DBs. — [moseori ADR 0004](https://github.com/Jiwook00/moseori/blob/HEAD/docs/adr/0004-%EC%95%8C%EB%9D%BC%EB%94%98%EC%97%90%EC%84%9C-%EC%B9%B4%EC%B9%B4%EC%98%A4%EB%A1%9C.md)

### Inferences
- **Expect a gap between Seoji's PUBLISH_PREDATE and actual publication.** Values such as price and pages can be revised later (REAL_PRICE, UPDATE_DATE). A DB should re-poll recent windows and store DEPOSIT_YN, so that deposited (actually published) books can be told apart from announced ones.
- **Use LOD values for page counts and sizes where available.** LOD `BIBFRAME_extent` (e.g. "263 p", "20 cm") comes from NLK's own cataloging of the physical item, so it is likely more accurate than Seoji PAGE for held books.
- **Covers:** neither LOD nor Seoji reliably provides cover images.

### Gaps
- I found no developer report on Seoji behaviour for large page_no values or full scans.
- I found no detailed Korean blog (velog/tistory) post on these APIs in 2026. The concrete evidence comes from GitHub repos.

## Q4. Licenses: 공공누리 type, attribution, commercial use, redistribution, caching

### Takeaway
- **LOD dumps and SPARQL are the clearest:** 공공누리 제1유형 + CC0 1.0, free for anyone, which allows commercial use and redistribution.
- **data.go.kr listings** mark most NLK APIs as "이용허락범위 제한 없음" and the 사서추천도서 API as 공공누리 1유형 (출처표시).
- **KORMARC/목차 bulk is explicitly non-commercial**, institutional and approval-gated.
- **The legacy nl.go.kr Open API pages state no license.**

### Cited Findings
- **LOD:** "공공누리 제1유형 및 크리에이티브 커먼즈 라이선스 CC0 1.0 조건에 따라 도서관, 출판산업, 연구 등의 목적으로 누구나 자유롭게 이용할 수 있습니다." — [LOD 데이터셋 다운로드](https://lod.nl.go.kr/home/dataset/datadownload.do)
- **data.go.kr LOD-based 서지 정보 제공 서비스 (15154402):** 이용허락범위 "제한 없음", 무료. — [data.go.kr 15154402](https://www.data.go.kr/data/15154402/openapi.do)
- **data.go.kr ISBN서지정보, 소장자료 and 국가자료종합목록 mirrors:** 이용허락범위 "제한 없음", 무료. — [3078982](https://www.data.go.kr/data/3078982/openapi.do); [3078981](https://www.data.go.kr/data/3078981/openapi.do); [3036346](https://www.data.go.kr/data/3036346/openapi.do)
- **사서추천도서:** "공공저작물 : 출처표시 (제 1유형)". — [data.go.kr 15064371](https://www.data.go.kr/data/15064371/openapi.do)
- **MARC/목차 via KOLIS-NET:** provided only to approved institutions "영리적 이용을 제한하기 위하여", and individuals are excluded. — [KOLIS-NET 참여방법](https://www.nl.go.kr/kolisnet/contents/procedure.do)
- **Press release:** its 공공누리 1유형 statement covers the press-release text itself. It does not explicitly state the license of the API data. — [NLK 보도자료 2026-01-12](https://www.nl.go.kr/NL/contents/N50603000000.do?schM=view&id=54867&schBcid=normal0302)

### Inferences
- **Building and redistributing a commercial Korean book DB is cleanest on LOD-derived data** (CC0; attribution is courteous but not required under CC0).
- **Seoji data should be safe for storage and commercial use, with attribution to 국립중앙도서관.** The basis is its data.go.kr "제한 없음" listing plus the general 공공누리 regime. However, NLK publishes no explicit terms for the Seoji API itself.
- **Seoji includes publisher-supplied cover images and inline 책소개/서평 text (TITLE_URL, BOOK_INTRODUCTION).** These may be third-party copyrighted works, so redistributing them is riskier than redistributing factual metadata. This is an inference; no NLK statement says so.

### Gaps
- I found no explicit 이용약관 page for the nl.go.kr Open API key covering commercial use, caching or redistribution.
- I found no explicit statement on rights to the cover images and 책소개 text served through Seoji.
