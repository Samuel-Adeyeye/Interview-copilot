"""
Progress Chart Component for Streamlit
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List

# Optional plotly import
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

def progress_chart_component(progress_data: Dict[str, Any]):
    """
    Display progress visualization charts
    
    Args:
        progress_data: Progress dictionary with scores, trends, etc.
    """
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sessions", progress_data.get('total_sessions', 0))
    
    with col2:
        success_rate = progress_data.get('success_rate', 0.0)
        st.metric("Success Rate", f"{success_rate * 100:.1f}%")
    
    with col3:
        avg_score = progress_data.get('average_score', 0.0)
        st.metric("Average Score", f"{avg_score * 100:.1f}%")
    
    with col4:
        improvement = progress_data.get('improvement_rate', 0.0)
        delta = f"+{improvement * 100:.1f}%" if improvement > 0 else f"{improvement * 100:.1f}%"
        st.metric("Improvement", delta)
    
    # Score trend chart
    scores = progress_data.get('scores', [])
    if len(scores) > 1:
        st.markdown("### Score Trend")
        df = pd.DataFrame({
            'Session': range(1, len(scores) + 1),
            'Score': scores
        })
        
        if PLOTLY_AVAILABLE:
            fig = px.line(
                df,
                x='Session',
                y='Score',
                title='Score Over Time',
                labels={'Score': 'Score (%)', 'Session': 'Session Number'}
            )
            fig.update_traces(line_color='#1f77b4', line_width=3)
            fig.update_layout(
                yaxis=dict(range=[0, 1], tickformat='.0%'),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Fallback to line chart using streamlit
            st.line_chart(df.set_index('Session'))
            st.info("💡 Install plotly for better charts: `pip install plotly`")
    
    # Skill breakdown (if available)
    skill_breakdown = progress_data.get('skill_breakdown', {})
    if skill_breakdown:
        st.markdown("### Skill Breakdown")
        skills_df = pd.DataFrame(list(skill_breakdown.items()), columns=['Skill', 'Score'])
        skills_df['Score'] = skills_df['Score'] * 100
        
        if PLOTLY_AVAILABLE:
            fig = px.bar(
                skills_df,
                x='Skill',
                y='Score',
                title='Performance by Skill',
                labels={'Score': 'Score (%)'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Fallback to bar chart
            st.bar_chart(skills_df.set_index('Skill'))
            st.info("💡 Install plotly for better charts: `pip install plotly`")
    
    # Trend indicator
    trend = progress_data.get('trend', 'stable')
    trend_icons = {
        'improving': '📈',
        'declining': '📉',
        'stable': '➡️',
        'no_data': '❓'
    }
    trend_messages = {
        'improving': 'Your performance is improving!',
        'declining': 'Your performance needs attention.',
        'stable': 'Your performance is stable.',
        'no_data': 'Not enough data to determine trend.'
    }
    
    st.info(f"{trend_icons.get(trend, '❓')} {trend_messages.get(trend, 'Unknown trend')}")

