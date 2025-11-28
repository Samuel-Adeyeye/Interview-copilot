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
        company_name = st.text_input("Company Name", value="TechCorp", key="research_company_name")
    
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
    run_research = False
    with col1:
        if st.button("🔍 Run Research", use_container_width=True, type="primary"):
            run_research = True
            
    # Create a placeholder for results below the button/columns
    results_area = st.empty()
    
    if run_research:
        if not jd_text:
            st.error("Please enter a job description")
        elif client:
            try:
                # Stream into the results area using the expander style
                with results_area.container():
                    with st.expander("📊 Research Results", expanded=True):
                        output_placeholder = st.empty()
                        full_response = ""
                        
                        with st.spinner("🔍 Researching company and interview process..."):
                            # Use streaming endpoint
                            for chunk in client.run_research_streaming(
                                session_id=st.session_state.session_id,
                                company_name=company_name,
                                job_description=jd_text,
                                user_id=st.session_state.get("user_id", "demo_user")
                            ):
                                full_response += chunk
                                # Update display in real-time
                                output_placeholder.markdown(full_response)
                
                st.success("✅ Research complete!")
                
                # Store in session state
                st.session_state["research_results"] = full_response
                
            except Exception as e:
                st.error(f"Research failed: {e}")
    
    # Display research results if available (and not currently running, or to overwrite/persist)
    if "research_results" in st.session_state and st.session_state["research_results"]:
        with results_area.container():
            with st.expander("📊 Research Results", expanded=True):
                st.markdown(st.session_state["research_results"])
    
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
            company_name = st.text_input(
                "Company Name (Optional)",
                placeholder="e.g., Google, Meta",
                help="Leave empty for general questions, or specify a company for tailored questions",
                key="interview_company_name"
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Start Interview", use_container_width=True, type="primary"):
            if client:
                # Create placeholder for streaming output
                output_placeholder = st.empty()
                full_response = ""
                
                try:
                    with st.spinner("🎯 Selecting questions..."):
                        # Use streaming endpoint
                        for chunk in client.start_mock_interview_streaming(
                            session_id=st.session_state.session_id,
                            user_id=st.session_state.get("user_id", "demo_user"),
                            difficulty=difficulty,
                            num_questions=num_questions,
                            job_description=st.session_state.get("research_results", ""),
                            company_name=company_name if company_name else None
                        ):
                            full_response += chunk
                            # Update display in real-time
                            output_placeholder.markdown(f"**Generating Questions:**\n\n{full_response}")
                    
                    # Parse questions from response (assuming they're in the text)
                    # For now, store the full response
                    st.session_state["interview_questions"] = full_response
                    st.success(f"✅ Interview questions generated!")
                    
                except Exception as e:
                    st.error(f"Failed to start interview: {e}")
    
    # Display interview questions if available
    if "interview_questions" in st.session_state and st.session_state["interview_questions"]:
        with st.expander("💡 Interview Questions", expanded=True):
            st.markdown(st.session_state["interview_questions"])
            
            st.markdown("---")
            st.markdown("### 📝 Submit Your Solution")
            
            # Code editor for submission
            code_input = st.text_area(
                "Write your solution here:",
                height=300,
                key="code_submission",
                help="Paste your code solution here. Make sure to specify which question you are solving."
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                language = st.selectbox(
                    "Language:",
                    ["python", "javascript", "java", "cpp"],
                    key="code_language"
                )
            
            with col2:
                question_id = st.text_input(
                    "Question ID (e.g., q1):",
                    key="question_id_input",
                    help="Enter the ID of the question you are solving (e.g., q1, q2)"
                )
            
            submit_code = False
            if st.button("✅ Submit Code", type="primary"):
                submit_code = True
            
            # Create a placeholder for results below the button
            eval_results_area = st.empty()
            
            if submit_code:
                if not code_input or not question_id:
                    st.error("Please provide both code and question ID.")
                elif client:
                    try:
                        # Stream into the results area using the expander style
                        with eval_results_area.container():
                            with st.expander("📊 Evaluation Results", expanded=True):
                                eval_placeholder = st.empty()
                                full_eval = ""
                                
                                with st.spinner("🧪 Evaluating code..."):
                                    for chunk in client.submit_code_streaming(
                                        session_id=st.session_state.session_id,
                                        user_id=st.session_state.get("user_id", "demo_user"),
                                        question_id=question_id,
                                        code=code_input,
                                        language=language
                                    ):
                                        full_eval += chunk
                                        eval_placeholder.markdown(full_eval)
                        
                        st.success("✅ Evaluation complete!")
                        st.session_state["evaluation_results"] = full_eval
                        
                    except Exception as e:
                        st.error(f"Evaluation failed: {e}")
    
    # Display evaluation results if available (and not currently running, or to overwrite/persist)
    if "evaluation_results" in st.session_state and st.session_state["evaluation_results"]:
        with eval_results_area.container():
            with st.expander("📊 Evaluation Results", expanded=True):
                st.markdown(st.session_state["evaluation_results"])
    
    # Prompt to start if no questions generated yet
    if "interview_questions" not in st.session_state or not st.session_state["interview_questions"]:
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
