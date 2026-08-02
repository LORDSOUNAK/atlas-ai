import asyncio

from aetheros.application.langgraph.langgraph_runtime import LangGraphRuntime


def test_langgraph_runtime_execute_and_stream():
    runtime = LangGraphRuntime()
    definition = {"nodes": [{"id": "n1"}, {"id": "n2"}]}
    graph_id = "g1"

    runtime.compile_graph(graph_id=graph_id, definition=definition)

    # Test synchronous execute (runs to completion)
    result = runtime.execute(graph_id=graph_id)
    assert result.graph_id == graph_id
    assert result.status == "COMPLETED"
    assert isinstance(result.outputs, list)

    # Test async stream
    async def drain_stream():
        items = []
        async for chunk in runtime.astream(graph_id=graph_id):
            items.append(chunk)
        return items

    items = asyncio.run(drain_stream())
    # stream yields start + node events + complete
    assert any(c.get("event") == "start" for c in items)
    assert any(c.get("event") == "complete" for c in items)
