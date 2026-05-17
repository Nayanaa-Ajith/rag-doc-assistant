# LangChain & LangGraph — Complete Guide

## What is LangChain?

LangChain is a framework for developing applications powered by language models. It provides:
- **Components**: Modular abstractions for working with LLMs, prompts, memory, indexes, chains, and agents.
- **Off-the-shelf chains**: Pre-built chains for common use cases like RAG, summarization, and Q&A.
- **LangGraph**: Extension for building stateful, multi-actor applications with LLMs as graphs.

## Installation

```bash
pip install langchain langchain-community langchain-groq
```

## Basic LLM Usage

```python
from langchain_groq import ChatGroq

llm = ChatGroq(model="llama3-8b-8192", temperature=0)
response = llm.invoke("What is the capital of France?")
print(response.content)  # Paris
```

## Prompt Templates

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that answers questions about {topic}."),
    ("human", "{question}"),
])

chain = prompt | llm
result = chain.invoke({"topic": "Python", "question": "What is a decorator?"})
```

## LCEL — LangChain Expression Language

LCEL uses the `|` pipe operator to compose chains:

```python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | llm | StrOutputParser()
result = chain.invoke({"topic": "Python", "question": "What is a list comprehension?"})
# Returns string directly
```

## RAG with LangChain

```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(embedding_function=embeddings, persist_directory="./db")
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
)
result = qa_chain.invoke({"query": "What is FastAPI?"})
```

## LangGraph — Stateful Graphs

LangGraph enables building agents as directed graphs where nodes are functions and edges control flow.

### Core Concepts

- **StateGraph**: The main graph class. Takes a TypedDict as state.
- **Nodes**: Python functions that take state and return updated state.
- **Edges**: Connections between nodes. Can be fixed or conditional.
- **Entry point**: The first node to run.
- **END**: Special constant marking terminal nodes.

### Basic Graph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    messages: list
    count: int

def node_a(state: State) -> State:
    return {"count": state["count"] + 1}

def node_b(state: State) -> State:
    return {"messages": state["messages"] + ["done"]}

def should_continue(state: State) -> str:
    if state["count"] < 3:
        return "a"
    return "b"

graph = StateGraph(State)
graph.add_node("a", node_a)
graph.add_node("b", node_b)
graph.set_entry_point("a")
graph.add_conditional_edges("a", should_continue, {"a": "a", "b": "b"})
graph.add_edge("b", END)

app = graph.compile()
result = app.invoke({"messages": [], "count": 0})
```

### Conditional Edges

```python
def route(state: State) -> str:
    """Return the name of the next node."""
    if state["score"] > 0.8:
        return "high_quality"
    elif state["score"] > 0.5:
        return "medium_quality"
    else:
        return "low_quality"

graph.add_conditional_edges(
    "grader",          # source node
    route,             # function that returns next node name
    {                  # mapping: return value → node name
        "high_quality": "generator",
        "medium_quality": "rewriter",
        "low_quality": "fallback",
    }
)
```

### Streaming Graph Execution

```python
for event in app.stream(initial_state):
    for node_name, node_output in event.items():
        print(f"Node '{node_name}' output: {node_output}")
```

## Document Loaders

```python
from langchain_community.document_loaders import TextLoader, DirectoryLoader

# Single file
loader = TextLoader("my_doc.txt")
docs = loader.load()

# Directory
loader = DirectoryLoader("./docs", glob="**/*.md", loader_cls=TextLoader)
docs = loader.load()
```

## Text Splitters

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,
    separators=["\n\n", "\n", ".", " "],  # try larger separators first
)
chunks = splitter.split_documents(docs)
```

## Memory in LangChain

```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(k=5)  # keep last 5 exchanges
memory.save_context({"input": "Hi"}, {"output": "Hello!"})
memory.load_memory_variables({})
# {"history": "Human: Hi\nAI: Hello!"}
```

## Output Parsers

```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

class Grade(BaseModel):
    score: str  # "yes" or "no"
    reason: str

parser = JsonOutputParser(pydantic_object=Grade)
chain = prompt | llm | parser
result = chain.invoke(...)
# result is a Grade object
```

## Troubleshooting Common Issues

**Issue**: `langchain.schema.output_parser.OutputParserException`
**Solution**: Use try/except around chain invocations and add format instructions to your prompt.

**Issue**: Context window exceeded
**Solution**: Reduce chunk size, use fewer documents in context, or switch to a model with larger context.

**Issue**: Slow embeddings
**Solution**: Batch your embedding calls, use `SentenceTransformer.encode(texts, batch_size=32)`.

**Issue**: ChromaDB collection not persisting
**Solution**: Use `PersistentClient` instead of `EphemeralClient`:
```python
import chromadb
client = chromadb.PersistentClient(path="./chroma_db")
```
