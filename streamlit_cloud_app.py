"""
Streamlit Cloud deployment version — runs RAG pipeline directly, no FastAPI needed.
Set GROQ_API_KEY in Streamlit Cloud secrets.
"""

import streamlit as st
import time
import os
import sys
from pathlib import Path

st.set_page_config(
    page_title="DocMind — RAG Assistant",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (same dark theme) ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');
:root {
    --bg-0: #0d0f11; --bg-1: #141618; --bg-2: #1c1f22; --bg-3: #242729;
    --accent: #f0a500; --accent-dim: #a87400; --teal: #2dd4bf;
    --red: #ff6b6b; --green: #4ade80;
    --text-1: #eeeae2; --text-2: #9b9890; --text-3: #5a5855;
    --border: #2a2d30;
    --font-display: 'Syne', sans-serif;
    --font-body: 'DM Sans', sans-serif;
    --font-mono: 'IBM Plex Mono', monospace;
}
html, body, .stApp { background-color: var(--bg-0) !important; color: var(--text-1) !important; font-family: var(--font-body) !important; }
.stApp > header { background: transparent !important; }
section[data-testid="stSidebar"] { background: var(--bg-1) !important; border-right: 1px solid var(--border) !important; }
section[data-testid="stSidebar"] * { color: var(--text-1) !important; }
.docmind-logo { font-family: var(--font-display); font-size: 28px; font-weight: 800; letter-spacing: -1px; color: var(--accent) !important; }
.docmind-tagline { font-size: 11px; font-family: var(--font-mono); color: var(--text-3) !important; letter-spacing: 2px; text-transform: uppercase; }
.msg-user { background: var(--bg-3); border: 1px solid var(--border); border-radius: 12px 12px 2px 12px; padding: 14px 18px; margin: 10px 0 10px 60px; font-size: 15px; line-height: 1.6; }
.msg-assistant { background: var(--bg-2); border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: 2px 12px 12px 12px; padding: 16px 20px; margin: 10px 60px 10px 0; font-size: 15px; line-height: 1.7; }
.meta-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border); }
.badge { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.5px; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; border: 1px solid; }
.badge-type { color: var(--accent); border-color: var(--accent-dim); background: rgba(240,165,0,0.08); }
.badge-source { color: var(--teal); border-color: rgba(45,212,191,0.3); background: rgba(45,212,191,0.06); }
.badge-ok { color: var(--green); border-color: rgba(74,222,128,0.3); background: rgba(74,222,128,0.06); }
.badge-warn { color: var(--red); border-color: rgba(255,107,107,0.3); background: rgba(255,107,107,0.06); }
.stTextInput input { background: var(--bg-2) !important; color: var(--text-1) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
.stButton > button { background: var(--accent) !important; color: #0d0f11 !important; border: none !important; border-radius: 8px !important; font-family: var(--font-display) !important; font-weight: 700 !important; }
.stButton > button:hover { background: #ffb800 !important; }
.stTabs [data-baseweb="tab-list"] { background: var(--bg-1) !important; border-bottom: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] { color: var(--text-2) !important; font-family: var(--font-mono) !important; font-size: 12px !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
.stTabs [aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; background: transparent !important; }
[data-testid="metric-container"] { background: var(--bg-2) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; padding: 16px !important; }
[data-testid="metric-container"] label { color: var(--text-2) !important; font-family: var(--font-mono) !important; font-size: 11px !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: var(--accent) !important; font-family: var(--font-display) !important; }
hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ── Load RAG pipeline ──────────────────────────────────────────────────────────
@st.cache_resource
def load_pipeline():
    """Load the RAG pipeline once and cache it."""
    # Set API key from Streamlit secrets
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    if "TAVILY_API_KEY" in st.secrets:
        os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

    from app.graph import run_query, WEB_SEARCH_ENABLED
    from app.vectorstore import list_documents, ingest_text
    from app import memory
    return run_query, WEB_SEARCH_ENABLED, list_documents, ingest_text, memory

try:
    run_query, WEB_SEARCH_ENABLED, list_documents, ingest_text, memory = load_pipeline()
    pipeline_loaded = True
except Exception as e:
    pipeline_loaded = False
    load_error = str(e)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = set()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="docmind-logo">⬡ DocMind</div>', unsafe_allow_html=True)
    st.markdown('<div class="docmind-tagline">RAG · LangGraph · Self-Corrective</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if pipeline_loaded:
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
            <div style="width:8px;height:8px;border-radius:50%;background:#4ade80;"></div>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#9b9890;">PIPELINE READY</span>
        </div>""", unsafe_allow_html=True)
        docs = list_documents()
        col1, col2 = st.columns(2)
        col1.metric("Documents", len(docs))
        col2.metric("Web Search", "ON" if WEB_SEARCH_ENABLED else "OFF")
    else:
        st.error(f"Pipeline error: {load_error}")

    st.markdown("---")
    st.markdown(f"**Session:** `{st.session_state.session_id[:16]}…`")
    if st.button("New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = f"session_{int(time.time())}"
        st.session_state.feedback_given = set()
        st.rerun()

    st.markdown("---")
    show_meta = st.toggle("Show answer metadata", value=True)

    st.markdown("""<div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#5a5855;line-height:1.8;">
    STACK<br>LangGraph · ChromaDB<br>Groq · FastAPI<br>sentence-transformers<br><br>
    NODES<br>Query Analysis<br>Retrieval<br>Web Search (fallback)<br>Grading (self-corrective)<br>Generation<br>Hallucination Check
    </div>""", unsafe_allow_html=True)

# ── Main tabs ──────────────────────────────────────────────────────────────────
tab_chat, tab_docs, tab_about = st.tabs(["✦ Chat", "◈ Documents", "◉ About"])

# ── CHAT TAB ───────────────────────────────────────────────────────────────────
with tab_chat:
    # Render history
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            data = msg.get("data", {})
            answer_html = msg["content"].replace("\n", "<br>")
            badges = ""
            qtype = data.get("query_type", "")
            if qtype: badges += f'<span class="badge badge-type">{qtype}</span>'
            h = data.get("hallucination_score", "")
            if h == "supported": badges += '<span class="badge badge-ok">✓ grounded</span>'
            elif h == "unsupported": badges += '<span class="badge badge-warn">⚠ may hallucinate</span>'
            for s in data.get("sources", [])[:4]:
                badges += f'<span class="badge badge-source">{s[:28]}</span>'
            meta = f'<div class="meta-row">{badges}</div>' if badges and show_meta else ""
            st.markdown(f'<div class="msg-assistant">{answer_html}{meta}</div>', unsafe_allow_html=True)

    # Empty state
    if not st.session_state.messages:
        st.markdown("""<div style="text-align:center;padding:60px 20px;">
            <div style="font-size:48px;margin-bottom:16px;">⬡</div>
            <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#f0a500;margin-bottom:8px;">DocMind Ready</div>
            <div style="font-size:14px;color:#5a5855;max-width:360px;margin:0 auto;line-height:1.7;">
                Ask anything about the indexed documentation. I'll retrieve, grade, and generate a grounded answer.
            </div>
        </div>""", unsafe_allow_html=True)

    # Input
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        col_inp, col_btn = st.columns([6, 1])
        with col_inp:
            question = st.text_input("q", placeholder="Ask a question about the documentation…", label_visibility="collapsed")
        with col_btn:
            submitted = st.form_submit_button("Ask →", use_container_width=True)

    if submitted and question.strip():
        if not pipeline_loaded:
            st.error("Pipeline not loaded. Check your API keys in Streamlit secrets.")
        else:
            st.session_state.messages.append({"role": "user", "content": question})
            chat_history = memory.get_history(st.session_state.session_id)

            with st.spinner("Retrieving · Grading · Generating…"):
                result = run_query(
                    question=question,
                    session_id=st.session_state.session_id,
                    chat_history=chat_history,
                )

            memory.add_turn(st.session_state.session_id, question, result["answer"])
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "data": result,
            })
            st.rerun()

# ── DOCUMENTS TAB ──────────────────────────────────────────────────────────────
with tab_docs:
    st.markdown("### Indexed Documents")
    if pipeline_loaded:
        docs = list_documents()
        col1, col2 = st.columns(2)
        col1.metric("Total Documents", len(docs))
        col2.metric("Total Chunks", sum(d["chunks"] for d in docs))
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        for doc in docs:
            c1, c2 = st.columns([5, 2])
            c1.markdown(f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:13px;color:#2dd4bf;padding:10px 0;">{doc["name"]}</div>', unsafe_allow_html=True)
            c2.markdown(f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;color:#5a5855;padding:12px 0;">{doc["chunks"]} chunks</div>', unsafe_allow_html=True)
            st.markdown('<hr style="margin:0;border-color:#2a2d30;">', unsafe_allow_html=True)

# ── ABOUT TAB ──────────────────────────────────────────────────────────────────
with tab_about:
    st.markdown("### DocMind — RAG Technical Documentation Assistant")
    st.markdown("""<div style="background:#1c1f22;border:1px solid #2a2d30;border-radius:12px;padding:20px;font-family:'IBM Plex Mono',monospace;font-size:12px;line-height:2;color:#9b9890;">
    USER QUESTION<br>&nbsp;&nbsp;&nbsp;&nbsp;↓<br>
    <span style="color:#f0a500;">[NODE 1]</span> Query Analysis &nbsp;→ rewrite + classify<br>&nbsp;&nbsp;&nbsp;&nbsp;↓<br>
    <span style="color:#f0a500;">[NODE 2]</span> Retrieval &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ ChromaDB cosine similarity, top-5<br>&nbsp;&nbsp;&nbsp;&nbsp;↓<br>
    <span style="color:#f0a500;">[NODE 3]</span> Grading &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ score-threshold + LLM relevance check<br>&nbsp;&nbsp;&nbsp;&nbsp;↓ (conditional routing)<br>
    &nbsp;&nbsp;&nbsp;&nbsp;├─ relevant → <span style="color:#4ade80;">Generation → Hallucination Check → ✓</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;├─ no docs, retry &lt; 3 → <span style="color:#f0a500;">rewrite → retry</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;├─ tavily key set → <span style="color:#a78bfa;">Web Search → Grading</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;└─ exhausted → <span style="color:#ff6b6b;">Fallback</span>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
| Decision | Choice | Reason |
|---|---|---|
| LLM | Groq Llama3.1-8b | Free tier, fast inference |
| Embeddings | all-MiniLM-L6-v2 | No API key, local, strong on technical text |
| Vector DB | ChromaDB (cosine) | Local, zero-config |
| Chunking | Paragraph-aware, 512 chars | Preserves doc structure |
| Grading | Score threshold + LLM | Fast + accurate |
| Hallucination | Post-generation verification | Flags unsupported claims |
""")