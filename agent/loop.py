import json

from agent import llm
from agent.index import VectorIndex
from agent.tools import run_sql

MAX_STEPS = 4

SYSTEM_PROMPT = """You answer questions about AI open-source projects (GitHub repos) and arXiv papers.
You have a DuckDB database. Use tools; never invent numbers.
- Call run_sql with ONE DuckDB SELECT query for any question about counts, rankings or stars.
- Call search_papers for questions about paper topics ("papers about X").
- Only use tables and columns listed in the schema below. If a query errors, fix it and retry.
- Some columns (stars_gained_*) can be NULL because history is short; say so if you see NULLs.
Answer briefly in plain language from the tool results.

Relevant schema and examples:
{context}"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Run a read-only DuckDB SELECT query and return up to 50 rows.",
            "parameters": {
                "type": "object",
                "properties": {"sql": {"type": "string", "description": "A single SELECT query"}},
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_papers",
            "description": "Semantic search over arXiv paper titles and abstracts.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Topic to look for"}},
                "required": ["query"],
            },
        },
    },
]


def schema_context(schema_index: VectorIndex, question: str, k: int = 4) -> str:
    return "\n".join(hit["text"] for hit in schema_index.search(question, k=k))


def search_papers(paper_index: VectorIndex, query: str) -> dict:
    hits = paper_index.search(query, k=5)
    return {
        "papers": [
            {"title": h["title"], "category": h["category"], "url": h["url"]} for h in hits
        ]
    }


def ask(question: str, schema_index: VectorIndex, paper_index: VectorIndex | None) -> str:
    context = schema_context(schema_index, question)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
        {"role": "user", "content": question},
    ]
    for _ in range(MAX_STEPS):
        reply = llm.chat(messages, tools=TOOLS)
        messages.append(reply)
        calls = reply.get("tool_calls") or []
        if not calls:
            return reply["content"]
        for call in calls:
            name, args = call["function"]["name"], call["function"]["arguments"]
            if name == "run_sql":
                result = run_sql(args.get("sql", ""))
            elif name == "search_papers" and paper_index is not None:
                result = search_papers(paper_index, args.get("query", ""))
            else:
                result = {"error": f"Unknown or unavailable tool: {name}"}
            messages.append(
                {"role": "tool", "name": name, "content": json.dumps(result, default=str)}
            )
    return "I could not finish answering within the step limit. Try a more specific question."
