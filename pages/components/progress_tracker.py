# ui/components/progress_tracker.py
import streamlit as st
from typing import List, Dict

class ProcessingStage:
    UPLOAD = "Image Upload"
    OCR = "OCR Processing"
    GRADING = "Grading"
    FEEDBACK = "Feedback Generation"
    COMPLETE = "Complete"

def render_progress_tracker(
    current_file: str,
    total_files: int,
    processed_files: int,
    current_stages: Dict[str, str],  # filename -> current stage
    completed_stages: Dict[str, List[str]]  # filename -> list of completed stages
):
    """Render processing progress UI"""
    
    st.markdown("### 📊 Processing Status")
    
    # Show overall progress with percentage
    progress = processed_files / total_files if total_files > 0 else 0
    percentage = int(progress * 100)
    
    # Progress bar container
    progress_container = st.container()
    with progress_container:
        st.progress(progress)
        st.markdown(f"**Overall Progress:** {percentage}% ({processed_files}/{total_files} files)")
    
    # Current file status with spinner
    if current_file:
        st.info(f"🔄 Currently Processing: **{current_file}**")
    
    # Detailed status tracking
    with st.expander("📋 Detailed Status", expanded=True):
        # Show status for each file
        for filename, stage in current_stages.items():
            st.markdown("---")
            
            # File header with status
            status_color = "🟢" if stage == ProcessingStage.COMPLETE else "🔵"
            st.markdown(f"{status_color} **File: {filename}**")
            
            # Progress indicators in a grid
            stages = [
                ProcessingStage.UPLOAD,
                ProcessingStage.OCR,
                ProcessingStage.GRADING,
                ProcessingStage.FEEDBACK
            ]
            
            completed = completed_stages.get(filename, [])
            
            # Create columns for stage indicators
            cols = st.columns(len(stages))
            for i, s in enumerate(stages):
                with cols[i]:
                    if s in completed:
                        st.markdown(f"✅ {s}")
                    elif s == stage:
                        st.markdown(f"⏳ **{s}**")
                    else:
                        st.markdown(f"⬜ {s}")
            
            # Show stage-specific messages
            if stage == ProcessingStage.OCR:
                st.caption("Extracting text from image...")
            elif stage == ProcessingStage.GRADING:
                st.caption("Evaluating response...")
            elif stage == ProcessingStage.FEEDBACK:
                st.caption("Generating detailed feedback...")
            
            # Show completion status
            if ProcessingStage.COMPLETE in completed or stage == ProcessingStage.COMPLETE:
                st.success("✨ Processing Complete")
    
    # Show completion message
    if processed_files == total_files and total_files > 0:
        st.balloons()  # Add celebration effect
        st.success("🎉 All files processed successfully!")
        
        # Navigation options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Results", type="primary"):
                st.session_state.current_page = "Results"
                st.session_state.processing = False
                st.rerun()
        with col2:
            if st.button("📤 Process More"):
                st.session_state.processing = False
                st.rerun()
