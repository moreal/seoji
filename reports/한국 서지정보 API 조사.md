# 한국 책 DB의 기반을 국립중앙도서관 데이터로 옮기다

2026년 10월 기준으로, 오래 보관하는 한국 책 데이터베이스의 **기록 원천(source of record)으로 쓸 수 있는 곳은 국립중앙도서관(NLK) 계열밖에 없다**. 네이버 책 검색 API는 **2026-07-31에 종료**됐다. 알라딘 Open API는 **2026-09-04에 신규 키 발급을 멈췄고 2026-10-30에 전면 종료**된다. 이 보고서 시점에서 8일 뒤다. 남은 카카오 책 검색은 하루 30,000건, 쿼리당 2,500건까지만 조회할 수 있고, 운영정책이 사전 승낙 없는 복제를 금지해 DB 축적 용도로 쓸 수 없다. 반대로 NLK 국가서지 LOD는 **공공누리 제1유형과 CC0 1.0**으로 공개된다. 일반도서 덤프만 **3,980,216건(2026-10-08 갱신)**이고, 재배포와 상업적 이용까지 허용된다. ISBN 서지정보 유통지원시스템(Seoji) API는 발행예정일 범위 검색을 지원해서, 신간·예정 ISBN을 날짜 구간별로 체계적으로 긁어올 수 있는 유일한 공식 경로다. 2026-01-12에 data.go.kr에 새로 열린 LOD 기반 OpenAPI 5종은 약 150개 필드를 준다. 하지만 날짜 필터가 없고 개발계정 트래픽이 10,000건이어서 단건 조회용으로 보는 게 맞다. 도서관 정보나루는 KDC, 대출통계, 도서관별 소장처럼 다른 데서 구할 수 없는 신호를 준다. 다만 약관이 복제와 제3자 제공을 막고 있고, 표지는 비영리 화면 표시에만 쓸 수 있다. 그래서 권장 구조는 이렇다. LOD 덤프로 처음 채우고, Seoji 날짜 구간 수집으로 신간을 더하고, 정보나루와 카카오는 저장하지 않는 실시간 보강원으로만 쓴다. 저장소는 PostgreSQL에 원본 JSONB, 정규화 테이블, pg_bigm을 얹어 bronze/silver/gold 3단으로 운영한다. 가장 큰 공백은 **표지, 판매가, 베스트셀러**다. 상업 API가 사라진 뒤로 이 세 가지를 합법적으로 대량 확보할 대체원이 없다.

## 2026년 가을, 상업 API는 카카오 하나만 남았고 그마저 DB 저장은 안 된다

먼저 상업 API의 상황이 이 설계 전체를 좌우한다. 네이버 개발자센터 약관 부칙은 Search API 가운데 쇼핑, 책, 학술정보 서비스가 **"2026년 7월 31일 24:00부로 종료"**된다고 정했다. 나머지 Search API는 NAVER API HUB로 옮겨 갔지만 책은 이전 대상에서 빠졌다 ([NAVER API 서비스 이용약관](https://developers.naver.com/products/terms/); [디지털데일리](https://m.ddaily.co.kr/page/view/2026071017302151678)). 알라딘은 2026-09-01 공지에서 15년 무료 운영에 따른 서버, 보안, 운영비 부담을 이유로 들었다. 그리고 **10월 30일 이후에는 기존 인증키로도 API 호출과 데이터 조회가 불가능**하다고 밝혔다. 프리미엄 API 신청도 함께 닫혔다 ([알라딘 OpenAPI 공지](https://blog.aladin.co.kr/openapi/17486624)). 알라딘의 ItemList(신간·베스트셀러 목록), salesPoint, 쪽수, 판형·무게, 목차, 저자 ID는 한국 책 메타데이터에서 가장 풍부한 상업 필드였다. 이들은 **상업적 대체원 없이 사라진다** ([알라딘 API 매뉴얼](https://docs.google.com/document/d/1mX-WxuoGs8Hy-QalhHcvuV17n50uGI2Sg_GHofgiePE/edit)). 교보문고와 YES24의 공개 개발자 API는 찾지 못했다. 인터파크도서는 2021년에 오픈마켓으로 전환했다 ([바이라인네트워크](https://byline.network/2021/09/9-99/)).

카카오 `dapi.kakao.com/v3/search/book`는 살아 있다. `KakaoAK` 헤더 인증을 쓰고, 응답 필드는 정확히 12개다. 제목, `contents`(소개), URL, `isbn`(10자리와 13자리가 공백으로 섞임), `datetime`, `authors`·`translators` 배열, 출판사, 정가(`price`), 판매가(`sale_price`), 썸네일, `status`다. 요청은 `page`와 `size`가 각각 최대 50이라 **쿼리당 최대 2,500건**만 볼 수 있다 ([Kakao 개발 가이드](https://developers.kakao.com/docs/ko/daum-search/dev-guide)). 쿼터는 **책 검색 하루 30,000건, 앱 전체 월 3,000,000건**이다. 다음(Daum) 검색 쪽에는 유료 초과 요금제가 공시돼 있지 않다 ([Kakao 쿼터](https://developers.kakao.com/docs/ko/getting-started/quota)). 결정적인 것은 운영정책이다. 정책은 사용자 환경 개선 외의 목적으로 캐시하거나 캐시 후 최신으로 유지하지 않는 행위를 금지한다. 또 **"카카오의 사전 승낙 없이 복사, 복제, 변경…"**하는 행위도 금지한다 ([Kakao 운영정책](https://developers.kakao.com/terms/latest/ko/site-policies)). 카카오 직원은 2026-10-15에 광고 기반 무료 앱은 괜찮다고 답했다. 하지만 같은 답변에서 저장 문제에는 답하지 않았다 ([DevTalk 152056](https://devtalk.kakao.com/t/api-ios/152056)). 이 조건으로는 카카오를 수집 원천으로 쓸 수 없다. 화면에 표시할 때 실시간으로 부르는 보강원으로 쓰는 것이 합리적이다. 카테고리, 쪽수, 목차, 신간 목록 엔드포인트가 없다는 점도 같은 결론으로 이끈다.

보조 소스도 사정이 비슷하다. Google Books는 키 없이 호출하면 2026-10-22 기준 일일 쿼터 0으로 HTTP 429를 돌려줬다. 이건 이 조사 중 직접 호출해서 확인한 결과다. Open Library는 번역판을 하나의 work로 합친다. 그래서 『채식주의자』 ISBN으로 조회하면 7개 언어, 26개 ISBN이 섞여 나온다. 한국 판(edition) 단위 메타데이터에는 부적합하다 ([Open Library 검색](https://openlibrary.org/search.json?isbn=9788936434120)).

## 국립중앙도서관이 수집, 증분, 라이선스를 모두 갖춘 유일한 원천이다

NLK 서비스는 세 갈래로 나뉜다. 기존 nl.go.kr Open API, 2026년에 새로 생긴 data.go.kr LOD API, 그리고 LOD 덤프와 SPARQL이다. 갈래마다 맡을 역할이 다르다.

### Seoji: 신간과 예정 ISBN을 날짜 구간으로 긁는 유일한 경로

엔드포인트는 `https://www.nl.go.kr/seoji/SearchApi.do`다. 필수 파라미터는 `cert_key`, `result_style`(json/xml), `page_no`, `page_size`다. 선택 파라미터로 **`start_publish_date`/`end_publish_date`(발행예정일 범위, yyyymmdd)**, `isbn`(우절단 전방일치), `set_isbn`, `deposit_yn`, `cip_yn`, `ebook_yn`, `form`이 있다. 정렬은 `sort=INPUT_DATE|PUBLISH_PREDATE`를 쓴다 ([NLK ISBN 서지정보 가이드](https://www.nl.go.kr/NL/contents/N31101030500.do)). 응답 필드는 상거래에 필요한 정보가 많다. 주요 필드는 다음과 같다. 상세는 같은 가이드에 있다.

- ISBN과 부가기호: `EA_ISBN`, `EA_ADD_CODE`(부가기호)
- 세트: `SET_ISBN`, `SET_ADD_CODE`, `SET_EXPRESSION`
- 서지: `VOL`, `SERIES_TITLE`/`SERIES_NO`, `EDITION_STMT`
- 가격: `PRE_PRICE`(예정가격), `REAL_PRICE`
- 분류와 형태: `KDC`, `DDC`, `PAGE`, `BOOK_SIZE`, `FORM`, `EBOOK_YN`
- 내용: `TITLE_URL`(표지), 목차·책소개·서평 인라인 텍스트
- 상태와 시각: `DEPOSIT_YN`, `INPUT_DATE`/`UPDATE_DATE`

일일 쿼터는 공식 가이드, 오류 코드표, data.go.kr 어디에도 나와 있지 않다 ([DeveloperAcademy-POSTECH Five-Guys](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md)). 오류 013 "쪽당 출력건수 제한"이 있다는 것만 공시돼 있고 숫자는 없다. 실제 운영 코드는 `page_size=200`으로 다음 달 날짜 구간을 페이지 단위로 넘기며 돌고 있다 ([WhatComicsComeNextMonth](https://github.com/ted1117/WhatComicsComeNextMonth/blob/HEAD/comic/services.py)).

품질은 감안하고 써야 한다. Seoji는 **출판사가 제출한 출간 전 데이터**다. 한 개발자의 표본 22권 중 약 절반은 PAGE와 BOOK_SIZE가 비어 있었다 ([moseori ADR 0004](https://github.com/Jiwook00/moseori/blob/HEAD/docs/adr/0004-%EC%95%8C%EB%9D%BC%EB%94%98%EC%97%90%EC%84%9C-%EC%B9%B4%EC%B9%B4%EC%98%A4%EB%A1%9C.md)). 같은 개발 문서에 따르면 `TITLE_URL`은 대부분 비어 있다. PAGE는 예정값이어서 소매점 값과 다를 수 있다. 예를 들어 『토지 1』은 400쪽으로 등록돼 있지만 알라딘에는 472쪽이다. NLK 계열 검색에서 같은 ISBN에 다른 기관(부산점자도서관)의 레코드가 붙어 나온 사례도 있다 ([Five-Guys](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md)). 목차, 책소개, 서평 **파일 URL**은 "21년 2월까지 생성된 데이터"만 제공된다 ([NLK 가이드](https://www.nl.go.kr/NL/contents/N31101030500.do)). 키는 NLK 회원가입 후 신청하고, **담당자 승인**을 받아야 쓸 수 있다. 승인에 걸리는 기간은 공시돼 있지 않다 ([NLK Open API 이용안내](https://www.nl.go.kr/NL/contents/N31101010000.do)).

### LOD 덤프와 SPARQL: CC0로 처음 채울 데이터

`lod.nl.go.kr`의 데이터셋은 2026-10-08에 모두 갱신됐다. 일반도서(전자책 포함)는 **3,980,216건(TTL 1,057.9MB, JSON-LD 883.5MB)**이다. 그 밖에 오프라인자료 7,151,860건, 온라인자료 21,236,692건, 학위논문 2,225,440건, 개인명 전거 1,859,505건, 주제명(NLSH) 257,764건이 있다. 라이선스 문구는 **"공공누리 제1유형 및 … CC0 1.0 조건에 따라 … 누구나 자유롭게 이용"**이다. 내려받을 때 소속, 기관명, 사용 목적을 적는 간단한 양식을 낸다 ([LOD 데이터셋 다운로드](https://lod.nl.go.kr/home/dataset/datadownload.do)). SPARQL 엔드포인트(`https://lod.nl.go.kr/sparql`)는 키 없이 쓸 수 있다. 2026-10-22 직접 질의 결과 `bibo:Book`이 3,644,964건이었다. 『아몬드』(9788936434267)를 조회하면 다음 값이 나온다. 이 값들은 출간 전 Seoji보다 실물을 보고 목록한 값에 가깝다.

- `bibframe:extent` "263 p", "20 cm"
- KDC 813.7, 청구기호
- KSH 주제 URI, KAC 저자 전거 URI
- 수상 주기, 번역 관계
- NANET, LIBRIS, OpenLibrary로의 `owl:sameAs`

### data.go.kr BookInformationService_v2: 필드는 많지만 단건 조회용

NLK는 2026-01-12 보도자료에서 LOD 약 3,000만 건을 서지, 저자, 주제, 도서관, 인터링킹 5개 범주의 OpenAPI로 data.go.kr에 공개한다고 발표했다 ([NLK 보도자료](https://www.nl.go.kr/NL/contents/N50603000000.do?schM=view&id=54867&schBcid=normal0302)). 서지 서비스(15154402)의 조건은 이렇다.

- 호스트: `apis.data.go.kr/1371029/BookInformationService_v2`
- 이용허락범위: "제한 없음", 무료
- 승인: 개발 자동승인, 운영 심의승인
- 트래픽: **개발계정 10,000건**, 활용사례를 등록하면 운영계정 상향

응답 필드는 약 150개이며 주요한 것은 다음과 같다 ([data.go.kr 15154402](https://www.data.go.kr/data/15154402/openapi.do)).

- 식별: `BIBO_isbn`
- 형태와 분류: `BIBFRAME_extent`, `NLON_kdc`/`NLON_ddc`, `DCTERMS_subject`
- 내용: `DCTERMS_tableOfContents`, `DCTERMS_abstract`
- 관계: `BIBO_translationOf`, `OWL_sameAs`
- 소장: `NLON_localHolding`

결정적 한계는 **날짜나 수정일 파라미터가 없다는 것**이다. 검색 조건은 표제, 제어번호, ISBN, 출판사, 총서명뿐이다. 가격 필드와 표지 필드도 없다. 페이지를 넘기며 전량을 수집하는 용도에는 맞지 않는다. 덤프에 없는 최신 레코드를 ISBN으로 하나씩 조회하는 데 쓰면 된다.

### 나머지 NLK API는 검색용이거나 기관 전용이다

소장자료 `search.do`와 대한민국 국가서지 `seojiSearch.do`에는 **"DATA LIMIT 500: 500건 이후 데이터 조회불가"**라는 하드 캡이 있다. 응답에도 쪽수, 크기, 가격이 없다 ([소장자료 가이드](https://www.nl.go.kr/NL/contents/N31101030700.do); [국가서지 가이드](https://www.nl.go.kr/NL/contents/N31101031100.do)). 출판예정도서 `cip.do`는 아직 응답한다. 하지만 메뉴에서 빠졌고, Seoji의 `deposit_yn=N`(미납본 목록)이 그 자리를 이었다 ([출판예정도서 가이드](https://www.nl.go.kr/NL/contents/N31101030800.do)). KORMARC 원본과 목차 대량 데이터는 KOLIS-NET으로만 나온다. 조건은 **"영리적 이용을 제한하기 위하여 … 승인된 기관에 한하여 제공 … (단, 개인은 대상에서 제외)"**다 ([KOLIS-NET 참여방법](https://www.nl.go.kr/kolisnet/contents/procedure.do)). 정리하면 개인이나 상업 프로젝트가 MARC를 직접 받을 길은 없다. LOD가 사실상 MARC를 대신한다.

## 정보나루, KPIPA, 국회도서관, RISS는 보강재로 쓴다

도서관 정보나루(data4library.kr)도 NLK가 운영하지만 성격이 다른 제품이다. 2026-06판 매뉴얼에 19개 API가 있다. 이 중 `itemSrch`(도서관별 장서)는 도서관별 청구기호, 복본 코드, `reg_date`, `class_no`(KDC)를 주는 유일한 엔드포인트다. 인기대출, 이용분석, 키워드, 함께 대출된 도서는 상업 API에 없는 신호다. `addition_symbol`(부가기호)과 `set_isbn13`도 별도 필드로 나온다 ([data4library API 매뉴얼 v20260620](https://www.data4library.kr/downloadApiManual)). 쿼터는 두 단계다. 서버 IP를 등록하지 않으면 **하루 500건 남짓**이고 ([공지 cn=88](https://data4library.kr/noticeV?cn=88)), IP를 등록하면 2023-11-20부터 **하루 30,000건 상한**이다 ([공지 cn=194](https://www.data4library.kr/noticeV?cn=194)). 대량 수집 경로로는 도서관별 월간 장서·대출 데이터셋 **1,678건**이 있다. 데이터셋마다 별도 이용신청과 승인이 필요하다 ([openDataL](https://www.data4library.kr/openDataL)). 라이선스는 이 보고서에서 다룬 공공 소스 중 가장 제한적이다. 공공누리 표기가 없고, 약관 제12조는 사전 승낙 없는 복제와 제3자 제공을 이용 제한 사유로 든다 ([정보나루 이용약관](https://www.data4library.kr/newSub01_01)). 매뉴얼은 **`bookImageURL`을 비영리 서비스의 화면 표시에만 쓰도록 허용하고, 영리 이용, 복사·저장·재배포, AI 입력·학습을 금지**한다 ([API 매뉴얼](https://www.data4library.kr/downloadApiManual)). 그래서 정보나루 데이터는 원본 그대로 재배포하지 말아야 한다. 대신 KDC 교차검증, 인기도 점수, 소장 여부처럼 가공한 신호로만 DB에 반영하는 편이 안전하다. 다만 이 우회가 약관상 명시적으로 허용되는지는 확인하지 못했다.

KPIPA 출판유통통합전산망은 출판사가 ONIX 3.0 기반으로 입력하는 메타데이터를 다룬다. 이 데이터는 5분마다 서점으로 전송된다 ([KPIPA 메타데이터 서비스](https://bnk.kpipa.or.kr/home/v3/center/centerGuideServiceMetaData)). 하지만 Open API 제공 범위는 **2021-09-29 이후 발행분 중 제공에 동의한 출판사 도서**에 한정된다 ([KPIPA 뉴스레터](https://bnkkpipa.stibee.com/p/12)). 키는 운영위원회 심사를 거쳐 1년 단위로 나온다. 약관은 사전 동의 없는 제3자 제공을 금지하고, **다른 정보와 섞지 않고 독립적으로 노출**하라고 요구한다 ([KPIPA Open API 약관](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)). 여러 원천을 병합하는 DB와는 정면으로 맞지 않는 조건이다. 엔드포인트와 필드 명세도 승인 전에는 공개되지 않는다.

국회도서관 API는 data.go.kr `ServiceKey`로 쓴다. 개발계정은 하루 약 10,000건, 운영계정은 최대 100,000건이고 `displaylines`는 최대 100이다. 라이선스는 **공공누리 제1유형**이어서 공공 소스 중 가장 관대하다. 응답이 name/value 쌍이라 별도 파서가 필요하고, 강점은 학위논문과 목차다 ([NANET OpenAPI 가이드](https://openapi.nanet.go.kr/S1001.html); [data.go.kr 15098174](https://www.data.go.kr/data/15098174/openapi.do)). RISS 단행본 API는 대학도서관 소장(`holdings`)을 주지만 **BY-NC-ND**이고 심사 후 승인한다. 상업 DB에는 쓸 수 없다 ([RISS 단행본 API](https://www.riss.kr/apicenter/apiSearchBook.do)).

## 한눈에 보는 비교: 필드보다 라이선스 차이가 더 크다

아래 표는 2026-10-22 기준이다. "DB 저장"은 원천 데이터를 자체 DB에 지속 보관해도 되는지를 약관 문구에 비춰 판단한 것이다. "추론"으로 표시한 칸은 명시 약관이 없어 간접 근거로 판단했다.

| API | 상태(2026-10) | 핵심 제공 정보 | 인증 | 쿼터·페이징 상한 | 라이선스 | DB 저장 | 대량수집 경로 |
|---|---|---|---|---|---|---|---|
| NLK Seoji `SearchApi.do` | 활성 | ISBN, 부가기호, 세트 ISBN, 예정·실제 가격, KDC/DDC, 쪽수·크기(절반가량 공란), 형태, 목차·책소개, 입력·수정일 | NLK 회원 + 키(담당자 승인) | 공식 쿼터 미공시, 쪽당 상한 숫자 미공시(200 실사용) | 명시 약관 없음, data.go.kr 미러는 "제한 없음" | 사실 메타데이터는 가능(추론), 표지·책소개 텍스트는 위험 | **발행예정일 범위 sweep** |
| NLK LOD 덤프 / SPARQL | 활성, 2026-10-08 갱신 | 일반도서 398만 건, 형태사항, KDC, 주제명·저자 전거 URI, 번역 관계, sameAs | 덤프는 간단 신청서, SPARQL은 키 없음 | 덤프는 무제한, SPARQL 한도 미공시 | **공공누리 1유형 + CC0** | **가능(재배포 포함)** | **전량 덤프(TTL/RDF-XML/JSON-LD)** |
| data.go.kr BookInformationService_v2 등 5종 | 2026-01-12 신설 | LOD와 같은 약 150필드, 저자·주제·인터링킹 별도 서비스 | data.go.kr serviceKey | 개발 10,000건, 운영은 심의 후 상향 | "제한 없음" | 가능 | 없음(날짜 필터 없음) → 단건 조회 |
| NLK `search.do` / KOLIS-NET / 국가서지 `seojiSearch.do` | 활성 | 표제·저자·발행사항·청구기호 정도 | NLK 키 | **결과 500건 하드 캡** | 명시 없음 | 추론상 가능 | 없음 |
| KOLIS-NET MARC·목차 | 활성 | KORMARC 원본, 목차 | 기관 신청(FAX/우편/메일) | — | **영리 이용 제한, 개인 제외** | 승인 기관 내부만 | 기관 한정 |
| 도서관 정보나루 | 활성(MCP 신설) | KDC, 부가기호, 세트 ISBN, 대출통계, 도서관별 소장·청구기호, 키워드 | 회원 + 인증키 + 서버 IP 등록 | IP 미등록 약 500건/일, 등록 30,000건/일 | 공공누리 없음, 복제·제3자 제공 제한, 표지 비영리 표시만 | **원본 저장·재배포 위험** | 도서관별 월간 덤프 1,678건(데이터셋별 승인) |
| KPIPA 출판유통통합전산망 | 활성 | ONIX 3.0, 출판사 입력, 출간예정 | 위원회 심사, 1년 키 | 운영기관 재량 | 사전 동의 없는 제3자 제공 금지, 독립 노출 | 승인 범위 내 | 없음(명세 비공개) |
| 국회도서관 | 활성 | 소장 서지, 청구기호, 학위논문, 목차 | data.go.kr ServiceKey | 개발 약 1만/일, 운영 최대 10만/일, 100건/페이지 | **공공누리 1유형** | 가능 | 페이지 조회만 |
| RISS 단행본 | 활성 | 대학도서관 단행본, 소장 기관 | 심사 승인(기관 대상) | 100건/페이지 | **BY-NC-ND** | 비영리만 | 없음 |
| 카카오 책 검색 | 활성(유일한 상업 API) | 12필드: 표지 썸네일, 소개(잘림), 정가·판매가, 저자·역자 배열 | KakaoAK REST 키 | 30,000/일, 쿼리당 2,500건 | 운영정책상 UX 목적 캐시만 허용 | **불가(사전 승낙 필요)** | 없음 |
| 네이버 책 검색 | **2026-07-31 종료** | — | — | — | 종료 전에도 DB화 명시 금지 | 불가 | — |
| 알라딘 TTB | **2026-10-30 종료**, 신규 발급 9/4 중단 | 표지 200px, 판매지수, 베스트셀러, 쪽수, 판형, 목차 | TTB 키 | 5,000/일(프리미엄 10만) | 저장(캐시 포함)·가공 금지 | 불가 | 종료 |

필드별로 다시 보면 역할 분담이 분명해진다. ●는 안정적으로 제공, ◐는 부분적이거나 공란이 많거나 조건부, ○는 제공하지 않음이다. 근거는 앞서 인용한 각 API 가이드와 매뉴얼이다. 알라딘은 종료 직전의 비교 기준으로만 넣었다.

| 필드 | Seoji | LOD / BookInfo_v2 | 정보나루 | 카카오 | 알라딘(종료) |
|---|---|---|---|---|---|
| ISBN-13 | ● `EA_ISBN` | ● `BIBO_isbn` | ● `isbn13` | ◐ 10·13자리 혼재 | ● |
| 세트 ISBN | ● `SET_ISBN` | ○ | ● `set_isbn13` | ○ | ○ |
| 부가기호 | ● `EA_ADD_CODE` | ○ | ● `addition_symbol` | ○ | ● `subbarcode` |
| 표제·부표제 | ◐ 본표제만 | ● 표제 + 나머지 표제 | ● | ● | ● 부제는 상세 조회 |
| 권차·총서 | ● | ● | ◐ `vol`만 | ○ | ◐ `seriesInfo` |
| 저자 | ◐ 책임표시 문자열 | ● 문자열 + 전거 URI | ◐ 문자열 | ● 배열 | ◐ 문자열(상세는 ID 포함) |
| 역자 분리 | ○ | ◐ | ○ | ● `translators` | ◐ |
| 발행일 | ◐ 예정일 | ◐ 주로 연도 | ◐ 연도 | ● ISO 8601 | ● |
| 판사항 | ● | ● | ○ | ○ | ○ |
| 쪽수·크기 | ◐ 절반가량 공란 | ● `extent` 텍스트 | ○ | ○ | ● 상세 조회 |
| 정가 | ● 예정·실제 가격 | ○ | ○ | ● | ● |
| 판매가 | ○ | ○ | ○ | ● | ● |
| KDC / DDC | ● | ● | ◐ KDC만 | ○ | ○ 자체 카테고리 |
| 주제명·키워드 | ◐ | ● KSH/NLSH | ◐ 가중 키워드 | ○ | ○ |
| 목차·소개 | ◐ 파일 URL은 2021-02까지 | ◐ | ◐ `description` | ◐ 잘린 소개 | ◐ 프리미엄·요청 시 |
| 표지 | ◐ 대부분 공란 | ○ | ◐ 비영리 표시만 | ● 저장 불가 | ● |
| 제본·전자책 구분 | ● `FORM`, `EBOOK_YN` | ◐ 자료유형 | ○ | ○ | ◐ |
| 번역 원서 관계 | ○ | ● | ○ | ○ | ◐ `originalTitle` |
| 소장·청구기호 | ○ | ◐ NLK 소장만 | ● 도서관별 | ○ | ○ |
| 대출·판매 인기 | ○ | ○ | ● 대출 | ○ | ● 판매지수 |
| 변경 추적 시각 | ● 입력·수정일 | ◐ 재발행 시각 | ◐ `reg_date` | ○ | ○ |

이 매트릭스에서 읽히는 것은 세 가지다. 첫째, **세트 ISBN, 부가기호, 가격, 전자책 구분은 Seoji만** 안정적으로 준다. 둘째, **실물 기준 형태사항, 전거, 주제명, 번역 관계는 LOD만** 준다. 셋째, 표지, 판매가, 인기 신호는 저장이 금지되거나 비영리로 묶인 소스에만 있다. 그래서 두 NLK 원천을 합치면 "법적으로 깨끗한 핵심 레코드"가 된다. 나머지는 표시할 때 붙이는 장식층으로 다루는 것이 이 지형에 맞는 설계다.

## LOD 덤프로 처음 채우고, Seoji 날짜 구간으로 증분한다

NLK가 제공하는 것 중 OAI-PMH나 공식 수정일 피드는 없다. 그래서 증분 수집은 다음 세 단계를 조합해야 한다. 첫 단계에서 LOD 일반도서 덤프를 ISBN과 `BIBLIO_ID` 기준으로 적재한다. 두 번째 단계에서 Seoji를 하루나 일주일 단위의 `start_publish_date`/`end_publish_date` 구간으로 훑어 신간과 예정 ISBN을 확보한다. 구간을 작게 잡으면 구간당 `TOTAL_COUNT`가 작아진다. 그러면 공시되지 않은 페이징 상한(오류 013)에 걸릴 위험이 줄어든다. 단 이 가정 자체는 검증하지 못했다. Seoji의 `INPUT_DATE`와 `UPDATE_DATE`는 응답에만 있고 요청 필터로는 쓸 수 없다 ([NLK 가이드](https://www.nl.go.kr/NL/contents/N31101030500.do)). 그래서 출간 예정일이 지나 가격이나 쪽수가 바뀐 레코드를 잡으려면 **최근 수개월 구간을 겹쳐서 다시 훑어야** 한다. `DEPOSIT_YN`을 보존하면 실제로 납본된 책과 예고만 된 책을 구분할 수 있다. 세 번째 단계는 덤프 이후 NLK가 새로 목록한 책을 BookInformationService_v2로 ISBN 단건 조회하는 것이다. 덤프는 몇 달마다 다시 받아 diff한다. LOD 레코드의 `nlon:datePublished`는 증분 기준으로 쓰지 않는다. 2017년 목록 레코드가 2026-10-11 값을 달고 있어 재발행 때 초기화되는 것으로 보이기 때문이다. 이것도 검증되지 않은 관찰이다.

규모는 한 대의 서버로 충분하다. 출협이 2026-05-29에 발표한 2025년 신간은 **64,491종**이다. 일부 매체는 64,991종으로 보도했다 ([뉴시스](https://www.newsis.com/view/NISX20260529_0003649654); [아시아경제](https://view.asiae.co.kr/article/2026052916413614584)). 이 숫자는 출협 납본분만 센 것이다. 전자출판물 ISBN의 **96.2%가 전자책**이라는 연구를 보면 ([KBIBLIA 35(1)](https://www.accesson.kr/kbiblia/assets/pdf/42257/journal-35-1-127.pdf)), 연간 ISBN 총량은 이보다 몇 배 많을 것이다. 다만 검증된 연간 ISBN 발급 총수는 찾지 못했다. 400만 건 규모의 정규화 레코드는 수십 GB 안에 들어간다는 것이 이 보고서의 추정이다. 표지를 복제하면 수백 GB로 늘어난다. 증분 주기에 필요한 호출량도 작다. Seoji 일 단위 sweep은 하루 몇 번에서 수십 번 호출이면 끝난다.

파이프라인은 bronze/silver/gold 3단으로 나눈다. **bronze**는 모든 응답을 `(source, source_key, fetched_at, request_params, body, body_sha256)`로 추가만 하는 저장소다. 해시가 같으면 `last_seen_at`만 갱신한다. **silver**는 bronze에서 결정적 함수 `normalize → merge`로 재생성한다. 이렇게 하면 병합 규칙을 바꿀 때 쿼터가 걸린 API를 다시 부를 필요가 없다. **gold**는 검색 인덱스와 work 클러스터다. 이 구조는 Open Library의 설계를 따른다. Open Library는 레코드마다 `revision`과 `last_modified`를 두고, 병합은 redirect, 삭제는 별도 tombstone 덤프로 표현한다 ([Open Library dumps](https://openlibrary.org/developers/dumps)). 처음에는 cron이나 GitHub Actions에 Python 스크립트 하나면 충분하다. 소스와 백필이 늘어나면 날짜·소스 파티션 단위의 asset으로 매핑되는 Dagster 같은 도구가 맞다. NLK 응답은 가끔 느리거나 끊긴다. 그래서 7–10초 타임아웃, 지수 백오프, "0건"을 TTL이 있는 음성 캐시로 처리하는 방식이 필요하다 ([Five-Guys](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md)).

## ISBN-13을 축으로 필드 단위 출처를 남기고 PostgreSQL에 저장한다

### 스키마: 판(edition)을 기본 행으로, 작품(work)과 세트는 따로 둔다

FRBR/LRM, BIBFRAME, Open Library, schema.org는 모두 추상적인 작품(work)과 구체적인 판(edition/manifestation)을 분리한다. ISBN은 판을 식별한다 ([schema.org/workExample](https://schema.org/workExample); [Open Library 스키마](https://openlibrary.org/about/schema)). 그래서 `edition` 행의 기본키는 `isbn13 CHAR(13)`이고, `work_id`는 나중에 클러스터링으로 채우는 nullable 열로 둔다. 기여자는 `edition_contributor(isbn13, contributor_id, role, role_raw, ordinal)`로 분리한다. `role_raw`에는 지음, 글, 그림, 옮김, 엮음, 감수 같은 원문을 보존한다. 세트는 플래그가 아니라 `set_isbn`/`set_member`로 다대다 연결한다. 총서(시리즈)는 세트와 별도 개념이라 `edition_series`로 분리한다. 판매가처럼 변동하는 값은 `price_observation` 시계열 테이블에 둔다. 출처는 `field_provenance(isbn13, field, source, raw_value, chosen)`에 기록한다. Open Library 덤프를 PostgreSQL JSONB 3테이블에 적재한 뒤 조인 테이블을 추출하는 패턴이 그대로 참고가 된다 ([Bookdata-tools](https://www.dagshub.com/gopalsinghal/Bookdata-tools/src/master/docs/data/openlib.md)).

### ISBN과 부가기호: 13자리로 통일하고 부가기호는 세 열로 쪼갠다

입력은 숫자와 X만 남기고, 10자리면 mod-11 검증 후 978을 붙여 13자리로 변환하고, mod-10 체크 숫자를 검증한다. ISBN-10은 978로 시작하는 번호에서만 파생 별칭으로 저장한다. **979-11에는 ISBN-10이 존재하지 않기** 때문이다. 한국 ISBN은 978-89 또는 979-11로 시작한다. 발행자번호가 2–6자리로 가변이라 고정 위치로 하이픈을 넣을 수 없다. 하이픈 표기에는 ISBN International 범위 파일이 필요하다 ([NLK ISBN 구성](https://nl.go.kr/seoji/contents/S20101050000.do); [ISBN Users' Manual](https://www.isbn-international.org/content/isbn-users-manual)). 소스마다 따로 처리할 것도 있다. 카카오는 "ISBN10 ISBN13"을 공백으로 붙여 주고, 978/979가 아닌 13자리 코드(예: 2090000157222)를 주기도 한다. NLK에 질의하기 전에 반드시 검증해야 한다 ([Five-Guys](https://github.com/DeveloperAcademy-POSTECH/2024-MacC-A6-Five-Guys/blob/HEAD/services/book-search/sources.md)). Seoji의 `isbn` 파라미터는 전방일치여서, 짧은 값을 넣으면 여러 건이 돌아온다.

부가기호 5자리는 다음과 같이 세 열로 분해한다 ([NLK 부가기호 안내](https://nl.go.kr/seoji/contents/S20101050000.do)).

| 자리 | 의미 | 값 |
|---|---|---|
| 1 | 독자대상 | 0 교양, 1 실용, 4 청소년, 5 중·고 학습참고서, 6 초등 학습참고서, 7 아동, 9 전문 |
| 2 | 발행형태 | 0 문고본, 1 사전, 2 신서판, 3 단행본, 4 전집·총서·다권본·시리즈, 5 전자출판물, 6 도감, 7 그림책·만화, 8 혼합자료 |
| 3–4 | 내용분류 | KDC 주류·강목(3번째 자리 0 총류 … 9 역사), 5번째 자리는 항상 0 |

세트는 개별 권과 일련번호가 연속하고, 부가기호 둘째 자리만 3에서 4로 바뀐다(예: 03820 → 04820). 이 값은 출판사가 신고한 것이어서 통제가 약하다. 그래서 확정값이 아니라 힌트로 쓴다. 쓰임새는 세 가지다. 아동·청소년·학습 패싯을 나누고, 전자책(5)과 만화·그림책(7)을 판별하고, KDC가 없을 때 3–4번째 자리를 대체 분류로 쓴다.

### 병합: 필드마다 우선순위를 따로 두고 원천 사실과 판정 결과를 분리한다

ISBN-13이 소스 간 조인 키다. 레코드를 통째로 덮어쓰지 않고 필드마다 우선순위를 둔다. 상업 API가 빠진 지금 기본값은 다음과 같다.

| 필드 | 우선순위 |
|---|---|
| 표제 | LOD → Seoji → 카카오 |
| 기여자와 역할 | LOD 전거 → Seoji 책임표시 파싱 → 카카오 배열(역자 분리 보조) |
| 형태사항 | LOD `extent` → Seoji `PAGE`/`BOOK_SIZE` |
| 분류 | LOD KDC → Seoji KDC → 정보나루 `class_no` → 부가기호 3–4번째 자리 |
| 부가기호, 세트, 가격, 전자책 구분 | Seoji 단독 |
| 발행일 | LOD 실제 연도와 Seoji 예정일을 둘 다 보존하고 정밀도 열을 따로 둔다 |

책임표시 문자열은 `;`로 나누고, 그 안의 이름은 `,`, `·`, `&`로 나눈다. 끝의 역할어는 사전으로 매핑한다. 지음·저·글은 저자, 옮김·역은 역자, 그림은 그림 작가, 엮음·편은 편자, 감수는 감수자, 원작은 원작자다. 텍스트 비교 키는 따로 만든다. 순서는 HTML 태그 제거와 엔티티 복원, NFKC 정규화, 가운뎃점과 괄호 통일, 한자 병기 `\(([\p{Han}]+)\)` 분리, 권차·판차 표지(`제?\d+권`, 개정판, 리커버, 양장) 제거다. 원값은 NFC로 따로 보존한다. 판을 작품으로 묶는 클러스터링은 오프라인에서 한다. 정규화 표제와 첫 저자로 블로킹하고, 표제 bigram Jaccard에 원서 동일성을 더해 점수를 매긴다. 결과는 원천 사실과 분리해 저장한다. 서로 다른 ISBN을 하나의 판으로 자동 병합해서는 안 된다. 같은 ISBN인데 소스 간 표제 유사도가 매우 낮으면 출판사의 ISBN 재사용이나 앞서 본 타 기관 레코드 혼입을 의심하고 플래그를 단다. LLM 출력(원서명 추출, KDC 제안, 중간 신뢰도 쌍 판정)은 `source='llm:<model>'`와 신뢰도와 함께 저장하고, 권위 있는 필드를 덮어쓰지 않는다.

### 저장소와 검색: PostgreSQL + pg_bigm이 기본, 2음절 검색이 관건이다

한국어 검색의 핵심 문제는 조사다. PostgreSQL 기본 `to_tsquery('simple','대한민국')`은 "대한민국은"을 찾지 못한다. 한국어 위키백과 10만 문서로 비교한 결과, pg_bigm은 "대한민국"으로 **27,846건**을 찾았고 tsvector는 **14,465건**에 그쳤다. 일상어 100개 전체로는 pg_bigm이 약 304% 더 많이 찾았다 ([AWS 기술 블로그](https://aws.amazon.com/ko/blogs/tech/aurora-postgresql-pg-bigm-pgvector-korean-hybrid-search/)). 같은 글은 pg_bigm 유사도와 pgvector HNSW를 RRF(k=60)로 합치는 하이브리드 구성도 제시한다. 원본 JSONB, 정규화 테이블, 검색, 임베딩을 한 시스템에 둘 수 있으니 소규모 팀에는 PostgreSQL + JSONB + pg_bigm(+pgvector)이 기본값이다.

개인용이나 정적 사이트라면 SQLite도 된다. 다만 FTS5 trigram 토크나이저는 **3글자 미만 질의에서 결과가 없다** ([SQLite FTS5](https://sqlite.org/fts5.html)). "역사", "철학" 같은 2음절 핵심어가 인덱스를 못 탄다. 그래서 별도 bigram 열이나 LIKE 스캔으로 보완해야 한다. 형태소 분석이 필요하면 Elasticsearch/OpenSearch에 nori(mecab-ko-dic, 사용자 사전, `decompound_mode`)를 붙인다. 가장 정교하지만 JVM 운영 부담이 따르고 동기화할 진실 원천이 둘로 늘어난다 ([Elastic nori](https://www.elastic.co/docs/reference/elasticsearch/plugins/analysis-nori-tokenizer)). Meilisearch는 lindera 한국어 사전을 써서 운영이 가볍다. 대신 한국어 분석을 세밀하게 조정하기는 어렵다 ([Meilisearch 언어 지원](https://www.meilisearch.com/docs/learn/resources/language)). bronze 원본은 날짜·소스 파티션의 gzip JSONL이나 Parquet으로 오브젝트 스토리지에 두고, DuckDB로 그 자리에서 재처리하면 된다.

표지는 기본적으로 핫링크하고 URL과 해시만 저장한다. 공공 소스 중 표지를 안정적으로 주는 곳은 없다. 정보나루 표지는 비영리 표시로 묶여 있고, 카카오 썸네일은 저장할 수 없다. Seoji 표지와 책소개 텍스트는 출판사 저작물일 가능성이 있다. 이들을 대량으로 복제하려면 법적 확인이 먼저다. 이 판단은 NLK의 명시적 진술이 아니라 이 보고서의 추론이다.

## 결론

2026년의 변화는 한국 책 DB의 경제학을 뒤집었다. 지금까지는 상업 API가 풍부한 필드를 주고 공공 API는 빈약한 보조였다. 이제는 **법적으로 저장하고 재배포할 수 있는 핵심 레코드는 NLK의 LOD(CC0)와 Seoji뿐**이다. 상업 데이터는 저장할 수 없는 표시용 장식층이 됐다. 이 변화는 기회이기도 하다. 공개된 한국 오픈소스 선행 사례는 대부분 알라딘이나 카카오를 감싼 얇은 클라이언트다. 다중 소스를 병합하고 출처를 추적하는 공개 카탈로그는 이번 조사에서 찾지 못했다. NLK 파생 필드만으로 덤프를 만들어 공개하면 Open Library의 한국판 같은 공공재가 될 수 있다. 법적으로 깔끔하게 공개할 수 있는 거의 유일한 구성이기도 하다.

남은 공백과 불확실성은 분명하다. Seoji의 일일 쿼터, 페이지 상한, 표지·책소개 텍스트의 권리 관계는 공시되지 않았다. 대량 수집을 시작하기 전에 NLK 디지털정보기획과(02-590-0548)에 서면으로 확인받는 것이 가장 비용 대비 효과가 큰 다음 단계다. 표지, 판매가, 베스트셀러는 KPIPA 위원회 승인이나 출판사와의 개별 협약 외에는 합법적 대량 경로가 없다. 그러니 제품 범위를 정할 때 이 세 가지가 꼭 필요한지부터 따져야 한다.
