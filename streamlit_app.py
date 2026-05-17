"""
Streamlit frontend for the RAG Documentation Assistant.

Design: Dark editorial aesthetic — deep charcoal background, amber/gold accents,
IBM Plex Mono for code elements, clean professional feel inspired by technical journals.
"""

import streamlit as st
import httpx
import json
import time
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocMind — RAG Assistant",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://localhost:8000"

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ── Root ──────────────────────────────────────────────────────────────────── */
:root {
    --bg-0: #0d0f11;
    --bg-1: #141618;
    --bg-2: #1c1f22;
    --bg-3: #242729;
    --accent: #f0a500;
    --accent-dim: #a87400;
    --teal: #2dd4bf;
    --red: #ff6b6b;
    --green: #4ade80;
    --text-1: #eeeae2;
    --text-2: #9b9890;
    --text-3: #5a5855;
    --border: #2a2d30;
    --font-display: 'Syne', sans-serif;
    --font-body: 'DM Sans', sans-serif;
    --font-mono: 'IBM Plex Mono', monospace;
}

/* ── Global ─────────────────────────────────────────────────────────────────── */
html, body, .stApp {
    background-color: var(--bg-0) !important;
    color: var(--text-1) !important;
    font-family: var(--font-body) !important;
}

.stApp > header { background: transparent !important; }

/* ── Sidebar ─────────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--bg-1) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text-1) !important; }

/* ── Main branding ───────────────────────────────────────────────────────────── */
.docmind-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 0 0 24px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
}
.docmind-logo {
    font-family: var(--font-display);
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
    color: var(--accent) !important;
    line-height: 1;
}
.docmind-tagline {
    font-size: 11px;
    font-family: var(--font-mono);
    color: var(--text-3) !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 2px;
}

/* ── Chat messages ───────────────────────────────────────────────────────────── */
.msg-user {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 12px 12px 2px 12px;
    padding: 14px 18px;
    margin: 10px 0 10px 60px;
    font-size: 15px;
    line-height: 1.6;
    color: var(--text-1);
}
.msg-assistant {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 2px 12px 12px 12px;
    padding: 16px 20px;
    margin: 10px 60px 10px 0;
    font-size: 15px;
    line-height: 1.7;
    color: var(--text-1);
}
.msg-assistant code {
    font-family: var(--font-mono);
    background: var(--bg-3);
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 13px;
    color: var(--teal);
}
.msg-assistant pre {
    background: var(--bg-0);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px;
    overflow-x: auto;
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--text-1);
    margin: 12px 0;
}

/* ── Meta badges ─────────────────────────────────────────────────────────────── */
.meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
}
.badge {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid;
}
.badge-type { color: var(--accent); border-color: var(--accent-dim); background: rgba(240,165,0,0.08); }
.badge-source { color: var(--teal); border-color: rgba(45,212,191,0.3); background: rgba(45,212,191,0.06); }
.badge-ok { color: var(--green); border-color: rgba(74,222,128,0.3); background: rgba(74,222,128,0.06); }
.badge-warn { color: var(--red); border-color: rgba(255,107,107,0.3); background: rgba(255,107,107,0.06); }
.badge-web { color: #a78bfa; border-color: rgba(167,139,250,0.3); background: rgba(167,139,250,0.06); }
.badge-retry { color: var(--text-2); border-color: var(--border); background: var(--bg-3); }

/* ── Input area ──────────────────────────────────────────────────────────────── */
.stTextArea textarea, .stTextInput input {
    background: var(--bg-2) !important;
    color: var(--text-1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
    font-size: 15px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(240,165,0,0.15) !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────────── */
.stButton > button {
    background: var(--accent) !important;
    color: #0d0f11 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: var(--font-display) !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    letter-spacing: 0.3px !important;
    padding: 10px 22px !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #ffb800 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(240,165,0,0.3) !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-1) !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-2) !important;
    font-family: var(--font-mono) !important;
    font-size: 12px !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    padding: 12px 20px !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: transparent !important;
}

/* ── Doc cards ───────────────────────────────────────────────────────────────── */
.doc-card {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.doc-name {
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--teal);
}
.doc-chunks {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-3);
}

/* ── Feedback buttons ────────────────────────────────────────────────────────── */
.fb-row { display: flex; gap: 8px; margin-top: 8px; }

/* ── Spinner ─────────────────────────────────────────────────────────────────── */
.thinking {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 16px 20px;
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 2px 12px 12px 12px;
    margin: 10px 60px 10px 0;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-2);
}
.dot-pulse { display: inline-flex; gap: 4px; }
.dot-pulse span {
    width: 5px; height: 5px; border-radius: 50%;
    background: var(--accent);
    animation: pulse 1.2s ease-in-out infinite;
}
.dot-pulse span:nth-child(2) { animation-delay: 0.2s; }
.dot-pulse span:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse { 0%,80%,100% { opacity:0.2; transform:scale(0.8); } 40% { opacity:1; transform:scale(1); } }

/* ── Selectbox / File uploader ───────────────────────────────────────────────── */
.stSelectbox > div > div {
    background: var(--bg-2) !important;
    border-color: var(--border) !important;
    color: var(--text-1) !important;
}
.stFileUploader {
    background: var(--bg-2) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 8px !important;
}

/* ── Metrics ─────────────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--bg-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 16px !important;
}
[data-testid="metric-container"] label { color: var(--text-2) !important; font-family: var(--font-mono) !important; font-size: 11px !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: var(--accent) !important; font-family: var(--font-display) !important; }

/* ── Expander ────────────────────────────────────────────────────────────────── */
details {
    background: var(--bg-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 2px 12px !important;
    margin: 4px 0 !important;
}
summary { color: var(--text-2) !important; font-family: var(--font-mono) !important; font-size: 12px !important; cursor: pointer !important; }

/* ── Scrollbar ───────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-0); }
::-webkit-scrollbar-thumb { background: var(--bg-3); border-radius: 3px; }

/* ── Divider ─────────────────────────────────────────────────────────────────── */
hr { border-color: var(--border) !important; }

/* ── Alert / info boxes ───────────────────────────────────────────────────────── */
.stAlert {
    background: var(--bg-2) !important;
    border-color: var(--border) !important;
    color: var(--text-1) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = set()


# ── API helpers ────────────────────────────────────────────────────────────────
def api_get(path: str):
    try:
        r = httpx.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def api_post(path: str, data: dict | None = None, files=None):
    try:
        if files:
            r = httpx.post(f"{API_BASE}{path}", files=files, timeout=60)
        else:
            r = httpx.post(f"{API_BASE}{path}", json=data, timeout=90)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def check_api_health():
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200, r.json()
    except Exception:
        return False, {}


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="docmind-header">
        <div>
            <div class="docmind-logo">⬡ DocMind</div>
            <div class="docmind-tagline">RAG · LangGraph · Self-Corrective</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Health check
    healthy, health_data = check_api_health()
    if healthy:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
            <div style="width:8px;height:8px;border-radius:50%;background:#4ade80;"></div>
            <span style="font-family:var(--font-mono);font-size:11px;color:#9b9890;">API ONLINE</span>
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        col1.metric("Documents", health_data.get("documents_indexed", "—"))
        col2.metric("Web Search", "ON" if health_data.get("web_search_enabled") else "OFF")
    else:
        st.error("⚠ API offline. Run: `uvicorn app.main:app --reload`")

    st.markdown("---")

    # Session control
    st.markdown(f"**Session:** `{st.session_state.session_id[:16]}…`")
    if st.button("New Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = f"session_{int(time.time())}"
        st.session_state.feedback_given = set()
        api_post(f"/session/{st.session_state.session_id}", {})
        st.rerun()

    st.markdown("---")

    # Settings
    st.markdown("**Settings**")
    show_meta = st.toggle("Show answer metadata", value=True)
    show_rewritten = st.toggle("Show rewritten query", value=False)

    st.markdown("---")
    st.markdown("""
    <div style="font-family:var(--font-mono);font-size:10px;color:var(--text-3);line-height:1.8;">
    STACK<br>
    LangGraph · ChromaDB<br>
    Groq · FastAPI<br>
    sentence-transformers<br><br>
    NODES<br>
    Query Analysis<br>
    Retrieval<br>
    Web Search (fallback)<br>
    Grading (self-corrective)<br>
    Generation<br>
    Hallucination Check
    </div>
    """, unsafe_allow_html=True)


# ── Main area ──────────────────────────────────────────────────────────────────
tab_chat, tab_docs, tab_ingest, tab_about = st.tabs([
    "✦ Chat", "◈ Documents", "⊕ Ingest", "◉ About"
])

# ─────────────────── TAB: CHAT ───────────────────────────────────────────────
with tab_chat:
    # Render chat history
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f'<div class="msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            data = msg.get("data", {})

            # Format answer — convert **bold** and `code` minimally
            answer_html = msg["content"].replace("\n", "<br>")

            # Build badge row
            badges = ""
            qtype = data.get("query_type", "")
            if qtype:
                badges += f'<span class="badge badge-type">{qtype}</span>'

            h_score = data.get("hallucination_score", "")
            if h_score == "supported":
                badges += '<span class="badge badge-ok">✓ grounded</span>'
            elif h_score == "unsupported":
                badges += '<span class="badge badge-warn">⚠ may hallucinate</span>'

            if data.get("used_web_search"):
                badges += '<span class="badge badge-web">⊕ web search</span>'

            retries = data.get("retry_count", 0)
            if retries > 0:
                badges += f'<span class="badge badge-retry">↺ {retries} retri{"es" if retries>1 else "y"}</span>'

            sources = data.get("sources", [])
            for s in sources[:4]:
                badges += f'<span class="badge badge-source">{s[:30]}</span>'

            meta_html = f'<div class="meta-row">{badges}</div>' if badges and show_meta else ""

            rewritten_html = ""
            if show_rewritten and data.get("rewritten_question"):
                rq = data["rewritten_question"]
                rewritten_html = f'<div style="font-family:var(--font-mono);font-size:11px;color:var(--text-3);margin-bottom:10px;">↳ searched: {rq}</div>'

            st.markdown(
                f'<div class="msg-assistant">{rewritten_html}{answer_html}{meta_html}</div>',
                unsafe_allow_html=True
            )

            # Feedback buttons (once per message)
            fb_key = f"fb_{i}"
            if fb_key not in st.session_state.feedback_given and i > 0:
                col_up, col_down, col_space = st.columns([1, 1, 8])
                with col_up:
                    if st.button("👍", key=f"up_{i}", help="Good answer"):
                        api_post("/feedback", {
                            "question": st.session_state.messages[i-1]["content"],
                            "answer": msg["content"],
                            "rating": "thumbs_up",
                            "session_id": st.session_state.session_id,
                        })
                        st.session_state.feedback_given.add(fb_key)
                        st.rerun()
                with col_down:
                    if st.button("👎", key=f"dn_{i}", help="Poor answer"):
                        api_post("/feedback", {
                            "question": st.session_state.messages[i-1]["content"],
                            "answer": msg["content"],
                            "rating": "thumbs_down",
                            "session_id": st.session_state.session_id,
                        })
                        st.session_state.feedback_given.add(fb_key)
                        st.rerun()

    # Empty state
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:48px;margin-bottom:16px;">⬡</div>
            <div style="font-family:var(--font-display);font-size:22px;font-weight:700;color:var(--accent);margin-bottom:8px;">DocMind Ready</div>
            <div style="font-family:var(--font-body);font-size:14px;color:var(--text-3);max-width:360px;margin:0 auto;line-height:1.7;">
                Ask anything about your indexed documentation. I'll retrieve, grade, and generate a grounded answer.
            </div>
            <div style="margin-top:28px;display:flex;flex-wrap:wrap;gap:8px;justify-content:center;">
                <div style="background:var(--bg-2);border:1px solid var(--border);border-radius:8px;padding:8px 14px;font-size:13px;color:var(--text-2);cursor:pointer;">How do I define a Pydantic model?</div>
                <div style="background:var(--bg-2);border:1px solid var(--border);border-radius:8px;padding:8px 14px;font-size:13px;color:var(--text-2);">What is LCEL in LangChain?</div>
                <div style="background:var(--bg-2);border:1px solid var(--border);border-radius:8px;padding:8px 14px;font-size:13px;color:var(--text-2);">How does ChromaDB cosine search work?</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Input
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        col_inp, col_btn = st.columns([6, 1])
        with col_inp:
            question = st.text_input(
                "question",
                placeholder="Ask a question about your documentation…",
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button("Ask →", use_container_width=True)

    if submitted and question.strip():
        if not healthy:
            st.error("API is offline. Please start the FastAPI server first.")
        else:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": question})

            # Call API
            with st.spinner(""):
                st.markdown("""
                <div class="thinking">
                    <div class="dot-pulse"><span></span><span></span><span></span></div>
                    Retrieving · Grading · Generating…
                </div>
                """, unsafe_allow_html=True)

                result = api_post("/query", {
                    "question": question,
                    "session_id": st.session_state.session_id,
                })

            if "error" in result:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"⚠ Error: {result['error']}",
                    "data": {},
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "data": result,
                })
            st.rerun()


# ─────────────────── TAB: DOCUMENTS ──────────────────────────────────────────
with tab_docs:
    st.markdown("### Indexed Documents")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if st.button("↻ Refresh", key="refresh_docs"):
        st.rerun()

    docs_data = api_get("/documents")
    if "error" in docs_data:
        st.error(f"Could not fetch documents: {docs_data['error']}")
    else:
        docs = docs_data.get("documents", [])
        if not docs:
            st.info("No documents indexed yet. Go to the Ingest tab to add some.")
        else:
            col1, col2 = st.columns(2)
            col1.metric("Total Documents", docs_data.get("total_documents", 0))
            col2.metric("Total Chunks", docs_data.get("total_chunks", 0))
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

            for doc in docs:
                col_name, col_chunks, col_del = st.columns([5, 2, 1])
                with col_name:
                    st.markdown(f'<div style="font-family:var(--font-mono);font-size:13px;color:var(--teal);padding:12px 0;">{doc["name"]}</div>', unsafe_allow_html=True)
                with col_chunks:
                    st.markdown(f'<div style="font-family:var(--font-mono);font-size:11px;color:var(--text-3);padding:14px 0;">{doc["chunks"]} chunks</div>', unsafe_allow_html=True)
                with col_del:
                    if st.button("✕", key=f"del_{doc['name']}", help=f"Delete {doc['name']}"):
                        result = httpx.delete(f"{API_BASE}/documents/{doc['name']}", timeout=10)
                        if result.status_code == 200:
                            st.success(f"Deleted {doc['name']}")
                            st.rerun()
                        else:
                            st.error("Delete failed")
                st.markdown('<hr style="margin:0;border-color:var(--border);">', unsafe_allow_html=True)


# ─────────────────── TAB: INGEST ─────────────────────────────────────────────
with tab_ingest:
    st.markdown("### Add Documents")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    ingest_tab1, ingest_tab2 = st.tabs(["Upload File", "From URL"])

    with ingest_tab1:
        uploaded = st.file_uploader(
            "Upload a document",
            type=["md", "txt", "html", "htm", "py", "rst"],
            help="Supported: Markdown, plain text, HTML, Python, RST",
        )
        if uploaded and st.button("Ingest File →", key="ingest_file"):
            with st.spinner("Chunking and embedding…"):
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "text/plain")}
                result = api_post("/ingest", files=files)
            if "error" in result:
                st.error(f"Failed: {result['error']}")
            else:
                st.success(f"✓ {result['message']} — {result['chunks_created']} chunks created")

    with ingest_tab2:
        url = st.text_input("URL", placeholder="https://docs.example.com/guide")
        if url and st.button("Ingest URL →", key="ingest_url"):
            with st.spinner(f"Fetching and indexing {url}…"):
                result = api_post(f"/ingest/url?url={url}", {})
            if "error" in result:
                st.error(f"Failed: {result['error']}")
            else:
                st.success(f"✓ {result['message']} — {result['chunks_created']} chunks created")


# ─────────────────── TAB: ABOUT ──────────────────────────────────────────────
with tab_about:
    st.markdown("""
    ### DocMind — RAG Technical Documentation Assistant

    **Architecture Overview**
    """)

    st.markdown("""
    <div style="background:var(--bg-2);border:1px solid var(--border);border-radius:12px;padding:20px;font-family:var(--font-mono);font-size:12px;line-height:2;color:var(--text-2);">
    USER QUESTION<br>
    &nbsp;&nbsp;&nbsp;&nbsp;↓<br>
    <span style="color:var(--accent);">[NODE 1]</span> Query Analysis &nbsp;→ rewrite + classify (conceptual/how-to/troubleshooting/api-ref)<br>
    &nbsp;&nbsp;&nbsp;&nbsp;↓<br>
    <span style="color:var(--accent);">[NODE 2]</span> Retrieval &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ ChromaDB cosine similarity, top-5 chunks<br>
    &nbsp;&nbsp;&nbsp;&nbsp;↓<br>
    <span style="color:var(--accent);">[NODE 3]</span> Grading &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ LLM judges each chunk: relevant / irrelevant<br>
    &nbsp;&nbsp;&nbsp;&nbsp;↓ (conditional routing)<br>
    &nbsp;&nbsp;&nbsp;&nbsp;├─ relevant docs found &nbsp;→ <span style="color:var(--green);">Generation → Hallucination Check → ✓</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;├─ no docs, retry &lt; 3 &nbsp;→ <span style="color:var(--accent);">rewrite query → retry loop</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;├─ tavily key set &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ <span style="color:#a78bfa;">Web Search fallback → Grading</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;└─ retries exhausted &nbsp;&nbsp;→ <span style="color:var(--red);">Fallback ("I don't know")</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""

    **Key Design Decisions**

    | Decision | Choice | Reason |
    |---|---|---|
    | LLM | Groq Llama3-8b | Free tier, very fast inference |
    | Embeddings | all-MiniLM-L6-v2 | No API key, 80MB, strong on technical English |
    | Vector DB | ChromaDB (cosine) | Local, zero-config, cosine space for text |
    | Chunking | Paragraph-aware, 512 chars, 64 overlap | Preserves natural doc structure |
    | Grading | Per-chunk LLM binary classification | Removes noise before generation |
    | Hallucination | Post-generation LLM verification (Self-RAG) | Flags unsupported claims |
    | Web Fallback | Tavily (1000 free/month) | AI-optimized search results |
    | Memory | In-process dict keyed by session_id | Simple; swap for Redis in prod |

    **What I'd improve with more time**
    - Reranking with a cross-encoder (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`)
    - Persistent feedback → fine-tuning loop
    - Streaming responses via SSE
    - Multi-tenant auth with JWT
    - Evaluation suite with RAGAS metrics
    """)
