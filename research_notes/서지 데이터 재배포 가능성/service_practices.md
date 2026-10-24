# 책소개·목차·서평·표지 재게시 관행: 국내외 도서 정보 서비스 사례 (2026년 10월 기준)

Scope: how Korean and international book-information services source and republish blurbs (책소개), tables of contents (목차), reviews (서평) and cover images (표지), and on what legal footing. The aim is to inform whether a new public Korean book search website, API or MCP server may show these fields from the NLK Seoji API. Research was done 2026-10-24. Facts and inferences are kept separate. Where a fact comes from this repo's earlier research notes (`research_notes/한국 서지정보 API 조사/`) and was not re-fetched this session, it is marked "(earlier note)".

## 1. 국내 서비스는 책소개·목차·표지를 어디서 받아 어떤 조건으로 보여주나

### Takeaway
Every Korean service whose terms I could read treats covers and enrichment text as more restricted than bare bibliographic facts. 정보나루 limits cover URLs to on-screen display by non-profit services. Kakao forbids permanent storage. Naver's revised search-API terms forbid copying, storing, caching and monetisation. KPIPA forbids third-party provision and mixing with other data. Public-library OPACs mostly pull enrichment from 알라딘, 네이버 and 다음, not from a licensed vendor. I found no Korean service that states a licence letting others republish 책소개 or 표지 text or images.

### Cited Findings
**도서관 정보나루 (data4library.kr)**
- Every book-returning endpoint in the API manual carries this rule (earlier note): "bookImageURL 은 비영리 서비스의 화면 표시에 한하여 이용 가능하며, 영리적 목적의 이용과 복사저장재배포 및 AI 입력학습 등 그 밖의 활용을 금함" — [정보나루 API manual v20260620](https://www.data4library.kr/downloadApiManual)
- `srchDtlList` and `usageAnalysisList` also return a `description` (책소개) field (earlier note) — [정보나루 API manual](https://www.data4library.kr/downloadApiManual). The note records no description-specific restriction like the bookImageURL one. I could not reach the site's 이용약관 text this session; the footer link is a `javascript:void(0)` stub — [data4library.kr/openDataL](https://www.data4library.kr/openDataL)

**공공도서관 OPAC 보강콘텐츠 (2019 survey)**
- Researchers surveyed the OPACs of 125 public libraries holding 『전두환 회고록』 and 260 holding 『반일 종족주의』 (Sep–Oct 2019, found through 국가자료종합목록). Enrichment content such as 책소개 and 서평 came mostly from 알라딘 인터넷서점, 네이버 and 다음. It consisted only of publishers' one-sided promotional introductions and excerpts from the text. It was shown either as a link from the external-information field or as full or partial text inside the bibliographic record — [Journal of the Korean Library and Information Science Society, v.50 no.4 (abstract, via search snippet)](https://accesson.kr/liss/v.50/4/181/12792). The direct page fetch returned an "invalid access" error, so these details come from the search-engine abstract.
- A 2023 follow-up (주소현·이수상, PNU) compared US and Korean public-library catalog enrichment. It concluded that Korean libraries need a separate vendor to develop and supply an enrichment solution ("별도의 업체에서 보강콘텐츠 서비스 솔루션을 개발 후, 제공하는 방식이 필요하다"), and that enrichment should be built from public data such as 정보나루 — [KLISS v.54 no.4, 2023-12-30, DOI 10.16981/kliss.54.4.202312.255](https://accesson.kr/liss/v.54/4/255/34051). This implies no Syndetics-like licensed Korean vendor was in general use in 2023.

**카카오 (다음) 책 검색 API**
- A Kakao DevTalk responder ("woody.ho", 2026-08-20/21) said a commercial online bookstore may use the API, but "제공되는 정보는 영구 저장하여 이용하실 수는 없는데요", and "일정기간 메모리 등에 캐시하여 이용하실 수는 있지만". The responder confirmed: "영구적으로 저장하는 것은 정책상 금지" — [devtalk.kakao.com/t/api/151260](https://devtalk.kakao.com/t/api/151260)
- The same responder (2026-10-15) said a free ad-supported app is not otherwise restricted, but "서비스를 판매, 거래, 재판매하거나 악용하는 행위는 정책상 제한". Questions about attribution wording went unanswered — [devtalk.kakao.com/t/api-ios/152056](https://devtalk.kakao.com/t/api-ios/152056)
- The page does not say whether the responder is Kakao staff, though the replies are presented as official answers.

**네이버 검색 API (책 포함 여부 불명)**
- A blog summary dated 2026-09-16 says the following. The revised terms apply from 9월 7일 with the move to NAVER API HUB. Search APIs may be used only "애플리케이션에서 네이버 검색 결과를 그대로 보여주는 목적". AI training or summarisation, ads on result pages, and crawling are prohibited. New applications for "3개 검색 API" closed on 7월 31일, and existing users have a grace period to 2027-06-30 — [brunch.co.kr/@ainote/123](https://brunch.co.kr/@ainote/123)
- A search-result summary of a TokenPost article lists further prohibitions in the revised terms: copying, storing or caching data, third-party provision or sale, and monetisation. It also lists a requirement to cite the source and link to the original. I did not fetch this article — [tokenpost.kr/news/ai/403521](https://www.tokenpost.kr/news/ai/403521)
- NAVER API HUB is run by Naver and brokered by Naver Cloud Platform — [ncloud API HUB guide](https://guide.ncloud-docs.com/docs/apihub-use)
- Naver 책's own data sourcing: a mid-2000s Naver press release describes 150만권+ 서지정보 with 책소개, 저자소개 and 목차, plus price links to several online bookstores. It does not name the data source — [navercorp press release](https://navercorp.com/media/pressReleasesDetail?seq=27374). A search summary also mentions a mid-2000s Daum–교보문고 tie-up, in which 교보 had a 315만종 도서DB; I did not open that press release — [navercorp press release list](https://navercorp.com/media/pressReleasesDetail?seq=27583)

**알라딘 TTB Open API**
- The guide (last modified 2007-09-01) caps use at 5,000 calls a day, with more by request to ttb@aladin.co.kr. ItemLookUp returns `description`, `toc` (목차), a "Let's Look" preview image, and covers in sizes Big, Mid, Small and Mini. The guide sets no rule on cover or description reuse, storage or attribution, and points to a separate 이용약관 — [aladin.co.kr/ttb/apiguide.aspx](https://www.aladin.co.kr/ttb/apiguide.aspx)

**교보문고 (서점 측 출판사 등록 요건)**
- Publishers registering new titles must supply a cover JPG at least 500px wide and an objective 책소개 ("도서에 대한 객관적인 소개"; superlatives are deleted as advertising). Books without a table of contents must say so ("이 책은 목차가 없습니다"). Preview files go separately to image@kyobobook.com. The page states no licence that publishers grant 교보 — [kyobobook.co.kr/partners/book-register](https://www.kyobobook.co.kr/partners/book-register)

**국립중앙도서관 / 서지정보유통지원시스템**
- ISBN·CIP were run together from Feb 2019, issuing a CIP from an uploaded cover or title-page image. The CIP programme stopped in Dec 2020 — [nl.go.kr/seoji 연혁](https://www.nl.go.kr/seoji/contents/S20101020000.do)
- The Seoji API documents 책소개, 목차 and 서평 file URLs as "21년 2월까지 생성된 데이터 제공" (earlier note: `research_notes/한국 서지정보 API 조사/nlk_apis.md`). The earlier note found no NLK statement on rights to those fields.

### Inferences
- Korean practice is to show covers and blurbs on one's own screen, sourced live from a bookstore, portal or government API, under that provider's terms. There is no "open licence" layer for this content. The restrictions (no permanent storage, no redistribution, non-profit display only) come from API providers who are themselves downstream of publishers. This suggests none of them believes it holds rights it can sublicense.
- The OPAC findings suggest public libraries rely on bookstore and portal APIs rather than licensed enrichment DBs. Libraries therefore follow the same "display, don't redistribute" pattern, and Korea has no Syndetics-style vendor whose licence a new service could copy.
- The 2020 end of CIP and the "21년 2월까지" note on Seoji's 책소개/목차/서평 file URLs suggest the Seoji enrichment fields are a legacy of CIP- and ISBN-era publisher submissions. That is relevant to what purpose the publishers consented to. This is inference only.

### Gaps
- I found no source for where 서울도서관, KOLIS-NET/국가자료종합목록 or 국립중앙도서관 소장자료 검색 get their cover images and 책소개 today (Seoji, 알라딘 API, or a purchased DB). I also found no published contract for a library buying a bookstore cover DB.
- I could not get the text of the 정보나루 이용약관, the 알라딘 TTB 이용약관, or Naver's official book-API terms (only secondary summaries). Whether Naver's book search API is one of the "3개 검색 API" being shut down is unconfirmed.
- I found no public information on Korean book-cover image supply businesses (북커버 이미지 공급 업체).

## 2. 출판사–서점 관행과 계약상 근거: 보도자료·표지는 판매 촉진용으로 허락된 것인가

### Takeaway
The government standard publishing contract covers only the author-to-publisher link. In it the author lets the publisher use, and give third parties, information the author supplied, for production, advertising, promotion and sales (제28조②). Trade practice is that publishers supply 보도자료, covers and TOCs to bookstores so they can sell the book. I found no document that extends this permission to non-sales third parties such as a search site, and I found no Korean court decision on 책소개 or 표지 reuse.

### Cited Findings
- 출판권설정계약서 제28조② (출판 분야 표준계약서 해설, 2021-02, published by 한국출판문화산업진흥원, research team led by 김기태): "저작권자는 출판사가 이 계약에 의한 출판물의 제작 및 광고, 홍보, 판매 등을 위하여 저작권자가 제공한 정보를 스스로 이용하거나 제3자에게 제공하는 것을 허락한다. 다만, 저작자의 초상 이용에 대하여는 저작자와 출판사가 합의하여 결정한다." The commentary explains it as letting the publisher use author-supplied information in "판매 촉진 활동" — [출판 분야 표준계약서 해설 PDF (kawf.kr)](https://www.kawf.kr/files/publish_contract_guide_20210323.pdf)
- The same model contract makes the publisher bear "출판물의 제작, 홍보, 광고 및 판매에 필요한 비용" (제11조③) and decide "홍보․광고, 판매의 방법" (제13조②). It also waives royalties on copies supplied for "납본, 증정, 신간 안내, 서평, 홍보" (제15조③) — [same PDF](https://www.kawf.kr/files/publish_contract_guide_20210323.pdf)
- The 2021 MCST revision added purpose and definition clauses and a duty to explain the contract. It also confirmed that the 2차적저작물작성권 stays with the author — [etoday 2021](https://www.etoday.co.kr/news/view/1997592); [MCST press release](https://www.mcst.go.kr/site/s_notice/press/pressView.jsp?pSeq=14139)
- A publishing-trade book listing describes 보도자료 as sent to the press and registered with online bookstores at the same time, working as a digital asset that links readers' searches to the book — [『에디터를 위한 보도자료 실전 매뉴얼』 (YES24 listing)](https://m.yes24.com/goods/detail/152457279)
- Book metadata on the 출판유통통합전산망 is entered by publishers in ONIX 3.0 form and pushed to linked distributors and bookstores every 5 minutes (earlier note) — [KPIPA 메타데이터 서비스](https://bnk.kpipa.or.kr/home/v3/center/centerGuideServiceMetaData). An etoday report says publishers' standardised metadata "유통사와 서점에서 실시간으로 확인하고 이용할 수 있다" — [etoday](https://www.etoday.co.kr/news/view/2065490)
- **Database right risk.** 저작권법 제93조 gives a 데이터베이스제작자 the right to reproduce or transmit all or a substantial part of a DB. Individual items do not count as a substantial part, unless they are copied repeatedly or systematically in a way that conflicts with normal use. Courts have found infringement in systematic crawling of a job site (2021) and in Naver 부동산 listings (특허법원 2024나11433) — [search summary citing 한국저작권위원회 판례, patent.scourt.go.kr and others](https://patent.scourt.go.kr/dcboard/new/DcNewsViewAction.work?seqnum=28157&gubun=44&cbub_code=000700&searchWord=&pageIndex=1); [newspim 2024-05-19](https://www.newspim.com/news/view/20240519000179)
- **No Korean case on blurbs or covers.** Searches for Korean decisions on 책소개 or 표지 reuse found none. The nearest e-commerce case is an image-sharing claim between 쿠팡 sellers, which the court dismissed (대구지법 2019가소****). The defence argued that platform terms implied consent to sharing listing photos — [법무법인 법승 사례](https://www.lawwin.co.kr/cases/747)

### Inferences
- 제28조② is a personal-information and author-supplied-information clause (약력, photos and similar). It is not a grant over the publisher's own 책소개 text or cover design. 책소개 is usually written in-house, so the publisher (or a cover designer under contract) probably holds rights in it as a work made for hire (업무상저작물). The permission bookstores rely on is therefore implied by the publisher's own act of supplying the text for sales. It is not written in any standard contract I found.
- If that implied permission exists, its scope is probably "promoting and selling this book". A search or reference service that does not sell books, and that redistributes the data through an API or MCP, sits outside the clearest core of that purpose. A display that sends users to a place to buy or borrow the book is easier to defend than bulk redistribution.
- Copying Seoji's 책소개/목차 for the whole catalogue into one's own DB and API could raise the 저작권법 제93조 database-right question (NLK as DB maker) separately from copyright in each blurb. This is inference; no case on library or ISBN data exists.

### Gaps
- I found no Korean court decision or 한국저작권위원회 consultation on whether 책소개 or 보도자료 text is a protected 어문저작물, or on implied licence for publisher press materials.
- I did not find the text of the 출판유통통합전산망 general 이용약관 for publishers (별표2 data form), which may say how publishers' metadata may be used downstream.
- I found no bookstore–publisher supply contract terms (교보, 알라딘, 예스24) that define the licence over covers and blurbs.

## 3. KPIPA 출판유통통합전산망 Open API 약관: 책소개·표지 재사용 조건

### Takeaway
KPIPA's Open API (amended 2025-08-01, effective 2025-08-11) allows commercial use only within the purpose declared at application. It forbids copying the data or giving it to third parties without prior consent, requires display unmixed with other data, and requires source attribution. It is the closest Korean analogue to a publisher-consented metadata licence, and it is still restrictive.

### Cited Findings
- Scope (제2조③): "출판사가 ｢출판유통통합전산망 이용약관｣ 제2조 제5항 제1호 및 그 약관 별표2의 형식에 따라 직접 등록한 도서정보로, 그 중에서 Open API 서비스 제공에 동의한 출판사의 도서 정보에 한한다." The terms do not say whether 표지, 책소개 or 목차 are included — [KPIPA Open API 약관](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)
- Commercial use (제5조①): "이용자는 Open API 서비스를 통해 제공받은 자료를 상업적으로 이용할 수 있다. 다만 상업적인 목적으로 이용하고자 하는 경우에는 서비스 신청 시 제출한 활용 정보([별표 1]) 내에서만 활용이 가능하며…". Unauthorised commercial copying or distribution "저작권법에 의해 처벌될 수 있다". Commercial applications go to the 운영위원회 (제5조②) — [same](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)
- Prohibited (제8조③2): using the information for profit or not "제공기관의 사전 승낙 없이 … 복제, 출판, 방송 등에 사용하거나 제3자에게 제공하는 행위". 제8조③3 also prohibits infringing the IP of the provider or third parties — [same](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)
- Display and attribution (제8조⑤): "이용자는 Open API 서비스를 이용한 결과를 다른 정보와 혼합하지 않고 독립적으로 노출하여야 하며 통합전산망에서 제공된 정보임을 명확하게 표시하여야 한다." — [same](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)
- No warranty: "메타데이터(도서 정보)는 전산망에 등록된 내용을 그대로 제공하며" (제10조②), and the provider bears no representations or warranties about it (제10조④) — [same](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi)
- Coverage is limited to titles from 2021-09-29 on, from publishers that opted in (earlier note) — [KPIPA newsletter 2023-08-14](https://bnkkpipa.stibee.com/p/12). In 2022 only 17,057 of 74,654 new titles (22.85%) were registered — [search summary of a news report](https://www.khan.co.kr/reporter_article.html?id=144) (I did not fetch the article to confirm which outlet ran the figure)

### Inferences
- Even with explicit publisher opt-in, the government's own publishing body does not let API users pass the data on to third parties. A public API or MCP server built on KPIPA data would breach 제8조③2 without prior consent. By analogy, an NLK Seoji re-exposure layer is the kind of use public data providers in this sector tend to forbid, unless NLK's own terms clearly allow it. That question is for whoever is researching NLK's terms.
- The "독립적으로 노출" (no mixing) rule conflicts with an aggregator design that merges sources per ISBN.

### Gaps
- I could not see the API field list (whether 책소개, 목차 and cover URLs are delivered). It is in member-only documentation.

## 4. 해외 사례: Open Library, Google Books, ISBNdb, Wikidata, OCLC, LC, BnF, DNB, Syndetics, LibraryThing

### Takeaway
Open-licence bibliographic data internationally covers descriptive metadata. That includes BnF under Licence Ouverte, DNB under CC0, OCLC's recommended ODC-BY, and Wikidata under CC0. None of the licence statements I read extends that open licence to covers or publisher blurbs. Covers are shown either under commercial licences (Syndetics, displayed on the fly, not stored) or with a fair-use argument and request-driven takedown (Open Library, LibraryThing). Wikidata holds facts, not blurbs.

### Cited Findings
**Open Library / Internet Archive**
- "The covers API is intended for displaying covers on public facing websites and not for bulk download." The page asks users not to crawl it and to hotlink with "a src URL that points to covers.openlibrary.org". Lookups by IDs other than CoverID or OLID are limited to 100 requests per IP per 5 minutes, returning 403 when exceeded. "A courtesy link back to Open Library is appreciated." The page has no copyright statement for covers — [openlibrary.org/dev/docs/api/covers](https://openlibrary.org/dev/docs/api/covers)
- Licensing: the Internet Archive "does not assert any new copyright or other proprietary rights" over the database, and warns "There may be existing rights issues on some contributions and in some jurisdictions" (page last edited 2021-06-27) — [openlibrary.org/developers/licensing](https://openlibrary.org/developers/licensing)
- The developer docs say the APIs are for real-time, low-volume, human-facing lookup and not for use as a data backend for third-party services. Bulk access is through the monthly dumps — [openlibrary.org/developers/api](https://openlibrary.org/developers/api)
- Takedown: the Authors Guild tells authors to send DMCA notices to info@archive.org with the exact URL, a good-faith statement and a statement under penalty of perjury. It reports the Internet Archive "has been responsive to many, but not all requests" — [Authors Guild](https://authorsguild.org/news/update-open-library/)

**Google Books API**
- Terms last modified 2012-04-25. They bar charging users for the application without a separate agreement. On request from Google, the developer must remove from the site or application any content provided through the Books API, and must provide contact information rights holders can use. The page says nothing on caching or on whether descriptions and covers are licensed from publishers — [developers.google.com/books/terms](https://developers.google.com/books/terms)
- LibraryThing's 2008 reading of the earlier Google Book Search terms found clauses against caching and reordering results, and a statement that the API is "not intended to be a substitute" for third-party content providers. This is secondhand and old — [LibraryThing blog 2008-06-06](https://blog.librarything.com/2008/06/covers-from-google-too-good-to-be-true/)
- Partner Program: publishers decide how much preview is shown. A 2008 Google guide gives 20%–100% — [GBS for Authors PDF](https://books.google.com.kw/intl/ar/googlebooks/pdf/GBS_for_Authors.pdf); [About Google Books](https://books.google.com/intl/en_uk/googlebooks/facts.html)

**LibraryThing covers (2008; APIs later suspended)**
- "Under U.S. law showing covers to show off books for sale, rental or commentary falls under Fair Use in most circumstances," with the disclaimer "We are not lawyers". Conditions were a developer key, about 1,000 covers a day, at most 1 per second, and no making covers available to others in bulk. Caching was allowed, and link-back was optional. A 2020 staff comment says all developer keys and APIs were suspended because of abuse — [LibraryThing blog 2008-08-07](https://blog.librarything.com/2008/08/a-million-free-covers-from-librarything/)

**Syndetics (ProQuest) – licensed enrichment for library catalogs**
- In 2000, Syndetic Solutions "established relationships with publishers, book wholesalers, and review sources" to gather TOCs, summaries, reviews, first chapters and covers. It distributed them commercially to libraries and system vendors — [Calcagno, LC Bibliographic Control conference, 2000](https://www.loc.gov/catdir/bibcontrol/calcagno_paper.html)
- Duke University Libraries: Syndetics enrichment is paid for by subscription and matched by ISBN. "These data are not stored in our back end datasets but are displayed on the fly." — [Duke DTSP wiki](https://duke.atlassian.net/wiki/spaces/DTSP/pages/59409354/Syndetics+Unbound)
- ProQuest reports about 64 million covers and over 43 million summaries; older pages give lower figures — [ProQuest Syndetics LibGuide](https://proquest.libguides.com/syndetics/uniquefeatures)

**OCLC WorldCat**
- In 2012 OCLC recommended ODC-BY for member libraries releasing WorldCat-derived catalog data, with attribution and adherence to "community norms". It objected to CC0 and PDDL for substantial WorldCat-derived data — [Library Technology Guides press release](https://librarytechnology.org/pr/17111); [Creative Commons 2012](https://creativecommons.org/2012/08/14/library-catalog-metadata-open-licensing-or-public-domain/)
- The WorldCat Rights and Responsibilities policy (approved 2010-06-14, effective 2010-08-01) defines "WorldCat data" as metadata, generally MARC records. It asks members to "make reasonable efforts to attribute the OCLC cooperative" (3B.4) and to ensure their contributions do not violate third-party rights (3B.3). It does not address TOCs, summaries or covers — [OCLC policy](https://www.oclc.org/en/worldcat/cooperative-quality/policy.html)

**Library of Congress**
- In 2017 LC released 25 million MARC records (1968–2014) for free bulk download. They were previously available only individually or by paid subscription — [LC press release 2017](https://loc.gov/item/prn-17-068); [2021 release](https://www.loc.gov/item/prn-21-047/library-of-congress-releases-data-for-free-download-and-discovery/2021-09-01/)
- The distribution page says only that the sets are "made available primarily for research and development usage". It gives no explicit licence and does not mention 505 (TOC) or 520 (summary) fields — [loc.gov/cds/products/marcDist.php](https://www.loc.gov/cds/products/marcDist.php)

**BnF**
- Since 2014-01-01 the BnF has placed its "métadonnées descriptives (données bibliographiques et d'autorité)" under the Licence Ouverte. Use is free, commercial use included, provided the source and retrieval date are kept — [BnF conditions de réutilisation](https://www.bnf.fr/fr/conditions-de-reutilisations-des-donnees-de-la-bnf); [data.bnf.fr à propos](https://data.bnf.fr/fr/about). The page does not address covers, résumés or back-cover text.

**DNB**
- Nearly all DNB metadata was under CC0 by 2014, with full release under CC0 via SRU and OAI from 2015-07-01 — [OpenGLAM 2014](https://openglam.org/?p=2558); [Koha-de list 2015](https://lists.koha-community.org/archives/list/koha-de@lists.koha-community.org/thread/7WN4EMMQTK2RQ4RGDLXDK3WP5JC6HXCL/). For some items DDB records note that only the 목차 (Inhaltsverzeichnis) is digitised and freely accessible — [DDB item example](https://www.deutsche-digitale-bibliothek.de/item/3MMYTJJVZX3GPLKG3CRCPJOUILR5DMHL)

**Wikidata**
- "All structured data in the main, property and lexeme namespaces is made available under the Creative Commons CC0 License". Wikidata avoids hosting data that cannot be under CC0 — [Wikidata:Licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)
- The CC0 book-data project Inventaire publishes under CC0 so Wikidata can import it — [Inventaire Entities data](https://wiki.inventaire.io/wiki/Entities_data)

**ISBNdb**
- The service offers about 19 data points per book, including a cover and synopsis, on a subscription basis — [Wikipedia: ISBNdb](https://www.wikipedia.org/wiki/ISBNdb.com). I could not retrieve ISBNdb's own terms on redistribution.

### Inferences
- The international split is consistent. Factual and descriptive metadata is open (CC0, ODC-BY, Licence Ouverte). Covers, summaries and TOCs are either licensed commercially and displayed without being stored (Syndetics), shown as on-screen display only with takedown (Open Library), or left out of open datasets (Wikidata holds no blurbs). The national libraries' open licences explicitly cover only "descriptive metadata". The licence text does not settle whether a publisher-written summary or TOC field inside the record is covered.
- Google's "remove content on request" clause and Open Library's DMCA route show that large services rely on fast removal, rather than upfront licences, for third-party content they cannot clear.

### Gaps
- I did not verify whether DNB and BnF dumps actually include publisher blurbs or abstracts, or whether DNB's TOC scans are within the CC0 grant.
- I did not find current Google Books Partner Program contract terms on metadata licensing.
- I did not find ISBNdb's or Open Library's description-specific copyright policy.

## 5. 실무 패턴과 위험 완화: 사실만 표시 + 링크, 짧은 발췌, 표지 핫링크 vs 캐시, 게시중단 절차

### Takeaway
The common low-risk patterns are these. Show factual metadata freely. Hotlink or proxy-display covers from the source and don't re-host or bulk-distribute them, which is what Open Library and Syndetics do. Limit stored copies of covers and blurbs to temporary caching, which matches Kakao's rule. Link out to the full 책소개. Run a published notice-and-takedown channel, which under 저작권법 제103조⑤ gives an online service provider a liability exemption once it complies.

### Cited Findings
- 저작권법 제103조 (복제·전송의 중단):
  - ① A rights holder may, "그 사실을 소명하여", ask an OSP to stop copying or transmission.
  - ② The OSP must "즉시 그 저작물등의 복제·전송을 중단시키고 권리주장자에게 그 사실을 통보하여야 한다".
  - ③ An uploader may request resumption.
  - ④ The OSP must designate and publicly post a recipient for these requests.
  - ⑤ If it has posted the recipient and acted under ② or ③, it is exempt from liability for the infringement. The exemption does not cover the period between learning of the infringement and receiving the request.
  - ⑥ False claimants are liable for damages.
  - [casenote.kr 저작권법 제103조](https://casenote.kr/법령/저작권법/제103조). A case summary on the same page cites 제102조③ as imposing no general duty to monitor.
- Display-only and no permanent storage is the norm in Korea. Kakao allows temporary caching but not permanent storage — [Kakao DevTalk](https://devtalk.kakao.com/t/api/151260). 정보나루 allows "비영리 서비스의 화면 표시" only and bans "복사저장재배포 및 AI 입력학습" of cover URLs (earlier note) — [정보나루 manual](https://www.data4library.kr/downloadApiManual). Naver's revised terms are reported to ban storing, caching and third-party provision — [tokenpost (search summary)](https://www.tokenpost.kr/news/ai/403521)
- Hotlinking: Open Library asks sites to point `<img src>` at covers.openlibrary.org and not to bulk-download — [Open Library Covers API](https://openlibrary.org/dev/docs/api/covers). Syndetics content is "displayed on the fly" and not stored — [Duke](https://duke.atlassian.net/wiki/spaces/DTSP/pages/59409354/Syndetics+Unbound)
- LibraryThing allowed caching but banned "bulk" re-provision of covers to others — [LibraryThing 2008](https://blog.librarything.com/2008/08/a-million-free-covers-from-librarything/)
- Attribution and link-back: Open Library requests a courtesy link — [Open Library](https://openlibrary.org/dev/docs/api/covers). KPIPA requires clear source labelling — [KPIPA 제8조⑤](https://bnk.kpipa.or.kr/home/v3/center/centerGuideOpenApi). BnF requires source and date — [BnF](https://www.bnf.fr/fr/conditions-de-reutilisations-des-donnees-de-la-bnf)
- Short excerpts: one blog post on Korean quotation rules summarises Supreme Court reasoning as weighing purpose, nature, amount, method, ordinary reader perception and market substitution. This is a secondary, non-authoritative source — [brunch @jiwoowriter](https://brunch.co.kr/@jiwoowriter/346). 저작권법 제28조 (공표된 저작물의 인용) and 제35조의5 (공정이용) are the statutory bases; I did not fetch their text this session.

### Inferences
- These patterns sort a Seoji-based public service's options by risk:
  - **Lowest:** show title, author, publisher, date, ISBN, KDC and price facts. Link to the NLK, bookstore or library page for 책소개, 목차 and 서평.
  - **Low to moderate:** show covers by hotlinking Seoji's TITLE_URL on a non-commercial site, with attribution, temporary caching only, and a takedown contact.
  - **Moderate:** show a short 책소개 excerpt, or the 목차, on the detail page with a source note and a link to the full text.
  - **Highest:** re-serve full 책소개, 서평 and cover files through a public API or MCP server, or in bulk dumps. That is the exact use that Kakao, 정보나루, KPIPA, Naver, Open Library and LibraryThing all exclude.
- Of the four fields, 목차 is probably the least creative: it is a factual list of chapter titles, though chapter titles themselves can be creative. Covers (artwork and design) and 서평 (likely third-party critics' or newspapers' text) are probably the most protected. This is a legal judgement that needs counsel; no Korean source above settles it.
- An MCP server that hands blurbs to LLM clients falls into the "AI 입력·학습" uses that 정보나루 (for covers) and Naver ban explicitly. That is a trend signal for how Korean providers treat AI reuse in 2026.
- The 제103조 exemption works only for an OSP hosting others' content, and only once a designated recipient is published. Whether a service that itself copies Seoji data counts as an "온라인서비스제공자" for that content, rather than the direct copier, is uncertain. Takedown therefore reduces risk but may not remove it.

### Gaps
- I did not fetch the text of 저작권법 제102조, 제28조 or 제35조의5, or any Korean case applying them to cover thumbnails (cf. US thumbnail cases such as Kelly v. Arriba, which I did not research).
- I found no Korean service that publishes a 게시중단 contact specifically for book covers or blurbs to use as a template.
