# Commercial (private-sector) Korean book search APIs, as of October 2026

Research date: 2026-10-22. **Headline: the landscape changed sharply in 2026.** Naver's book search API was **shut down on 2026-07-31**. Aladin's Open API **stopped issuing new keys on 2026-09-04 and shuts down entirely on 2026-10-30**, eight days after this research date. That leaves **Kakao (Daum) book search as the only general-purpose commercial Korean book search API still open to new developers.** Every claim below has a URL; items without a source are under Gaps.

---

## Q1. Is each API still current, and what are its endpoints, parameters, response fields, auth, quotas and pagination caps?

### Takeaway
Kakao `dapi.kakao.com/v3/search/book` is live. It has 12 document fields, allows 30,000 calls/day for book search, and returns at most 50 pages × 50 results (2,500) per query. Naver book search (`book.json` / `book_adv.xml`) ended on 2026-07-31 and was not moved to NAVER API HUB. Aladin TTB (ItemSearch, ItemList, ItemLookUp, ItemOffStoreList) ends on 2026-10-30. I found no public API for Kyobo, YES24 or Interpark Book.

### Cited Findings

#### Kakao (Daum) book search: LIVE
- **Endpoint:** `GET https://dapi.kakao.com/v3/search/book`. **Auth:** a required header, `Authorization: KakaoAK ${REST_API_KEY}`. The REST API key comes from an app registered on Kakao Developers. — [Kakao Daum search dev guide](https://developers.kakao.com/docs/ko/daum-search/dev-guide)
- **Request params:** `query` (required). `sort` = `accuracy` (default) or `latest` (publication date). `page` 1–50, default 1. `size` 1–50, default 10. `target` = `title` | `isbn` | `publisher` | `person`. — [Kakao dev guide](https://developers.kakao.com/docs/ko/daum-search/dev-guide)
- **Response `meta`:** `total_count`, `pageable_count` (displayable documents with duplicates removed), `is_end`. — [Kakao dev guide](https://developers.kakao.com/docs/ko/daum-search/dev-guide)
- **Response `documents[]` (exactly 12 fields):** `title`, `contents` (description), `url` (Daum book detail page), `isbn` (ISBN10, ISBN13, or both separated by a space), `datetime` (ISO 8601 publication date), `authors` (String[]), `publisher`, `translators` (String[]), `price` (list price), `sale_price`, `thumbnail`, `status`. For `status` (normal, out of stock, out of print, etc.), the docs say the value can change and should be used for display only, not in string-matching logic. — [Kakao dev guide](https://developers.kakao.com/docs/ko/daum-search/dev-guide)
- **Format:** JSON only, since the docs show no XML variant. — [Kakao dev guide](https://developers.kakao.com/docs/ko/daum-search/dev-guide)
- **Quota:** Daum search as a whole allows **50,000/day**. Each sub-API, **책 검색** included, is capped at **30,000/day**. The app-wide monthly cap across all APIs is **3,000,000**. The quota page lists no Daum-specific per-second limit and no paid overage tier for Daum search; it shows paid overage pricing only for KakaoTalk sharing and Kakao Map. — [Kakao quota page](https://developers.kakao.com/docs/ko/getting-started/quota)
- **Pagination cap:** page ≤ 50 and size ≤ 50, so at most **2,500 results per query**. — [Kakao dev guide](https://developers.kakao.com/docs/ko/daum-search/dev-guide)
- **Pricing and higher quota:** free within the quota. On 2026-10-15, a Kakao staff member pointed questions about exceeding the free quota or partnerships to Daum customer support and Daum partnership contacts. — [DevTalk thread 152056](https://devtalk.kakao.com/t/api-ios/152056)

#### Naver Search API, book: DISCONTINUED 2026-07-31
- **What it was:** `GET https://openapi.naver.com/v1/search/book.json` (and `.xml`), plus `book_adv.xml` (detailed search, XML only). Auth was the `X-Naver-Client-Id` / `X-Naver-Client-Secret` headers. Params were `query`, `display` (default 10, max 100), `start` (default 1, max 1000) and `sort` = `sim` | `date`. In the current docs, `book_adv` accepts only **`d_titl` and `d_isbn`**; the older `d_auth`/`d_cont`/`d_publ`/`d_dafr`/`d_dato`/`d_catg` are no longer documented. The daily limit was 25,000 calls for the Search API as a whole. — [Naver book search doc](https://developers.naver.com/docs/serviceapi/search/book/book.md)
- **Documented response fields:** `title`, `link` (Naver book info URL), `image`, `author`, `discount` (sale price; omitted when there is no price, e.g. out of print), `publisher`, `isbn`, `description`, `pubdate`. The list price field `price` is **missing from the field table** but still appears in the old sample response. — [Naver book search doc](https://developers.naver.com/docs/serviceapi/search/book/book.md)
- **Shutdown:** the NAVER API terms (revised 2026-10-07), Addendum Art. 2③, say: "네이버 개발자센터를 통한 'Search API' 중 '쇼핑', '책', '학술정보' 데이터 제공 서비스는 2026년 7월 31일 24:00부로 종료". Existing users lost access from 2026-08-01 00:00. The rest of the Search API stopped taking new applications on 2026-07-30 24:00, remains available to existing users until 2027-06-30, and then moves to NAVER API HUB on Naver Cloud Platform. — [NAVER API 서비스 이용약관](https://developers.naver.com/products/terms/)
- Press coverage agrees: the shopping, book and academic APIs were left out of the API HUB migration, and calls with existing keys were blocked after 2026-07-31. — [TokenPost (search snippet; page returned 404 when fetched)](https://www.tokenpost.kr/news/ai/403521); [ddaily, 2026-07-10](https://m.ddaily.co.kr/page/view/2026071017302151678); [brunch commentary](https://brunch.co.kr/@ainote/123)
- The doc page `developers.naver.com/docs/serviceapi/search/book/book.md` was still online at research time, even though the service has ended. — [Naver book doc](https://developers.naver.com/docs/serviceapi/search/book/book.md)

#### Aladin Open API (TTB key): SHUTTING DOWN 2026-10-30
- **Shutdown notice (2026-09-01):** the whole book search and book information API is ending. **New key issuance ended 2026-09-04**, and **existing users lose service on 2026-10-30**: "10월30일 이후에는 기존 인증키를 이용한 API 호출 및 데이터 조회가 불가능". The stated reason is rising server, network, security and operating costs after about 15 years of free service. New Premium API applications also closed on 2026-09-04. — [Aladin OpenAPI notice](https://blog.aladin.co.kr/openapi/17486624); [API 이용 안내 category](https://blog.aladin.co.kr/openapi/category/29154404)
- **Endpoints, from the manual last updated 2022-07-13:**
  - `http://www.aladin.co.kr/ttb/api/ItemSearch.aspx` (search)
  - `ItemList.aspx` (lists)
  - `ItemLookUp.aspx` (single item)
  - `ItemOffStoreList.aspx` (used-book store stock)

  Source: [Aladin Open API manual (Google Doc)](https://docs.google.com/document/d/1mX-WxuoGs8Hy-QalhHcvuV17n50uGI2Sg_GHofgiePE/edit), linked from [blog.aladin.co.kr/openapi](https://blog.aladin.co.kr/openapi/5353294)
- **ItemSearch params:**
  - `TTBKey`, `Query`
  - `QueryType` = Keyword (title+author, default) | Title | Author | Publisher
  - `SearchTarget` = Book | Foreign | Music | DVD | Used | eBook | All
  - `Start`; `MaxResults` 1–100
  - `Sort` = Accuracy | PublishTime | Title | SalesPoint | CustomerRating | MyReviewCount
  - `Cover` = Big (200px) | MidBig (150px) | Mid (85px, default) | Small (75px) | Mini (65px) | None
  - `CategoryId`; `Output` = XML | JS (JSON); `Partner`; `includeKey`; `InputEncoding`; `Version` (latest is 20131101)
  - `outofStockfilter`; `RecentPublishFilter` (0–60 months); `OptResult` (ebookList, usedList, fileFormatList)

  The manual adds: "한 페이지에 최대 50개, 총 결과는 200개까지만 검색 가능". — [Aladin manual](https://docs.google.com/document/d/1mX-WxuoGs8Hy-QalhHcvuV17n50uGI2Sg_GHofgiePE/edit)
- **ItemList params:** `QueryType` = ItemNewAll | ItemNewSpecial | ItemEditorChoice (by category only) | Bestseller | BlogBest (domestic books only). Plus `SubSearchTarget` (for Used), `CategoryId`, and `Year`/`Month`/`Week` for past bestseller weeks. — [Aladin manual](https://docs.google.com/document/d/1mX-WxuoGs8Hy-QalhHcvuV17n50uGI2Sg_GHofgiePE/edit)
- **ItemLookUp params:** `ItemIdType` = ISBN | ISBN13 | ItemId, plus `offCode`. `OptResult` options:
  - ebookList, usedList, fileFormatList, c2binfo, packing, b2bSupply, subbarcode, cardReviewImgList, ratingInfo, bestSellerRank
  - Marked "추가 요청시 가능" (on request only): previewImgList, eventList, authors, reviewList, fulldescription, fulldescription2, Toc, Story, categoryIdList, mdrecommend, phraseList (max 3)

  Source: [Aladin manual](https://docs.google.com/document/d/1mX-WxuoGs8Hy-QalhHcvuV17n50uGI2Sg_GHofgiePE/edit)
- **Response fields (search/list/lookup):**
  - Header fields: `version`, `title`, `link`, `pubDate`, `totalResults`, `startIndex`, `itemsPerPage`, `query`, `searchCategoryId`, `searchCategoryName`
  - Per `item`: `title`, `link`, `author`, `pubDate`, `description`, `isbn`, `isbn13`, `priceSales`, `priceStandard`, `mallType`, `stockStatus` (empty when the book is in normal distribution), `mileage`, `cover`, `publisher`, `salesPoint`, `adult`, `fixedPrice`, `subbarcode`, `customerReviewRank` (0–10), `bestDuration`/`bestRank` (bestsellers only), `seriesInfo` (seriesId/seriesLink/seriesName)
  - `subInfo` lists: ebookList, usedList (aladinUsed/userUsed/spaceUsed with itemCount, minPrice, link), newBookList, paperBookList, fileFormatList

  Source: [Aladin manual](https://docs.google.com/document/d/1mX-WxuoGs8Hy-QalhHcvuV17n50uGI2Sg_GHofgiePE/edit)
- **ItemLookUp extras:** `fullDescription`, `fullDescription2` (publisher's description), `categoryIdList`, and these under `subInfo`:
  - Bibliographic: `subTitle`, `originalTitle`, `itemPage`, `subbarcode`, `taxFree`, `toc`, `story`
  - Ratings and rank: `ratingInfo` (ratingScore, ratingCount, commentReviewCount, myReviewCount), `bestSellerRank`
  - People: `authors` (authorId, authorName, authorType, authorTypeDesc, authorInfo, authorInfoLink)
  - Physical: `packing` (styleDesc such as 양장본, weight in g, sizeDepth/Height/Width in mm)
  - Commerce: `c2bsales`, `c2bsales_price`, `b2bSupply`
  - Editorial and reviews: `cardReviewImgList`, `eventList`, `reviewList`, `offStoreInfo`, `phraseList`, `mdRecommendList`
  - DVD and music fields

  Source: [Aladin manual](https://docs.google.com/document/d/1mX-WxuoGs8Hy-QalhHcvuV17n50uGI2Sg_GHofgiePE/edit)
- **Quota:** "OpenAPI는 1일 5,000회로 제한됩니다." The basic tier omits some data such as TOC and full descriptions. **Premium** allowed **100,000/day (max 10,000/hour)** plus TOC and description data, but required attribution, an Aladin-only buy link and a yearly compliance check. — [Aladin API 이용 안내](https://blog.aladin.co.kr/openapi/category/29154404)
- **Key issuance:** you registered the URL where the key would be used, after signing up for Aladin. The key was issued immediately, but issuance closed on 2026-09-04. — [Aladin API 이용 안내](https://blog.aladin.co.kr/openapi/category/29154404)
- **Category list:** an XLS file, [aladin_Category_CID_20200626.xls](http://image.aladin.co.kr/img/files/aladin_Category_CID_20200626.xls), and a Google Sheet last revised 2026-03-16. — [Aladin blog](https://blog.aladin.co.kr/openapi/category/29154404)

#### Kyobo, YES24, Interpark Book
- Searches turned up no official public developer API or developer center for Kyobo or YES24. The only related item was a 2025 blog post about publisher distribution contracts with the "4대 온라인 서점". — [damoang post](https://damoang.net/tutorial/16448); [search results](https://www.inews24.com/view/944341)
- Interpark Book turned into an open marketplace from October 2021, leaving direct book sales. That is evidence of decline, but not a dated shutdown of its API. — [Byline Network, 2021-09](https://byline.network/2021/09/9-99/)
- A legacy Ruby gem wrapped the "Interpark book API", with keys from an Interpark API console. It is evidence that the API once existed, not that it exists now. — [rubydoc interpark-book](https://rubydoc.info/gems/interpark-book)

#### Google Books / Open Library (supplementary)
- **Google Books:** a keyless call to `https://www.googleapis.com/books/v1/volumes?q=isbn:9788936434120` on 2026-10-22 returned HTTP 429. The message was "Quota exceeded … 'Queries per day'", with `quota_limit_value: "0"` for the default project. In practice, anonymous calls may be unusable now, so plan to use an API key from your own Google Cloud project. — direct API probe (this research; the endpoint was `https://www.googleapis.com/books/v1/volumes`)
- **Open Library:** `https://openlibrary.org/search.json?isbn=9788936434120` returns the work-level record for Han Kang's 채식주의자 / The Vegetarian. It merges about 26 ISBNs across 7 languages, with `language` containing `kor`. The Korean ISBN 9788936434120 is present, but publisher and title data mix editions. — [Open Library Search API](https://openlibrary.org/dev/docs/api/search) (direct probe)

### Inferences
- From late October 2026, **Kakao is the only no-cost commercial Korean book search API open to new developers.** Any system that relied on Naver or Aladin needs to migrate. Likely replacements are Kakao plus public sources: the National Library of Korea ISBN/Seoji API and the 도서관 정보나루 API, which other researchers are covering.
- Because Kakao has no "new releases" or "bestseller" listing endpoint, the Aladin ItemList feature (new and bestseller lists by CategoryId) has **no commercial replacement**.
- Kakao's `url` points to Daum book pages. Kakao has no category field, no page count, no TOC and no rating.

### Gaps
- I could not confirm whether NAVER API HUB offers any paid or partner book endpoint. Sources say book was excluded, but I did not read the HUB catalog directly.
- I found no primary source confirming the exact date Interpark's book API was discontinued.
- Whether Kyobo or YES24 offer partner-only APIs (affiliate or B2B feeds) is unconfirmed. No public documentation was found.
- Google Books daily quotas for keyed projects, and the exact text of the Google Books API Terms, were not extracted. My attempt to fetch developers.google.com/books/terms returned only footer text.

---

## Q2. What do the terms say about storing results in a DB, caching, redistribution, commercial use and attribution?

### Takeaway
All three Korean providers' terms prohibit copying or storing ("캐시 포함") results beyond the permitted scope. In plain terms, **none allows building a persistent DB from API results without separate approval.** Naver's terms are the most explicit: server caching up to 21 days for history only, 24 hours for personalization, plus bans on ads, AI training and resale. Kakao allows caching only to improve UX and requires it be kept fresh. Kakao staff say ad-supported free apps are fine, but resale and sales-connection uses are not. Aladin barred corporate bookselling and book-info businesses and required attribution and a link-back for public institutions and Premium.

### Cited Findings

#### Kakao (Kakao Developers 운영정책, effective 2026-04-20)
- Prohibited: caching data received from Kakao "앱에서 사용자 환경을 개선하기 위한 목적 외 다른 목적으로 … 캐시하거나 캐시 후 최신 데이터로 유지하지 않는 행위". In other words, caching is allowed only for UX and must be kept up to date. — [Kakao 운영정책](https://developers.kakao.com/terms/latest/ko/site-policies)
- Prohibited: using information obtained through the service "카카오의 사전 승낙 없이, 복사, 복제, 변경, 번역, 출판, 방송, 검색 엔진 또는 디렉터리에 입력" or giving it to others. — [Kakao 운영정책](https://developers.kakao.com/terms/latest/ko/site-policies)
- Exceeding the daily or monthly quota is prohibited except under paid service, and running multiple accounts or apps for the same service is prohibited. — [Kakao 운영정책](https://developers.kakao.com/terms/latest/ko/site-policies)
- Staff answer, 2026-10-15: free ad-supported apps are not specially restricted. Proxy servers that hide the REST key are allowed. "서비스를 판매, 거래, 재판매하거나 악용하는 행위" is restricted, and so is "소개된 콘텐츠의 재판매, 판매 연결". The reply did not answer the storage or attribution questions. — [DevTalk 152056](https://devtalk.kakao.com/t/api-ios/152056)

#### Naver (NAVER API 서비스 이용약관, revised 2026-10-07; book API already terminated)
- General 7.3③ prohibits copying or storing data "(캐시 행위 포함)" beyond the permitted scope. Its examples include "별도 데이터베이스로 관리하며 이용하는 행위" and storing data in ways that don't fit the API's purpose. 7.3④ bars ads alongside API results. 7.3⑤ bars using multiple client IDs to raise quota or extract data. 7.3⑥ bars re-providing the API to third parties. — [Naver terms](https://developers.naver.com/products/terms/)
- Search API special terms:
  - **2.1:** for displaying Naver search results only, with "네이버 검색결과임을 표시" per the BI guide.
  - **2.2:** display the data unmodified, with the original source shown and a link to it.
  - **2.3:** prohibits "데이터…를 복사, 저장 또는 캐싱하는 행위", giving or selling data to third parties, using it for AI input, training or evaluation, and showing ads or otherwise earning revenue on results pages.
  - **2.4:** temporary caching allowed: on device for 24h or until the next query, whichever is shorter; on server for history lookup up to **21 days**, and for personalization 24h.

  Source: [Naver terms](https://developers.naver.com/products/terms/)
- Art. 8: copyright in result data belongs to Naver or the original rights holder. Users get only a limited license. — [Naver terms](https://developers.naver.com/products/terms/)

#### Aladin (OpenAPI 이용약관, effective 2022-09-01, plus the 이용 안내)
- Clause 7.3③ prohibits using API data "무단으로 복제, 저장(캐시 행위 포함), 가공, 배포 등". Clause 7.3⑤ prohibits re-providing the API to third parties. Clause 7.2③ prohibits charging your users for API or DB access. Clause 6.3③ lets Aladin refuse a key if a for-profit company uses it without approval, or if an individual or non-profit uses it for profit. — [Aladin 이용약관](https://blog.aladin.co.kr/openapi/category/84629934)
- 이용 안내:
  - Individuals with non-commercial use: no conditions.
  - Public libraries and institutions: must show that Aladin is the source and link items to Aladin pages.
  - **Corporations running bookselling or book-info services cannot use it.** Individual developers or sole proprietors running small book services can, including ones monetized with AdMob or AdSense.
  - Premium attribution text: "도서 DB 제공 : 알라딘 인터넷서점(www.aladin.co.kr)", plus a "자세히보기/구매하기" button linking only to Aladin, with no other bookstore links.

  Source: [Aladin API 이용 안내](https://blog.aladin.co.kr/openapi/category/29154404)

### Inferences
- If the goal is a persistent bibliographic DB (as in the "seoji" project), none of the commercial APIs is a legitimate source of record. Kakao comes closest but still requires prior consent for copying into a DB. Storing only ISBN-keyed pointers or derived facts, and refreshing cover and price data live, is a lower-risk pattern. It is still not explicitly sanctioned. Public-sector sources (NL Korea) are the safer basis for persistence.
- Naver's 21-day server cache rule is moot for books now, but it shows how strict Korean portal terms have become, including the new AI-use ban.

### Gaps
- I found no Kakao Daum-search-specific attribution or BI requirement, such as a mandatory "Daum" logo. The staff reply left this unanswered.
- I did not find Google Books or Open Library terms text (Open Library data is generally CC0, but I did not verify that in this session).

---

## Q3. Which fields does each provide that public APIs lack, and can you bulk-enumerate data?

### Takeaway
Commercial APIs added **cover images, descriptions, list and sale prices, sales and stock status**, and (Aladin only) **sales rank, ratings, TOC, page count, dimensions, series, category and author IDs**. Bulk enumeration was only ever practical through Aladin ItemList (new releases and bestsellers by category, capped). Kakao offers no listing endpoint, only query-driven search capped at 2,500 results.

### Cited Findings
- Kakao has `thumbnail`, `contents`, `price`, `sale_price`, `status` and `translators`. It has no category, page count, rank or rating. Its `sort=latest` exists but needs a query. — [Kakao dev guide](https://developers.kakao.com/docs/ko/daum-search/dev-guide)
- Aladin:
  - Every call: `cover` (up to 200px), `salesPoint`, `customerReviewRank`, `bestRank`, `categoryId`/`categoryName`, `seriesInfo`, `priceStandard`/`priceSales`, `stockStatus`, `fixedPrice`, `adult`
  - Lookup extras: `itemPage`, `packing` dimensions and weight, `toc`, `story`, `authors` with IDs, `ratingInfo`, `subTitle`, `originalTitle`

  Source: [Aladin manual](https://docs.google.com/document/d/1mX-WxuoGs8Hy-QalhHcvuV17n50uGI2Sg_GHofgiePE/edit)
- Aladin enumeration: `ItemList` with `QueryType=ItemNewAll|ItemNewSpecial|Bestseller|ItemEditorChoice|BlogBest`, filterable by `CategoryId`, with past bestseller weeks via `Year/Month/Week`. The manual says max 50 per page and 200 total results. — [Aladin manual](https://docs.google.com/document/d/1mX-WxuoGs8Hy-QalhHcvuV17n50uGI2Sg_GHofgiePE/edit). The newer blog guide says ItemList "총 결과는 1,000개까지만 조회 가능". — [Aladin blog guide](https://blog.aladin.co.kr/openapi/category/29154404). **The sources conflict.** The blog is newer (category sheet revised 2026-03), but the point is moot after 2026-10-30.
- Naver's fields were `image`, `description` and `discount`. The listing cap was 1,000 for `start` plus 100 for `display`. — [Naver doc](https://developers.naver.com/docs/serviceapi/search/book/book.md) (discontinued)

### Inferences
- With Aladin and Naver gone, getting **sales rank, bestseller lists, TOC, page count and category for Korean books from a commercial API is no longer possible** for new projects. Bestsellers and loan-based popularity would have to come from public sources, such as 도서관 정보나루's popular-loan API, or from scraping, which carries its own ToS issues.
- Kakao "enumeration" amounts to many query sweeps (publisher names with `target=publisher`, `sort=latest`). That runs into the 30,000/day quota, the 2,500-per-query cap and the anti-DB terms.

### Gaps
- I could not verify whether Aladin will offer any paid or partner replacement after 2026-10-30. The notice mentions none.

---

## Q4. Real-world data-quality notes

### Takeaway
Expect HTML highlight tags, space-separated dual ISBNs, inconsistent types and volatile status strings. Aladin's richest fields were gated behind on-request or Premium approval.

### Cited Findings
- Naver's official sample shows `<b>` highlight tags inside `title` and `description` (e.g. "불곰의 <b>주식</b>투자 불패공식"). `isbn` holds two values separated by a space ("8960515523 9788960515529") even though the doc types it as Integer. `pubdate` is `YYYYMMDD`. `discount` is omitted for books with no price. — [Naver doc](https://developers.naver.com/docs/serviceapi/search/book/book.md)
- In Kakao, `isbn` can be ISBN10, ISBN13 or both, separated by a space. `status` values are subject to change and should not drive logic. `datetime` is ISO 8601. — [Kakao dev guide](https://developers.kakao.com/docs/ko/daum-search/dev-guide)
- A developer asked on DevTalk for the binding format (제본형태) to be added to book search responses, which suggests Kakao lacks format/edition data. — [DevTalk 133442](https://devtalk.kakao.com/t/topic/133442) (title only; not fetched)
- Aladin's `stockStatus` is an empty string for normally distributed items. `customerReviewRank` is on a 0–10 scale (1 point per half star). The manual says to prefer ISBN13 for lookups ("가급적 13자리 ISBN을 이용해주세요"). Many lookup extras are "추가 요청시 가능" (on request only). — [Aladin manual](https://docs.google.com/document/d/1mX-WxuoGs8Hy-QalhHcvuV17n50uGI2Sg_GHofgiePE/edit)
- Open Library merges translations under one work, so a Korean ISBN query returns mixed-language publisher and ISBN lists (26 ISBNs and 7 languages for 채식주의자). That makes it poor for Korean edition-level metadata. — [Open Library search](https://openlibrary.org/search.json?isbn=9788936434120) (direct probe)

### Inferences
- Any ingestion layer should strip HTML tags, split the ISBN string and validate ISBN13 checksums, then normalize dates (Naver `YYYYMMDD`, Kakao ISO 8601, Aladin `YYYY-MM-DD`).

### Gaps
- I did not systematically measure how often pubdate or ISBN13 is missing in Kakao results. No reliable blog statistics were found within the time budget.
