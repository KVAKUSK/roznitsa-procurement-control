from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class Product:
    name: str
    category: str
    packaging: str | None = None
    mass_g: float | None = None
    brand: str | None = None
    line: str | None = None
    flavor: str | None = None


@dataclass(frozen=True)
class MatchResult:
    allowed: bool
    score: float
    reasons: tuple[str, ...]


def _norm(value: str | None) -> str:
    return " ".join((value or "").lower().replace("ё", "е").split())


def _same(a: str | None, b: str | None) -> bool:
    return bool(_norm(a)) and _norm(a) == _norm(b)


def evaluate_analogue(requested: Product, candidate: Product, preferred_mass_delta: float = 0.20) -> MatchResult:
    reasons: List[str] = []

    if not _same(requested.category, candidate.category):
        return MatchResult(False, 0.0, ("Категория товара не совпадает",))

    score = 0.55

    if requested.packaging and candidate.packaging:
        if _same(requested.packaging, candidate.packaging):
            score += 0.12
        else:
            reasons.append("Формат упаковки отличается")

    if requested.mass_g and candidate.mass_g:
        delta = abs(candidate.mass_g - requested.mass_g) / requested.mass_g
        if delta <= preferred_mass_delta:
            score += 0.12
        else:
            reasons.append(f"Масса отличается на {delta:.0%}, больше ориентира {preferred_mass_delta:.0%}")

    if requested.brand and candidate.brand:
        if _same(requested.brand, candidate.brand):
            score += 0.10
        else:
            reasons.append("Бренд отличается")

    if requested.line and candidate.line:
        if _same(requested.line, candidate.line):
            score += 0.06
        else:
            reasons.append("Линейка отличается")

    if requested.flavor and candidate.flavor:
        if _same(requested.flavor, candidate.flavor):
            score += 0.05
        else:
            reasons.append("Вкус/вариант отличается")

    return MatchResult(True, min(score, 1.0), tuple(reasons))


def rank_candidates(requested: Product, candidates: Iterable[Product]) -> list[tuple[Product, MatchResult]]:
    evaluated = [(candidate, evaluate_analogue(requested, candidate)) for candidate in candidates]
    allowed = [item for item in evaluated if item[1].allowed]
    return sorted(allowed, key=lambda item: item[1].score, reverse=True)
