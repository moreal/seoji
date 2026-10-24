# NLK (국립중앙도서관) terms and licenses for redistributing Seoji Open API and 국가서지 LOD data (as of 2026-10)

> Research date: 2026-10-24. Most pages were fetched directly with curl or WebFetch, and the Korean quotes are verbatim from those fetches. The LOD SPARQL endpoint was queried directly (it needs no key). Pages behind a login (the NLK Open API 인증키 신청 form) and pages reached only by submitting a form (step 2 of Seoji publisher account registration) were not read. The downloadable ISBN 통보서 .hwp forms were not downloaded. **This is not legal advice.** Lines marked "Inference" are this researcher's reading, not NLK statements.

## Q1. Does the Seoji service have its own 이용약관, Open API 이용약관 or 저작권 정책? What do publishers agree to when they submit 책소개, 목차 and 표지?

### Takeaway
I found no Seoji-specific 이용약관, Open API 약관 or 저작권정책.
- The Seoji site (now branded "ISBN·ISSN·UCI·납본 시스템") links only to NLK's 개인정보처리방침 in its footer, and it carries "All Rights Reserved".
- The Seoji API guide states no license and no reuse terms for any field.
- I could not find any public text of what publishers agree to about redistribution of 책소개, 목차 or 표지. The only clue is a response field, `BIB_YN` "서지유통여부", which suggests a per-record distribution flag. Its meaning is undocumented.

### Cited Findings
- **The site has been rebranded.** The Seoji home page title and logo read "ISBN·ISSN·UCI·납본 시스템", not "서지정보 유통지원시스템". — [nl.go.kr/seoji](https://www.nl.go.kr/seoji/)
- **The footer has no terms or copyright page.** It contains only "개인정보처리방침" (linking to `nl.go.kr/NL/contents/N70101000000.do`), "문의처" and "오시는길". It ends "Copyright(c) 2021 by National Library of Korea All Rights Reserved." The site menu (서비스안내, ISBN, ISSN, UCI, 납본, 계정관리, 회원, 통합검색) has no 이용약관, 저작권정책 or Open API page. — [nl.go.kr/seoji](https://www.nl.go.kr/seoji/); [계정등록 page](https://www.nl.go.kr/seoji/contents/S70300000000.do)
- **Publisher account registration (계정등록), step 1, is a duplicate check (발행처 중복검사)**, with the note "증빙자료(출판사신고확인증 또는 사업자등록증, 고유번호증)의 기관명이 계정의 발행처명과 다르면 발행자 번호가 부여되지 않습니다." Any terms shown at the next step were not visible without submitting the form. — [Seoji 계정등록](https://www.nl.go.kr/seoji/contents/S70300000000.do)
- **The ISBN 신청 안내 page mentions only one consent:** "메일 및 카카오톡 알림서비스 수신 여부에 동의 필요". Nothing there concerns data distribution or licensing of submitted content. — [ISBN 신청 안내](https://www.nl.go.kr/seoji/contents/S30201000000.do)
- **The ISBN 통보서 forms exist as .hwp downloads** (개별도서, 세트, 다품목묶음세트). They were not downloaded, so their consent wording, if any, is unknown. — [Seoji main page links](https://www.nl.go.kr/seoji/) (e.g. `/seoji/resource/form/user/new_ea_isbn.hwp`)
- **The Seoji API guide has no license wording.** It lists TITLE_URL "표지이미지 URL" and the file URLs "목차 파일 URL / 책소개 파일 URL / 서평 파일 URL (21년 2월까지 생성된 데이터 제공)". It also lists the inline fields 목차, 책소개 and 서평, and `BIB_YN` "서지유통여부". Its only caveat is "※ 제공서비스에 따라 출력결과 필드는 제한될 수 있습니다." It contains no 공공누리 type, no 출처표시 rule and no commercial-use rule. The only KOGL element is the generic site-wide footer badge ("open 공공누리|공공저작물 자유이용허락"), which names no type. — [NLK Open API 활용방법: ISBN 서지정보](https://www.nl.go.kr/NL/contents/N31101030500.do)
- **The site FAQ has nothing on reuse.** The "사이트관련" FAQ contains only "크롬 브라우저 사용 안내입니다." The ISBN FAQ titles cover 판권지, 판유형, 비매품 and the like; none is about reuse or redistribution. — [사이트관련 FAQ](https://www.nl.go.kr/seoji/contents/S20304000000.do); [ISBN FAQ](https://www.nl.go.kr/seoji/contents/S20301000000.do)
- **The retired CIP API's fields** included `cover_yn, thumb_path, title_page_yn, copyright_page_yn, preface_yn, contents_yn, abstract_yn` (from the previous research note). This indicates that publishers historically submitted cover, title-page, copyright-page, preface, contents and abstract files for CIP. — [NLK 출판예정도서 guide](https://www.nl.go.kr/NL/contents/N31101030800.do)

### Inferences
- **The Seoji cover path suggests publisher uploads.** The TITLE_URL host path `nl.go.kr/seoji/fu/ecip/dbfiles/...` ("ecip") fits files that publishers uploaded during (e-)CIP/ISBN application. If so, covers and 책소개 are publisher-authored works (or their designers' and authors'). NLK does not own them.
- **`BIB_YN` (서지유통여부) may record publisher opt-in.** It suggests a per-record flag for whether the publisher allowed the record to be "distributed". This would be the strongest evidence of a publisher distribution consent, but its semantics and the underlying consent text are undocumented publicly.
- **No public instrument grants third parties rights to the content.** Without a published publisher-consent text, I found no public document by which publishers license NLK to sublicense 책소개, 목차 or 표지 to third-party sites, APIs or AI tools.

### Gaps
- I could not read the publisher-side consent, if any, at account step 2 or in the ISBN 통보서 .hwp forms. The forms are downloadable files, which this researcher did not download. Recommended follow-up: download `new_ea_isbn.hwp` with the user's permission and look for "서지정보 유통" or "제3자 제공" wording, or ask 한국서지표준센터 (02-590-0700, isbn@korea.kr).
- The meaning of `BIB_YN` "서지유통여부" (what Y and N govern) is undocumented.
- Whether 출판유통통합전산망 (KPIPA) terms, which feed Seoji since 2024, contain a content license was not researched. It is a KPIPA document.

## Q2. NLK 저작권정책 and the scope of 공공누리: which type applies to Open API data, and are third-party works excluded?

### Takeaway
- **NLK's 저작권정책 limits free reuse to works whose 저작재산권 NLK wholly owns, and only where a 공공누리 mark is attached.** Material without a 공공누리 mark needs prior consultation ("사전에 협의").
- **The Seoji API page carries no 공공누리 type.** On this policy's own terms, its data therefore falls in the "consult first" bucket.
- **The policy does not name third-party works explicitly.** Its structure (NLK-owned → KOGL 1; others only with the rights holder's consent) excludes them by implication.

### Cited Findings
- "국립중앙도서관(홈페이지)에서 제공하는 자료 중에서 국립중앙도서관이 저작재산권의 전부를 보유한 저작물의 경우에는 저작권법 제24조의 2(공공저작물의 자유이용)에 따라 별도의 이용 허락 없이 자유이용이 가능합니다." — [NLK 저작권정책](https://www.nl.go.kr/NL/contents/N70600000000.do)
- "단, 위 규정에 따라 자유이용이 가능한 자료는 "공공저작물 자유이용허락표시기준(공공누리, KOGL) 제1유형"을 부착하여 개방하고 있으므로 공공누리 표시가 부착된 저작물인지를 확인한 이후에 자유롭게 이용하시기 바랍니다." — [NLK 저작권정책](https://www.nl.go.kr/NL/contents/N70600000000.do)
- "그 밖에도 권리자의 동의가 있는 경우를 비롯하여, 널리 자유이용을 허락하는 것이 바람직한 자료들은 공공누리 표시를 부착하여 개방하고 있습니다. … 모든 출처표시 유형은 출처(해당 공공기관명과 누리집(홈페이지) URL, 저작물 작성자의 성명이 표시된 경우에는 그 성명도 포함)는 반드시 표시하여야 함을 유의하시기 바랍니다." — [NLK 저작권정책](https://www.nl.go.kr/NL/contents/N70600000000.do)
- "공공누리가 부착되지 않은 자료들을 이용하고자 할 경우에는 공공저작물 관리책임관 및 담당자와 사전에 협의한 이후에 이용하여 주시기 바랍니다." — [NLK 저작권정책](https://www.nl.go.kr/NL/contents/N70600000000.do)
- **Contacts named on the policy page:** 공공저작물 관리책임관 디지털정보기획과 이현주 02-590-0560; 공공저작물 관리담당자 디지털정보기획과 김태경 **02-590-0548**. The 담당자 number is the same one the Seoji API guide gives for the API (디지털정보기획과 02-590-0548). — [NLK 저작권정책](https://www.nl.go.kr/NL/contents/N70600000000.do); [Seoji API guide](https://www.nl.go.kr/NL/contents/N31101030500.do)
- **The AI유형 is defined on the same page.** Its conditions include "3. 공공저작물을 학습한 인공지능 모델의 상업적 이용은 가능하나 공공저작물을 이용해 제작한 인공지능 학습용 데이터의 재판매는 금지". Nothing ties the AI유형 to Seoji data. — [NLK 저작권정책](https://www.nl.go.kr/NL/contents/N70600000000.do)
- **NLK attaches 공공누리 1유형 to specific outputs explicitly.**
  - Press releases: "국립중앙도서관의 보도자료 저작물은 "공공누리 1유형(출처표시)" 조건에 따라 누구나 이용할 수 있습니다." — [NLK 보도자료 2024-09-23](https://www.nl.go.kr/NL/contents/N50603000000.do?schM=view&id=49248&schBcid=normal0302)
  - The 사서추천도서 API is marked 제1유형 on data.go.kr (previous research note). — [data.go.kr 15064371](https://www.data.go.kr/data/15064371/openapi.do)

### Inferences
- **Seoji API output appears to fall in the "사전에 협의" bucket.** No 공공누리 type is attached to it anywhere I found.
- **(a) Factual fields** (title, author, ISBN, price, pages, KDC, 부가기호, dates) are probably not 저작물 at all. A bare fact is not a "창작물", so the copyright policy arguably does not reach them. Contract terms (Q3) and possible 데이터베이스제작자 rights (Q7) remain.
- **(b) and (c), 책소개, 서평 and 표지,** are works that NLK does not wholly own. They fall outside 제24조의2 free use and outside any KOGL grant.

### Gaps
- No NLK page states the 공공누리 type, or "적용 제외", for the Seoji API specifically.

## Q3. NLK Open API terms (accepted when applying for an 인증키): commercial use, redistribution, attribution, prohibited acts

### Takeaway
- **There is no separate "Open API 이용약관" that I could find.** The key application page is login-gated, and the Open API 이용안내 page describes only the procedure: 회원가입 → 인증키 신청 → 담당자 승인.
- **The terms that do bind key holders are the NLK 통합회원 이용약관** (effective 2019-09-16), because NLK membership is mandatory for a key. These general terms contain broad clauses:
  - No 영리행위 without NLK's prior approval.
  - No reproduction of information obtained through the service, or provision of it to others, without NLK's prior approval.
  - Read literally, they cut against public republication or commercial use of API output. They are generic site terms, however, and sit uneasily with the API's stated mash-up purpose and the data.go.kr "제한 없음" label.

### Cited Findings
- **Open API procedure:** "1. 회원가입 Open API를 활용 하려면 국립중앙도서관 회원이어야 합니다. 2. 인증키 발급 신청 … 3. 담당자 승인 발급된 인증키를 활용하기 위해서는 담당자 승인이 필요합니다." — [NLK Open API 이용안내](https://www.nl.go.kr/NL/contents/N31101010000.do)
- **Purpose of the Open API:** "개발자가 국립중앙도서관 소장자료, 국가자료종합목록 등을 활용하여 다양한 애플리케이션을 보다 쉽게 개발할 수 있도록 기술과 서비스를 제공하는 인터페이스", "XML 프로토콜을 적용하여 다양한 매쉬업 서비스 개발이 용이함". — [NLK Open API 이용안내](https://www.nl.go.kr/NL/contents/N31101010000.do)
- **The key application page needs a login.** Without one it returns a JS prompt, "로그인이 필요한 서비스입니다", so any key-specific terms there could not be read. — [N31101020000](https://www.nl.go.kr/NL/contents/N31101020000.do)
- **NLK's site-policy footer has no 이용약관 page.** It lists 개인정보처리방침, 윤리강령, 도서관법령, 이용봉사헌장, 저작권정책 and so on. — [NLK 저작권정책 page footer](https://www.nl.go.kr/NL/contents/N70600000000.do)
- **Clauses of the 통합회원 이용약관** (shown at 회원가입, "본 약관은 2019년 9월 16일부터 적용됩니다"; all from [NLK 회원가입 / 통합회원 이용약관](https://www.nl.go.kr/NL/contents/N60300000000.do)):
  - 제1조: "본 약관은 국립중앙도서관 … 사이트가 제공하는 서비스 … 및 자료의 이용 조건 및 절차 … 를 규정함을 목적으로 합니다."
  - 제4조①: "도서관은 필요한 경우 개별 서비스에 대하여 약관 및 이용 규정(이하 '서비스별 안내')을 정할 수 있으며, 본 약관과 서로 상충되는 경우에는 서비스별 안내의 내용을 우선하여 적용합니다."
  - 제10조②: "… 회원이 이러한 특정 서비스를 이용할 경우 해당 사이트 또는 서비스의 이용 약관, 규정 또는 세칙 등이 본 약관보다 우선 적용됩니다."
  - 제14조①: "서비스에 대한 저작권 및 지적재산권은 도서관에 귀속됩니다."
  - 제15조① 5호 (grounds for 이용제한/해지): "서비스를 통해 얻은 정보를 도서관의 사전 승낙 없이 서비스 이용 외의 목적으로 복제하거나, 이를 출판 및 방송 등에 사용하거나, 제 3자에게 제공하는 행위"
  - 제17조④: "회원은 도서관의 사전 승낙 없이 서비스를 이용하여 어떠한 영리행위도 할 수 없으며, … 영리행위로 도서관이 손해를 입은 경우, 회원은 도서관에 대해 손해배상 의무를 지며 …"
  - 제17조⑥: "회원은 도서관 서비스를 이용하여 얻은 정보를 도서관의 사전승낙 없이 복사, 복제, 변경, 번역, 출판·방송 기타의 방법으로 사용하거나 이를 타인에게 제공할 수 없습니다."
  - 제17조⑦ 5호: "타인의 지적재산권 등의 권리를 침해하는 행위" is prohibited.
  - 제19조④: "도서관은 … 서비스를 이용하면서 얻은 자료로 인한 손해에 대하여 책임을 지지 않습니다."

### Inferences
- **The 통합회원 이용약관 are the only NLK contract terms I could find that a Seoji API key holder has accepted.** Read literally, 제15조①5 and 제17조④⑥ require NLK's "사전 승낙" for:
  - commercial activity using the service;
  - copying API output for uses beyond the service;
  - providing API output to third parties.
  Public websites, public REST APIs and MCP servers all do the last of these.
- **Counter-arguments (uncertain):**
  1. The terms are generic membership boilerplate written for the website and its 게시판, not for an API whose stated purpose is building "매쉬업 서비스".
  2. 제4조① and 제10조② let service-specific terms prevail, but none exist for the Open API.
  3. NLK lists the same API on data.go.kr as "이용허락범위 제한 없음" (Q4), and the Seoji system's stated purpose is "정확한 도서정보의 유통" (Q6). Both suggest NLK intends downstream reuse.
  4. 공공데이터법 policy disfavors restricting public data.
- **Net effect:** the contractual position for commercial or public redistribution of Seoji output is ambiguous. The cautious course is written confirmation from 디지털정보기획과 (02-590-0548).
- **Attribution:** no Seoji-specific attribution rule exists. NLK's KOGL attribution template (Q2) is the natural model, e.g. "출처: 국립중앙도서관 ISBN 서지정보 Open API (https://www.nl.go.kr/seoji/)".

### Gaps
- I could not see any terms shown inside the logged-in 인증키 신청 form, such as a 이용목적 field or a checkbox.
- I found no NLK statement interpreting the 통합회원 이용약관 as applying to Open API output.

## Q4. The data.go.kr mirror of the Seoji API: 이용허락범위, 공공누리 type, cost

### Takeaway
- **The data.go.kr listing "문화체육관광부_국립중앙도서관_ISBN서지정보" (3078982)** reads: 무료, 실시간, **"이용허락범위 제한 없음"**, 개발/운영 자동승인, and no 공공누리 type.
- **It is a LINK-type entry.** Calls go to NLK's endpoint with an NLK key.
- **data.go.kr's own policy says data containing third-party copyright requires the rights holder's license and a KOGL mark.** The listing's "제한 없음" therefore does not by itself clear 책소개 or 표지.

### Cited Findings
- **Listing metadata:**
  - 제공기관: 문화체육관광부 국립중앙도서관; 관리부서: 디지털정보기획과
  - API 유형: LINK; 데이터 포맷: XML
  - 등록일: 2020-04-01; 수정일: 2025-07-16; 활용신청 수: 2061
  - "비용부과유무 무료"; "업데이트 주기 실시간"; "이용허락범위 제한 없음"
  - "심의유형 개발단계 : 자동승인 / 운영단계 : 자동승인"
  - "신청 가능 트래픽: 해당 기관의 정책에 따라 트래픽 수는 상이 할 수 있음"
  - — [data.go.kr 3078982](https://www.data.go.kr/data/3078982/openapi.do)
- **The listing description, verbatim:** "국내에서 ISBN을 발급받은 출판 자료뿐만 아니라, 출판이 예정된 자료에 대해서도 관련 정보를 확인할 수 있습니다. 국립중앙도서관 산하의 한국서지표준센터에서 제공하며, 출판사가 해당 센터에 통보한 내용을 바탕으로 구성됩니다. 제공되는 정보에는 ISBN을 포함하여 도서의 서명(제목), 저자, 판 사항, 형태사항(페이지 수, 크기 등), 가격사항, 발행 예정일, 키워드, 본문 언어 등의 주요 서지정보가 포함됩니다. … 도서관, 서점, 학계 등 다양한 분야에서의 자료 검색과 출판 유통, 학술 활용에도 도움을 줄 수 있습니다." It lists factual fields only and does not mention 책소개, 목차, 서평 or 표지. — [data.go.kr 3078982](https://www.data.go.kr/data/3078982/openapi.do)
- **The listing's embedded schema.org/DCAT metadata** sets `"license" : "https://data.go.kr/ugs/selectPortalPolicyView.do"`, which is the portal's generic policy page. — [data.go.kr 3078982](https://www.data.go.kr/data/3078982/openapi.do) (page source)
- **data.go.kr 공공데이터 이용허락범위 policy:** "저작권 등 제3자 권리가 포함된 공공데이터는 권리자의 정당한 이용허락을 확보해야 합니다. 저작물이 포함된 공공데이터를 제공하는 경우에는 저작권법 등 관련 법령에 따른 공공누리 유형을 부착하도록 합니다." — [data.go.kr 정책](https://www.data.go.kr/ugs/selectPortalPolicyView.do)
- **공공데이터 관리지침 제8조①**, quoted on the same page: "공공기관의 장은 저작물이 포함된 공공데이터를 관리하는 경우 제3자의 권리가 침해되지 않도록 권리 소재 및 권리자의 이용허락 범위를 명확히 파악해야 한다. 이 경우 권리자의 이용허락은 서면 등 명시적으로 의사를 확인할 수 있는 방법으로 받아야 한다." — [data.go.kr 정책](https://www.data.go.kr/ugs/selectPortalPolicyView.do)
- **Portal 이용약관 제16조②:** "공공데이터법 제36조 제3항에 따라 이용자는 제3자의 권리가 포함된 공공데이터가 제공된 경우 이를 이용하였더라도 진정한 권리자에게 발생한 손해에 대하여 책임을 지지 않습니다. 다만 제3자의 권리가 포함된 사실을 인지하고 이용한 경우는 제외됩니다." — [data.go.kr 이용약관](https://www.data.go.kr/ugs/selectPortalPolicyView.do)
- **Portal 이용약관 제14조4:** a 제공기관 may stop providing data where "공공데이터의 이용이 제3자의 권리를 현저하게 침해하는 경우". — [data.go.kr 이용약관](https://www.data.go.kr/ugs/selectPortalPolicyView.do)

### Inferences
- **"제한 없음" with no KOGL type is plausible for (a).** Under 관리지침 제8조②, 저작물-bearing data should carry a KOGL type, so the absence of one is consistent with NLK treating the listed dataset as non-copyrightable bibliographic facts. That supports republishing the factual fields.
- **The 제36조③ safe harbor does not help a knowing republisher.** 책소개 and 표지 are obviously third-party works and the user now knows it, so the "인지하고 이용한 경우" exclusion would apply.
- **NLK's own terms may also apply.** Because the listing is LINK-type, the actual data comes from NLK under an NLK key, so the NLK 통합회원 약관 (Q3) arguably still governs alongside the data.go.kr label.

### Gaps
- I found no explanation from NLK of what "이용허락범위 제한 없음" covers for the Seoji fields.

## Q5. LOD license (공공누리 1유형 + CC0 1.0): does it cover dcterms:tableOfContents and description? Any statement on third-party content?

### Takeaway
- **The LOD download page grants 공공누리 제1유형 and CC0 1.0 to the datasets as a whole, without field exclusions.** It says nothing about third-party content.
- **The LOD's contents, description and abstract values are NLK cataloguing notes (MARC-style 505/500/520), not publisher blurbs.** Samples: "색인수록", "附錄 : 出版品 總目錄", "고대복식사를 400매 사진자료와 함께 해설을 수록".
- **LOD has no cover images.**

### Cited Findings
- **License statement:** "제공되는 데이터셋은 국립중앙도서관 LOD 온톨로지 모델을 기반으로 설계된 트리플 단위 데이터로 구성되었으며, 공공누리 제1유형 및 크리에이티브 커먼즈 라이선스 CC0 1.0 조건에 따라 도서관, 출판산업, 연구 등의 목적으로 누구나 자유롭게 이용할 수 있습니다." — [LOD 데이터셋 다운로드](https://lod.nl.go.kr/home/dataset/datadownload.do)
- **Scope:** the datasets cover "국립중앙도서관 전체 소장자료를 대상으로 구축한 국가서지 링크드 오픈 데이터(LOD)" in TTL, RDF/XML and JSON-LD. — [LOD 데이터셋 다운로드](https://lod.nl.go.kr/home/dataset/datadownload.do)
- **The LOD introduction encourages reuse** of exported data in other services ("또 다른 서비스 또는 프로그램에 국가서지 링크드 오픈 데이터(LOD)에서 반출한 데이터를 활용할 수 있습니다"). It has no separate license or terms page. — [LOD 서비스 소개](https://lod.nl.go.kr/home/service/introduction.do)
- **SPARQL samples of the content fields** (direct queries to `https://lod.nl.go.kr/sparql`, 2026-10-24):
  - `dcterms:tableOfContents` on `nlk:CMO000000010` = "使西日記;味水軒日記;孫夏峰先生日譜殘稿;…" and on `nlk:CMO000000053` = "1.軍事 1". These are contents-note style.
  - `dcterms:description` on `nlk:CMO000000018` = "색인수록" and on `nlk:CMO000000015` = "附錄 : 出版品 總目錄". These are general notes.
  - `dcterms:abstract` on `nlk:KCF200100344` = "고대복식사를 400매 사진자료와 함께 해설을 수록". This is a short summary note.
  - A `bibo:abstract` query timed out with the message "쿼리 실행이 제한 시간을 초과했습니다".
  - — [lod.nl.go.kr/sparql](https://lod.nl.go.kr/sparql)
- **The LOD-based data.go.kr API (15154402) exposes the same fields** (DCTERMS_tableOfContents, DCTERMS_abstract, BIBO_abstract, DCTERMS_description), with 이용허락범위 "제한 없음" and no price or cover field (previous research note). — [data.go.kr 15154402](https://www.data.go.kr/data/15154402/openapi.do)

### Inferences
- **The CC0/KOGL1 grant reads as blanket, covering all triples including tableOfContents and abstract.** Most such values are short factual or cataloguer notes, so the third-party risk is low.
- **The risk is not zero.** Some 505 contents notes reproduce a book's table of contents verbatim, and a 520 summary might be adapted from jacket copy. NLK cannot waive rights it does not hold. CC0 is a waiver by the affirmer, not a warranty about third-party rights. This is a general CC0 property; the CC0 legal text was not fetched in this session.
- **For (b), LOD tableOfContents and abstract are much safer to republish than Seoji BOOK_INTRODUCTION or BOOK_SUMMARY.**

### Gaps
- There is no explicit statement on LOD pages about third-party content or field exclusions.
- I did not measure how many LOD tableOfContents values are full verbatim tables of contents versus short notes.

## Q6. Purpose statements: is the system explicitly for 유통 of 서지정보 to 서점, 포털 and 도서관?

### Takeaway
Yes, NLK's own descriptions frame the system as distributing standardized book information to libraries and the book trade.
- **NLK:** "정확한 도서정보의 유통" via OpenAPI since 2017.
- **The 2013 launch:** libraries and bookstores "제공받음".
- **The data.go.kr description:** "도서관, 서점, 학계 … 출판 유통".

None of these statements names 포털 or AI services. None extends explicitly to 책소개 or 표지 images.

### Cited Findings
- **NLK's description of the system:** "ISBN·ISSN·UCI·납본 시스템은 발행처(출판사)가 ISBN, ISSN 발급 신청 및 납본 접수, 확인 등의 업무를 편리하게 이용할 수 있도록 지원하고, 국내 발행 자료의 도서정보를 체계적으로 관리하여 고품질의 데이터를 제공·공유하기 위한 통합관리시스템" / "2017년부터 OpenAPI로 방대한 도서정보를 제공하고 있으며, ISBN랜딩페이지·QR코드와 같은 도서정보로의 다양한 접근방법을 제공하여 도서관계의 수서 및 정리업무 효율성 증대 뿐 아니라 정확한 도서정보의 유통, 출판예정도서의 홍보를 통한 판매촉진의 효과를 기대" — [NLK 도서관정보화](https://www.nl.go.kr/NL/contents/N50107060000.do)
- **2013 launch of "서지정보유통지원 홈페이지"** (article dated 2013.03.04): "출판을 앞둔 출판사가 서지정보유통지원홈페이지에서 CIP와 ISBN을 함께 신청하면, 국립중앙도서관은 CIP를 토대로 출판 전 도서정보데이터를 생성한다"; "전국의 도서관 및 서점 등의 기관도 이 데이터를 활용할 수 있다"; "출판사는 출판예정도서를 사전에 홍보할 수 있고, 도서관과 서점 등은 표준 목록 및 출판 전 도서정보데이터를 제공받음으로써 …" — [독서신문 2013-03-04](http://www.readersnews.com/news/articleView.html?idxno=40439)
- **2024 link-up with KPIPA's 출판유통통합전산망:** "출판사는 출판전산망 내에서 ISBN 신청부터 도서 유통단계의 서지정보까지 원스톱으로 입력할 수 있고, 이를 유통사에 전송하는 등 다양하게 활용할 수 있다." The page says nothing about 책소개, 목차, 표지 or data-use terms. — [NLK 보도자료 2024-09-23](https://www.nl.go.kr/NL/contents/N50603000000.do?schM=view&id=49248&schBcid=normal0302); [librarian.nl.go.kr 2024-10-08](https://librarian.nl.go.kr/LI/contents/L30301000000.do?schM=view&page=1&viewCount=9&id=49371&schBdcode=&schGroupCode=)
- **data.go.kr description:** "… 도서관, 서점, 학계 등 다양한 분야에서의 자료 검색과 출판 유통, 학술 활용에도 도움을 줄 수 있습니다." — [data.go.kr 3078982](https://www.data.go.kr/data/3078982/openapi.do)
- **The 2026-01 LOD OpenAPI press release** states an intent to expand openness for AI: "AI 학습 및 지능형 서비스 활용을 고려한 데이터 개방을 단계적으로 확대" (previous research note). — [NLK 보도자료 2026-01-12](https://www.nl.go.kr/NL/contents/N50603000000.do?schM=view&id=54867&schBcid=normal0302)

### Inferences
- **Downstream circulation of the factual records is the declared purpose.** Publishers submit data so that it circulates to libraries and bookstores for 수서/정리 and sales promotion. That supports an implied-intent argument for republishing (a). It also arguably supports showing publisher-supplied promotional content (책소개, 표지) in a book-discovery context. That second part is a weaker argument with no documentary consent behind it.
- **AI and MCP reuse is mentioned only for the LOD/data.go.kr OpenAPI line**, not for Seoji.

### Gaps
- I found no NLK statement that 책소개, 목차, 서평 or 표지 obtained through Seoji may be republished by third parties.

## Q7. Synthesis by field class: what NLK permits and forbids for a public website, public REST API or MCP server

### Takeaway
- **(a) Factual fields:** republishing is likely permissible in practice.
  - The data are facts, NLK's purpose is circulation, data.go.kr says "제한 없음", and the LOD equivalents are CC0/KOGL1.
  - There is residual contractual risk from the NLK 통합회원 이용약관's "사전 승낙" clauses for Seoji-sourced copies.
  - Using LOD as the primary source for overlapping fields removes most of that risk.
- **(b) Publisher text:** Seoji BOOK_INTRODUCTION, BOOK_SUMMARY and BOOK_TB_CNT are not covered by any NLK license I found. NLK's copyright policy limits free use to NLK-owned, KOGL-marked works. These texts are publisher-authored, so republishing them verbatim is the riskiest category. LOD tableOfContents, description and abstract are under CC0/KOGL1 and are mostly cataloguing notes, so the risk there is lower.
- **(c) Cover images (TITLE_URL):** no license from NLK; third-party works (publisher, designer, illustrator). Hotlinking or rehosting them through a public service is not authorized by any NLK document I found.

### Cited Findings
- **Free use covers only NLK-owned, KOGL-marked works;** other material needs "사전에 협의". — [NLK 저작권정책](https://www.nl.go.kr/NL/contents/N70600000000.do)
- **Membership terms require "사전 승낙"** for 영리행위 and for providing service-obtained information to others (제15조①5, 제17조④⑥). — [NLK 통합회원 이용약관](https://www.nl.go.kr/NL/contents/N60300000000.do)
- **The Seoji mirror is labeled "이용허락범위 제한 없음",** and its description lists factual fields only. — [data.go.kr 3078982](https://www.data.go.kr/data/3078982/openapi.do)
- **data.go.kr policy:** third-party-rights data requires the rights holder's license. — [data.go.kr 정책](https://www.data.go.kr/ugs/selectPortalPolicyView.do)
- **The LOD grant** is "공공누리 제1유형 및 … CC0 1.0 … 누구나 자유롭게 이용". — [LOD 데이터셋 다운로드](https://lod.nl.go.kr/home/dataset/datadownload.do)
- **Commercial MARC/목차 bulk via KOLIS-NET is restricted:** "MARC 및 목차 데이터의 영리적 이용을 제한하기 위하여 … 승인된 기관에 한하여 제공" (previous research note). This shows NLK treats 목차 data as commercially sensitive in at least one channel. — [KOLIS-NET 참여방법](https://www.nl.go.kr/kolisnet/contents/procedure.do)

### Inferences
- **Public website, REST API or MCP server, (a) factual fields:**
  - Source from LOD (CC0) where possible, and attribute "국립중앙도서관" as a courtesy and as the KOGL1 condition.
  - For Seoji-only fields (PRE_PRICE, EA_ADD_CODE, SET_ISBN, PUBLISH_PREDATE), attribute NLK and treat the 통합회원 약관 risk as low but nonzero.
  - Optionally get a written OK from 디지털정보기획과 (02-590-0548), which is also the 공공저작물 관리담당자.
- **(b) Seoji publisher text:** to keep the risk low, store and use it internally (for search indexing, for example) and do not republish it verbatim. Alternatives are linking to the publisher or retailer, or asking publishers directly. An MCP tool that returns full 책소개 text to an AI client is a public "전송" of the work.
- **(c) Covers:** do not rehost. Even hotlinking TITLE_URL from a public site rests on no license.
- **KOLIS-NET is a warning sign for 목차.** NLK's explicit non-commercial gate on 목차 bulk data suggests it may object to commercial redistribution of Seoji BOOK_TB_CNT, although the two channels differ.
- **Database producer rights (저작권법 제93조) are an untested risk for (a).** A wholesale mirror of the Seoji database could engage NLK's 데이터베이스제작자 rights over "전부 또는 상당한 부분". This is from general knowledge of Korean copyright law; the statute text was not fetched in this session. How it would play out for a public institution's openly listed dataset is uncertain.

### Gaps
- No primary NLK text resolves the tension between the 통합회원 약관 (prior approval) and the data.go.kr "제한 없음" label. Only NLK can clarify it.
- The publisher-side consent text is unread (Q1).
- I did not verify the 저작권법 제93조 text or whether it would apply here.
