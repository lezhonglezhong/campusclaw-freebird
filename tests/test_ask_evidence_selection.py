"""Answer prompting selects useful evidence from a bounded retrieval pool."""

from types import SimpleNamespace

from campusclaw.knowledge_api import select_answer_evidence


def hit(chunk_id: int, text: str, title: str = "校园能耗记录"):
    return SimpleNamespace(
        chunk=SimpleNamespace(id=chunk_id, chunk_text=text),
        title=title,
    )


def install_titles(monkeypatch):
    monkeypatch.setattr(
        "campusclaw.knowledge_api.public_hit",
        lambda session, candidate: {"material_title": candidate.title},
    )


def test_comparison_selection_retains_all_values_and_drops_background(monkeypatch):
    install_titles(monkeypatch)
    background = hit(1, "这是校园节能实验的背景介绍。", "实验背景")
    building_one = hit(2, "一号楼的用电量下降了150度。")
    building_three = hit(3, "三号楼的用电量下降了300度。")
    building_four = hit(4, "四号楼的用电量下降了40度。")

    selected = select_answer_evidence(
        None,
        "哪个楼的用电量下降最多？",
        [background, building_one, building_three, building_four],
    )

    assert [candidate.chunk.id for candidate in selected] == [2, 3, 4]
    assert [candidate.chunk.chunk_text for candidate in selected] == [
        "一号楼的用电量下降了150度。",
        "三号楼的用电量下降了300度。",
        "四号楼的用电量下降了40度。",
    ]


def test_selection_removes_duplicates_and_bounds_semantic_fallback(monkeypatch):
    install_titles(monkeypatch)
    candidates = [hit(index, f"semantic paraphrase {index}", "unrelated") for index in range(1, 8)]

    selected = select_answer_evidence(None, "无字面重合问题", [candidates[0], candidates[0], *candidates[1:]])

    assert [candidate.chunk.id for candidate in selected] == [1, 2, 3, 4]


def test_noncomparison_selection_uses_relevance_instead_of_first_four(monkeypatch):
    install_titles(monkeypatch)
    candidates = [
        hit(1, "unrelated background", "background"),
        hit(2, "another unrelated section", "appendix"),
        hit(3, "光合作用需要光。", "生物"),
        hit(4, "irrelevant notes", "notes"),
        hit(5, "光合作用产生氧气。", "生物"),
    ]

    selected = select_answer_evidence(None, "光合作用会产生什么？", candidates)

    assert [candidate.chunk.id for candidate in selected] == [3, 5]
