"""
Interview Co-Pilot Streamlit UI
Complete implementation with all features
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import traceback

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from client.api_client import InterviewCoPilotSyncClient
from ui.components import (
    code_editor_component,
    question_display_component,
    evaluation_result_component,
    progress_chart_component,
    session_list_component
)

# Page configuration
st.set_page_config(
    page_title="Interview Co-Pilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fee;
        border-left: 4px solid #f00;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #efe;
        border-left: 4px solid #0f0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'current_questions' not in st.session_state:
    st.session_state.current_questions = []
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = {}

# Initialize client
@st.cache_resource
def get_client():
    """Get or create API client"""
    try:
        return InterviewCoPilotSyncClient(base_url="http://localhost:8000", timeout=60.0)
    except Exception as e:
        st.error(f"Failed to initialize API client: {e}")
        return None

client = get_client()

# Sidebar - Session Management
with st.sidebar:
    st.header("🤖 Interview Co-Pilot")
    st.markdown("---")
    
    st.subheader("Session Management")
    user_id = st.text_input("User ID", value="demo_user", key="user_id")
    
    # Create new session
    if st.button("➕ Create New Session", use_container_width=True):
        if client:
            with st.spinner("Creating session..."):
                try:
                    result = client.create_session(user_id)
                    st.session_state.session_id = result.get('session_id')
                    st.session_state.current_questions = []
                    st.session_state.current_question_index = 0
                    st.session_state.evaluation_results = {}
                    st.success(f"✅ Session created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create session: {e}")
    
    st.markdown("---")
    
    # Load user sessions
    if user_id and client:
        with st.spinner("Loading sessions..."):
            try:
                # Get user progress which includes session info
                progress = client.get_user_progress(user_id)
                if progress:
                    sessions = progress.get('sessions', [])
                    if sessions:
                        st.subheader("Your Sessions")
                        for session in sessions[:5]:  # Show last 5
                            session_id = session.get('session_id', '')
                            if st.button(
                                f"📝 {session_id[:8]}...",
                                key=f"load_{session_id}",
                                use_container_width=True
                            ):
                                st.session_state.session_id = session_id
                                st.rerun()
            except Exception as e:
                st.error(f"Error loading sessions: {e}")
    
    st.markdown("---")
    
    # Current session info
    if st.session_state.session_id:
        st.info(f"**Current Session:**\n`{st.session_state.session_id[:16]}...`")
        if st.button("🔄 Refresh Session", use_container_width=True):
            st.rerun()

# Main content
st.title("🤖 Interview Co-Pilot")
st.markdown("Multi-agent system for interview preparation with AI-powered feedback")

# Check if session exists
if not st.session_state.session_id:
    st.warning("⚠️ Please create a session to get started!")
    st.info("Use the sidebar to create a new session or select an existing one.")
    st.stop()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 Job Description & Research",
    "💻 Mock Interview",
    "📊 Progress & Analytics",
    "⚙️ Session Details"
])

# ========== TAB 1: Job Description & Research ==========
with tab1:
    st.header("📄 Job Description & Research")
    
    col1, col2 = st.columns(2)
    
    with col1:
        job_title = st.text_input("Job Title", value="Senior Software Engineer", key="job_title")
        company_name = st.text_input("Company Name", value="TechCorp", key="company_name")
    
    with col2:
        st.markdown("### Research Options")
        research_enabled = st.checkbox("Enable Research Agent", value=True)
        use_llm_parsing = st.checkbox("Use Advanced JD Parsing", value=True)
    
    jd_text = st.text_area(
        "Job Description",
        height=300,
        placeholder="Paste the job description here...",
        key="jd_text"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔍 Run Research", use_container_width=True, type="primary"):
            if not jd_text:
                st.error("Please enter a job description")
            elif client:
                with st.spinner("🔍 Researching company and interview process..."):
                    try:
                        result = client.run_research(
                            st.session_state.session_id,
                            jd_text,
                            company_name
                        )
                        
                        st.success("✅ Research complete!")
                        
                        # Display research results
                        with st.expander("📊 Research Results", expanded=True):
                            if isinstance(result, dict):
                                st.json(result)
                            else:
                                st.write(result)
                    except Exception as e:
                        st.error(f"Research failed: {e}")
    
    # Display parsed JD if available
    if jd_text and use_llm_parsing:
        with st.expander("📋 Parsed Job Description"):
            st.info("JD parsing would be displayed here (requires JD Parser integration)")

# ========== TAB 2: Mock Interview ==========
with tab2:
    st.header("💻 Mock Technical Interview")
    
    # Interview setup
    with st.expander("⚙️ Interview Settings", expanded=not st.session_state.current_questions):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            difficulty = st.selectbox(
                "Difficulty",
                options=["easy", "medium", "hard"],
                index=1,
                key="difficulty"
            )
        
        with col2:
            num_questions = st.number_input(
                "Number of Questions",
                min_value=1,
                max_value=10,
                value=3,
                key="num_questions"
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Start Interview", use_container_width=True, type="primary"):
                if client:
                    with st.spinner("🎯 Selecting questions..."):
                        try:
                            result = client.start_mock_interview(
                                st.session_state.session_id,
                                difficulty,
                                num_questions
                            )
                            
                            if result and result.get('questions'):
                                st.session_state.current_questions = result.get('questions', [])
                                st.session_state.current_question_index = 0
                                st.session_state.evaluation_results = {}
                                st.success(f"✅ Interview started with {len(st.session_state.current_questions)} questions!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to start interview: {e}")
    
    # Display current question
    if st.session_state.current_questions:
        total_questions = len(st.session_state.current_questions)
        current_idx = st.session_state.current_question_index
        
        # Question navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀️ Previous", disabled=current_idx == 0):
                st.session_state.current_question_index = max(0, current_idx - 1)
                st.rerun()
        
        with col2:
            st.markdown(f"<center><b>Question {current_idx + 1} of {total_questions}</b></center>", unsafe_allow_html=True)
        
        with col3:
            if st.button("Next ▶️", disabled=current_idx >= total_questions - 1):
                st.session_state.current_question_index = min(total_questions - 1, current_idx + 1)
                st.rerun()
        
        st.markdown("---")
        
        # Display question
        current_question = st.session_state.current_questions[current_idx]
        question_display_component(current_question, current_idx + 1)
        
        st.markdown("---")
        
        # Code editor
        st.markdown("### 💻 Your Solution")
        
        question_id = current_question.get('id', f'q{current_idx}')
        editor_key = f"editor_{question_id}"
        
        # Get saved code or default
        default_code = st.session_state.get(f"code_{question_id}", "")
        
        editor_result = code_editor_component(
            default_code=default_code,
            language="python",
            height=400,
            key=editor_key
        )
        
        # Save code to session state
        st.session_state[f"code_{question_id}"] = editor_result["code"]
        
        # Submit button
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("✅ Submit Code", use_container_width=True, type="primary"):
                if not editor_result["code"].strip():
                    st.error("Please write some code before submitting!")
                elif client:
                    with st.spinner("🔍 Evaluating your code..."):
                        try:
                            result = client.submit_code(
                                st.session_state.session_id,
                                question_id,
                                editor_result["code"],
                                editor_result["language"]
                            )
                            
                            st.session_state.evaluation_results[question_id] = result
                            st.success("✅ Code submitted and evaluated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to submit code: {e}")
        
        # Display evaluation results
        if question_id in st.session_state.evaluation_results:
            st.markdown("---")
            st.markdown("### 📊 Evaluation Results")
            evaluation_result_component(st.session_state.evaluation_results[question_id])
    
    else:
        st.info("👆 Start an interview using the settings above to begin!")

# ========== TAB 3: Progress & Analytics ==========
with tab3:
    st.header("📊 Progress & Analytics")
    
    if user_id and client:
        with st.spinner("Loading your progress..."):
            try:
                progress = client.get_user_progress(user_id)
                
                if progress:
                    progress_chart_component(progress)
                    
                    # Session history
                    st.markdown("---")
                    st.subheader("Session History")
                    
                    sessions = progress.get('sessions', [])
                    if sessions:
                        import pandas as pd
                        session_df = pd.DataFrame([
                            {
                                'Session ID': s.get('session_id', '')[:8],
                                'State': s.get('state', ''),
                                'Created': s.get('created_at', '')[:10] if s.get('created_at') else '',
                                'Score': s.get('average_score', 0) * 100 if s.get('average_score') else 0
                            }
                            for s in sessions[:10]
                        ])
                        st.dataframe(session_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No session history available yet.")
                else:
                    st.error("Failed to load progress data.")
            except Exception as e:
                st.error(f"Failed to load progress: {e}")
    else:
        st.warning("Please enter a User ID to view progress.")

# ========== TAB 4: Session Details ==========
with tab4:
    st.header("⚙️ Session Details")
    
    if st.session_state.session_id and client:
        # Get session summary
        if st.button("🔄 Refresh Session Details"):
            st.rerun()
        
        with st.spinner("Loading session details..."):
            try:
                summary = client.get_session_summary(st.session_state.session_id)
                
                if summary:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Session ID", st.session_state.session_id[:16] + "...")
                        st.metric("State", summary.get('state', 'unknown'))
                        st.metric("Total Questions", summary.get('total_questions', 0))
                    
                    with col2:
                        st.metric("Average Score", f"{summary.get('average_score', 0) * 100:.1f}%")
                        st.metric("Questions Completed", summary.get('questions_completed', 0))
                        st.metric("Created", summary.get('created_at', '')[:10] if summary.get('created_at') else 'N/A')
                    
                    # Session artifacts
                    artifacts = summary.get('artifacts', [])
                    if artifacts:
                        st.markdown("### Session Artifacts")
                        for artifact in artifacts:
                            with st.expander(f"📎 {artifact.get('type', 'Unknown')}"):
                                st.json(artifact.get('payload', {}))
                    
                    # Full session data
                    with st.expander("📋 Full Session Data"):
                        st.json(summary)
                else:
                    st.error("Failed to load session summary.")
            except Exception as e:
                st.error(f"Failed to load session summary: {e}")
    else:
        st.info("No active session. Create a session to see details here.")

# Footer
st.markdown("---")
st.markdown(
    "<center><small>🤖 Interview Co-Pilot v1.0 | Built with Streamlit</small></center>",
    unsafe_allow_html=True
)
