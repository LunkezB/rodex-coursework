import pytest

from app.services.sosa import PersonNode, SosaCycleError, build_sosa_report


def test_build_sosa_report_three_generations() -> None:
    persons = {
        "p1": PersonNode(id="p1", full_name="Пробанд"),
        "p2": PersonNode(id="p2", full_name="Отец"),
        "p3": PersonNode(id="p3", full_name="Мать"),
        "p4": PersonNode(id="p4", full_name="Дед"),
        "p5": PersonNode(id="p5", full_name="Бабушка"),
    }
    parents_by_child = {
        "p1": ("p2", "p3"),
        "p2": ("p4", "p5"),
    }

    report = build_sosa_report(
        proband_id="p1",
        persons=persons,
        parents_by_child=parents_by_child,
        max_depth=3,
    )

    assert [(item.number, item.full_name, item.generation) for item in report] == [
        (1, "Пробанд", 1),
        (2, "Отец", 2),
        (3, "Мать", 2),
        (4, "Дед", 3),
        (5, "Бабушка", 3),
    ]


def test_build_sosa_report_skips_unknown_parent() -> None:
    persons = {
        "p1": PersonNode(id="p1", full_name="Пробанд"),
        "p2": PersonNode(id="p2", full_name="Отец"),
    }
    parents_by_child = {"p1": ("p2", None)}

    report = build_sosa_report(
        proband_id="p1",
        persons=persons,
        parents_by_child=parents_by_child,
        max_depth=2,
    )

    assert [item.number for item in report] == [1, 2]


def test_build_sosa_report_detects_cycle() -> None:
    persons = {
        "p1": PersonNode(id="p1", full_name="Пробанд"),
        "p2": PersonNode(id="p2", full_name="Отец"),
    }
    parents_by_child = {
        "p1": ("p2", None),
        "p2": ("p1", None),
    }

    with pytest.raises(SosaCycleError):
        build_sosa_report(
            proband_id="p1",
            persons=persons,
            parents_by_child=parents_by_child,
            max_depth=10,
        )
