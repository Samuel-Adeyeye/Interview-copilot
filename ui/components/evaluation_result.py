"""
Evaluation Result Display Component for Streamlit
"""

import streamlit as st
from typing import Dict, Any, List

def evaluation_result_component(evaluation: Dict[str, Any]):
    """
    Display code evaluation results
    
    Args:
        evaluation: Evaluation dictionary with scores, test results, feedback, etc.
    """
    # Overall score
    overall_score = evaluation.get('overall', 0.0)
    score_color = "green" if overall_score >= 0.8 else "orange" if overall_score >= 0.5 else "red"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Score", f"{overall_score * 100:.1f}%", delta=None)
    
    with col2:
        correctness = evaluation.get('correctness', 0.0)
        st.metric("Correctness", f"{correctness * 100:.1f}%")
    
    with col3:
        quality = evaluation.get('code_quality', 0.0)
        st.metric("Code Quality", f"{quality * 100:.1f}%")
    
    with col4:
        efficiency = evaluation.get('efficiency', 0.0)
        st.metric("Efficiency", f"{efficiency * 100:.1f}%")
    
    # Test results
    test_results = evaluation.get('test_results', [])
    if test_results:
        st.markdown("### Test Case Results")
        
        for i, test_result in enumerate(test_results, 1):
            passed = test_result.get('passed', False)
            status_icon = "✅" if passed else "❌"
            
            with st.expander(f"{status_icon} Test Case {i}", expanded=not passed):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Input:**")
                    st.code(test_result.get('input', ''), language="text")
                    st.markdown("**Expected:**")
                    st.code(test_result.get('expected', ''), language="text")
                
                with col2:
                    st.markdown("**Actual:**")
                    st.code(test_result.get('actual', ''), language="text")
                    if test_result.get('execution_time'):
                        st.caption(f"⏱️ Execution time: {test_result.get('execution_time'):.3f}s")
                    
                    if test_result.get('stderr'):
                        st.error(f"Error: {test_result.get('stderr')}")
    
    # Feedback and recommendations
    feedback = evaluation.get('feedback', '')
    recommendations = evaluation.get('recommendations', [])
    
    if feedback:
        st.markdown("### Feedback")
        st.info(feedback)
    
    if recommendations:
        st.markdown("### Recommendations")
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")
    
    # Status message
    status = evaluation.get('status', 'unknown')
    if status == 'success':
        st.success("🎉 All tests passed! Great job!")
    elif status == 'partial':
        st.warning("⚠️ Some tests passed. Keep working on it!")
    else:
        st.error("❌ Tests failed. Review the feedback and try again.")

