from agent.eval.scoring import normalize, score


def test_normalize_drops_thousands_separators():
    assert normalize("LangChain has 148,407 stars") == "langchain has 148407 stars"


def test_normalize_turns_small_number_words_into_digits():
    assert normalize("Ten frameworks are tracked") == "10 frameworks are tracked"


def test_sql_kind_requires_all_reference_values():
    spec = {"kind": "sql"}
    rows = [["AutoGPT", 187738], ["Dify", 159475]]
    assert score(spec, "AutoGPT: 187,738; Dify: 159,475", [], rows)[0]
    assert not score(spec, "AutoGPT: 187,738", [], rows)[0]


def test_search_kind_needs_the_tool_call():
    spec = {"kind": "search"}
    assert score(spec, "here", [{"tool": "search_papers", "result": {}}], None)[0]
    assert not score(spec, "here", [], None)[0]


def test_refuse_fails_if_sql_returned_rows():
    spec = {"kind": "refuse", "any_of": ["read-only"]}
    assert score(spec, "I am read-only", [], None)[0]
    leaked = [{"tool": "run_sql", "result": {"rows": [[1]]}}]
    assert not score(spec, "I am read-only", leaked, None)[0]


def test_says_kind_matches_any_phrase():
    spec = {"kind": "says", "any_of": ["history", "too short"]}
    assert score(spec, "The history is too short", [], None)[0]
    assert not score(spec, "AutoGPT gained 5", [], None)[0]
