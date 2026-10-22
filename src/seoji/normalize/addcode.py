from dataclasses import dataclass

# NLK ISBN 부가기호 tables. Reader codes 2, 3 and 8 are unassigned.
READER_LABELS = {
    "0": "교양",
    "1": "실용",
    "4": "청소년",
    "5": "중·고 학습참고",
    "6": "초등 학습참고",
    "7": "아동",
    "9": "전문",
}
FORM_LABELS = {
    "0": "문고본",
    "1": "사전",
    "2": "신서판",
    "3": "단행본",
    "4": "전집·총서·시리즈",
    "5": "전자출판물",
    "6": "도감",
    "7": "그림책·만화",
    "8": "혼합자료",
}


@dataclass(frozen=True)
class AddCode:
    code: str
    reader: str
    form: str
    kdc_class: str
    kdc_division: str


def decode_add_code(code: str | None) -> AddCode | None:
    if not code or len(code) != 5 or not code.isdigit():
        return None
    return AddCode(code, code[0], code[1], code[2], code[2:4])
