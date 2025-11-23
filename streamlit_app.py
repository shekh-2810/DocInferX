# streamlit_app.py
import streamlit as st
import os
import time
import uuid
from library.manager import DocumentManager
from embed.vectorizer import VectorStore
from rag.pipeline import RAGPipeline
import config


# PAGE CONFIG

st.set_page_config(
    page_title="DocInferX",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# FULLSCREEN LOADING SCREEN (CSS FADE OUT)

st.markdown("""
<style>
#loading-screen {
    position: fixed;
    width: 100vw;
    height: 100vh;
    background: #000;
    top: 0;
    left: 0;
    z-index: 99999;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    animation: fadeOut 1s ease-in-out forwards;
    animation-delay: 1.6s;
}

@keyframes fadeOut {
    0% { opacity: 1; }
    100% { opacity: 0; visibility: hidden; }
}

.loader {
    border: 6px solid #1f1f1f;
    border-top: 6px solid #00B4FF;
    border-radius: 50%;
    width: 70px;
    height: 70px;
    animation: spin 1.2s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loading-text {
    margin-top: 18px;
    font-size: 22px;
    font-weight: 700;
    color: #00B4FF;
    font-family: monospace;
    text-shadow: 0px 0px 18px #00B4FF;
}
</style>

<div id="loading-screen">
    <div class="loader"></div>
    <div class="loading-text">Launching DocInferX...</div>
</div>
""", unsafe_allow_html=True)



# BACKEND SPINNER (model load)

with st.spinner("Initializing DocInferX... Loading models, OCR engine, vector store..."):
    time.sleep(1.2)



# MAIN UI STYLE

st.markdown("""
<style>
html, body { background-color: #0A0C10 !important; }

.block-container { padding-top: 1.5rem; }

section[data-testid="stSidebar"] {
    background: rgba(20,25,32,0.75);
    border-right: 1px solid rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
}

.sidebar-title { font-size: 28px; font-weight: 800; text-align: center; color: #00B4FF; }

div[data-testid="stRadio"] > div {
    background: rgba(255,255,255,0.03);
    padding: 12px 10px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06);
}
div[data-testid="stRadio"] label { font-size: 16px; font-weight: 550; padding: 6px 8px; }
div[data-testid="stRadio"] input:checked + div {
    background: rgba(0,180,255,0.15);
    border: 1px solid #00B4FF;
    box-shadow: 0 0 14px #009fe6;
}

.stButton > button {
    background: #00B4FF !important;
    color: black !important;
    border-radius: 10px;
    font-weight: 700;
    border: none;
}
.stButton > button:hover {
    background: #29C5FF !important;
    box-shadow: 0 0 12px #009fe6;
}

.answer-bubble {
    padding: 18px 22px;
    background: rgba(255,255,255,0.04);
    border-left: 3px solid #00B4FF;
    border-radius: 10px;
}

.doc-card {
    background: rgba(255,255,255,0.05);
    padding: 18px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 16px;
}
.doc-card:hover { border: 1px solid #00B4FF; box-shadow: 0 0 12px #00AEEF55; }
</style>
""", unsafe_allow_html=True)



# CACHED LOADERS

@st.cache_resource
def load_vector_store():
    return VectorStore(
        model_name=config.EMBED_MODEL_NAME,
        index_path=config.INDEX_PATH,
        meta_path=config.META_PATH
    )

@st.cache_resource
def load_rag(_vs):   
    return RAGPipeline(_vs)

@st.cache_resource
def load_doc_manager():
    return DocumentManager(config.LIBRARY_META_PATH)


# Init
vs = load_vector_store()
rag = load_rag(vs)
dm = load_doc_manager()



# SIDEBAR

st.sidebar.markdown('<div class="sidebar-title">⚡ DocInferX</div>', unsafe_allow_html=True)
st.sidebar.markdown("Local AI Document Engine.")

menu = st.sidebar.radio("", ["Upload Document", "Chat", "Library"], index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Settings")
st.sidebar.caption(f"Embedding model: `{config.EMBED_MODEL_NAME}`")
st.sidebar.caption(f"Generator model: `{config.GENERATOR_MODEL}`")


# UPLOAD DOCUMENT

if menu == "Upload Document":
    st.markdown("## 📤 Upload Document")

    uploaded = st.file_uploader("Upload PDF or Image:", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded:
        save_path = os.path.join(config.UPLOAD_DIR, uploaded.name)
        with open(save_path, "wb") as f:
            f.write(uploaded.read())

        st.success("File uploaded.")
        doc_id = str(uuid.uuid4())

        with st.spinner("Processing document..."):
            progress = st.progress(0)
            chunks = dm.ingest_document(save_path, doc_id)
            progress.progress(50)
            stored = vs.add_with_return(chunks, doc_id, uploaded.name, len(chunks))
            progress.progress(100)

        vs.save()
        st.success(f"Indexed {len(stored)} chunks.")


# CHAT

elif menu == "Chat":
    st.markdown("## 💬 Chat With Your Documents")

    query = st.text_input("Ask anything:")

    if st.button("Search") and query:
        with st.spinner("Processing..."):
            progress = st.progress(0)
            answer = rag.query(query)
            progress.progress(100)

        st.markdown(f'<div class="answer-bubble">{answer}</div>', unsafe_allow_html=True)


# LIBRARY

elif menu == "Library":
    st.markdown("## 📚 Your Library")

    docs = dm.list_documents()

    if not docs:
        st.warning("No documents uploaded.")
    else:
        for d in docs:
            st.markdown(
                f"""
                <div class="doc-card">
                    <h3>{d['name']}</h3>
                    <p><b>ID:</b> {d['doc_id']}</p>
                    <p><b>Pages:</b> {d['pages']}</p>
                    <p><b>Chunks:</b> {d['chunks']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
