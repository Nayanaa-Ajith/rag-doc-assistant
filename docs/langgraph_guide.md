# LangGraph Developer Guide

LangGraph is a library for building stateful, multi-agent applications with LLMs. It extends LangChain with graph-based orchestration.

## Core Concepts

### StateGraph

LangGraph uses a StateGraph to define the workflow. Nodes are Python functions; edges define the flow.

from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    messages: list
    count: int

graph = StateGraph(State)

### Nodes

Nodes are Python functions that take state and return updated state.

def my_node(state: State) -> State:
    return {**state, "count": state["count"] + 1}

graph.add_node("my_node", my_node)

### Edges

graph.add_edge("node_a", "node_b")   # Always goes from A to B
graph.set_entry_point("node_a")      # First node to run

### Conditional Edges

def router(state: State) -> str:
    if state["count"] > 5:
        return "done"
    return "continue"

graph.add_conditional_edges("my_node", router, {
    "done": END,
    "continue": "my_node",
})

## Building a RAG Agent

### State Schema

class RAGState(TypedDict):
    question: str
    documents: list
    answer: str
    retry_count: int

### Retrieval Node

def retrieve(state: RAGState) -> RAGState:
    docs = vectorstore.similarity_search(state["question"])
    return {**state, "documents": docs}

### Grading Node

def grade_documents(state: RAGState) -> RAGState:
    relevant = []
    for doc in state["documents"]:
        score = llm.invoke(f"Is this relevant? {doc.page_content}")
        if "yes" in score.content.lower():
            relevant.append(doc)
    return {**state, "documents": relevant}

### Generation Node

def generate(state: RAGState) -> RAGState:
    context = "
".join([d.page_content for d in state["documents"]])
    answer = llm.invoke(f"Context: {context}
Question: {state["question"]}")
    return {**state, "answer": answer.content}

## Compiling and Running

app = graph.compile()
result = app.invoke({"question": "What is LangGraph?", "documents": [], "answer": "", "retry_count": 0})

## Streaming

for event in app.stream({"question": "Hello"}):
    for key, value in event.items():
        print(f"Node: {key}")

## Checkpointing (Persistence)

from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string(":memory:") as checkpointer:
    app = graph.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "session-1"}}
    result = app.invoke(state, config=config)

## Human-in-the-Loop

graph.add_node("human_review", lambda s: s)
graph.add_edge("generation", "human_review")

app = graph.compile(interrupt_before=["human_review"])

## Multi-Agent Patterns

LangGraph supports supervisor patterns where one agent routes tasks to specialized sub-agents.

Supervisor decides which agent handles each task.
Each agent is a subgraph with its own state and tools.
Results flow back to the supervisor for final synthesis.

## Self-Corrective RAG Pattern (CRAG)

The Corrective RAG pattern grades retrieved documents and corrects the retrieval when documents are irrelevant.

1. Retrieve documents
2. Grade each document as relevant or irrelevant
3. If all irrelevant: rewrite query and re-retrieve (with retry limit)
4. If some relevant: filter and generate
5. Optional: check if generated answer is grounded in context (Self-RAG)

This pattern is implemented with conditional edges that route back to retrieval when grading fails.
