import streamlit as st
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from client.api_client import InterviewCoPilotClient

st.set_page_config(page_title="Interview Co-Pilot", page_icon="🤖", layout="wide")

st.title("🤖 Interview Co-Pilot")
st.markdown("Multi-agent system for interview preparation")

# Initialize client
@st.cache_resource
def get_client():
    return InterviewCoPilotClient(base_url="http://localhost:8000")

client = get_client()

# Sidebar
with st.sidebar:
    st.header("Session Management")
    user_id = st.text_input("User ID", "demo_user")
    
    if st.button("Create New Session"):
        with st.spinner("Creating session..."):
            session = asyncio.run(client.create_session(user_id))
            st.session_state['session_id'] = session['session_id']
            st.success(f"Session created: {session['session_id'][:8]}...")

# Main content
tab1, tab2, tab3 = st.tabs(["📄 Job Description", "💻 Mock Interview", "📊 Progress"])

with tab1:
    st.header("Upload Job Description")
    job_title = st.text_input("Job Title", "Senior Software Engineer")
    company_name = st.text_input("Company Name", "TechCorp")
    jd_text = st.text_area("Job Description", height=200)
    
    if st.button("Run Research"):
        if 'session_id' in st.session_state:
            with st.spinner("Running research agent..."):
                result = asyncio.run(client.run_research(
                    st.session_state['session_id'],
                    jd_text,
                    company_name
                ))
                st.success("Research complete!")
                st.json(result)

with tab2:
    st.header("Mock Technical Interview")
    # Add interview UI here

with tab3:
    st.header("Your Progress")
    if st.button("Refresh Progress"):
        progress = asyncio.run(client.get_user_progress(user_id))
        st.metric("Total Sessions", progress['total_sessions'])
        st.metric("Success Rate", f"{progress['success_rate']*100:.1f}%")