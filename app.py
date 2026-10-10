from pathlib import Path

import streamlit as st

from rag_sql_router import db
from rag_sql_router.agent import RouterAgent
from rag_sql_router.config import settings
from rag_sql_router.rag import DocumentStore

st.set_page_config(page_title="RAG-SQL Router", page_icon="🧭")
st.title("RAG-SQL Router Agent")
st.caption("Routes each question to your documents, your database, or both.")


@st.cache_resource
def get_agent() -> RouterAgent:
    if not Path(settings.db_path).exists():
        db.seed()
    docs = DocumentStore()
    if not docs.count():
        docs.index_directory()
    return RouterAgent(docs)


agent = get_agent()

with st.sidebar:
    st.header("Schema")
    st.code(db.get_schema(), language="sql")
    st.markdown("**Try:** total quantity ordered per region / what is the refund window for electronics / how many orders were placed by Asha and what is the refund approval limit for sales reps")

if question := st.chat_input("Ask about sales data or company policy"):
    st.chat_message("user").markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Routing..."):
            result = agent.ask(question)
        labels = {"sql": "🗄️ Database", "rag": "📄 Documents", "both": "🔀 Database + Documents"}
        st.markdown(f"**Route:** {labels[result.route]}")
        st.markdown(result.answer)
        if result.sql:
            with st.expander("Generated SQL"):
                st.code(result.sql, language="sql")
                if result.rows:
                    st.dataframe([dict(zip(result.columns, r)) for r in result.rows])
                elif result.error:
                    st.error(result.error)
        if result.sources:
            with st.expander("Document sources"):
                for h in result.sources:
                    st.markdown(f"**{h.source}** (score {h.score:.2f})\n\n{h.text}")
