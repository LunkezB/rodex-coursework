from collections import deque
from collections.abc import Mapping

from pydantic import BaseModel, Field


class SosaCycleError(ValueError):
    """Raised when a cyclic ancestry link is detected."""


class PersonNode(BaseModel):
    id: str
    full_name: str


class SosaReportItem(BaseModel):
    number: int = Field(description="Номер по системе Соса–Страдоница")
    person_id: str
    full_name: str
    generation: int = Field(description="Поколение: 1 - пробанд, 2 - родители и т.д.")


def build_sosa_report(
    *,
    proband_id: str,
    persons: Mapping[str, PersonNode],
    parents_by_child: Mapping[str, tuple[str | None, str | None]],
    max_depth: int = 10,
) -> list[SosaReportItem]:
    """Build a Sosa-Stradonitz ancestry report.

    Rules:
    - proband has number 1;
    - father of n has number 2n;
    - mother of n has number 2n + 1;
    - unknown parents are skipped;
    - cyclic ancestry produces SosaCycleError.

    parents_by_child maps child_id -> (father_id, mother_id).
    """
    if max_depth < 1:
        raise ValueError("max_depth must be >= 1")
    if proband_id not in persons:
        raise KeyError(f"Unknown proband_id: {proband_id}")

    result: dict[int, SosaReportItem] = {}
    queue: deque[tuple[str, int, int, tuple[str, ...]]] = deque([(proband_id, 1, 1, ())])

    while queue:
        person_id, number, generation, path = queue.popleft()

        if person_id in path:
            cycle = " -> ".join((*path, person_id))
            raise SosaCycleError(f"Cycle detected in ancestry: {cycle}")

        person = persons.get(person_id)
        if person is None:
            continue

        result[number] = SosaReportItem(
            number=number,
            person_id=person.id,
            full_name=person.full_name,
            generation=generation,
        )

        if generation >= max_depth:
            continue

        father_id, mother_id = parents_by_child.get(person_id, (None, None))
        next_path = (*path, person_id)

        if father_id is not None:
            queue.append((father_id, number * 2, generation + 1, next_path))
        if mother_id is not None:
            queue.append((mother_id, number * 2 + 1, generation + 1, next_path))

    return [result[number] for number in sorted(result)]
