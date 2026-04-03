import csv
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Expression:
    index: int
    english_text: str
    korean_text: str
    romanization: str
    tts_korean: str = ""


def load_expressions(path: str) -> list[Expression]:
    p = Path(path)
    if p.suffix == ".json":
        return _load_json(p)
    return _load_csv(p)


def _load_csv(path: Path) -> list[Expression]:
    expressions = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            tts_kr = (row.get("tts_korean") or "").strip()
            expressions.append(Expression(
                index=i,
                english_text=row["english_text"].strip(),
                korean_text=row["korean_text"].strip(),
                romanization=row["romanization"].strip(),
                tts_korean=tts_kr if tts_kr else row["korean_text"].strip(),
            ))
    _validate(expressions)
    return expressions


def _load_json(path: Path) -> list[Expression]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    expressions = [
        Expression(index=i, english_text=item["english_text"].strip(),
                   korean_text=item["korean_text"].strip(),
                   romanization=item["romanization"].strip())
        for i, item in enumerate(data)
    ]
    _validate(expressions)
    return expressions


def _validate(expressions: list[Expression]):
    for expr in expressions:
        if not expr.english_text or not expr.korean_text or not expr.romanization:
            raise ValueError(f"Expression {expr.index}: empty field detected")
