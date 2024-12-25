# ui/pages/upload.py
import streamlit as st
import tempfile
import os
import json
from pathlib import Path
from services.storage import StorageService
from services.pipeline import ProcessingPipeline
from models.submission import Submission
from ui.components.progress_tracker import render_progress_tracker, ProcessingStage

def show_no_assignments_warning():
    """Display warning when no assignments exist"""
    st.warning(
        "No assignments found. Please create an assignment first in the Assignment Management section."
    )
    if st.button("Go to Assignment Management"):
        st.session_state.current_page = "Assignment Management"
        st.rerun()

def show_assignment_preview(assignment: dict):
    """Show selected assignment details"""
    with st.expander("Assignment Details", expanded=False):
        st.write("**Question:**")
        st.write(assignment['question_text'])
        
        st.write("**Rubric:**")
        rubric = (
            assignment['rubric_structure'] 
            if isinstance(assignment['rubric_structure'], dict)
            else json.loads(assignment['rubric_structure'])
        )
        
        for req in rubric['requirements']:
            st.write(f"- {req['text']} ({req['points']} points)")
            
        if rubric.get('metadata', {}).get('notes'):
            st.write("\n**Grading Notes:**")
            st.write(rubric['metadata']['notes'])

def save_uploaded_file(uploaded_file) -> str:
    """Save an uploaded file to a temporary directory"""
    try:
        # Create a temporary directory if it doesn't exist
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        # Create a unique filename
        file_path = temp_dir / f"{uploaded_file.name}"
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        return str(file_path)
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None

def show_upload_preview(uploaded_files):
    """Show preview of uploaded files"""
    for file in uploaded_files:
        st.image(file, caption=file.name, use_container_width=True)

def process_submissions(storage: StorageService, 
                       assignment: dict,
                       uploaded_files: list):
    """Process uploaded submissions"""
    try:
        # Initialize processing pipeline
        pipeline = ProcessingPipeline()
        
        # Process each file
        for i, file in enumerate(uploaded_files):
            try:
                # Update progress
                st.session_state.current_file = file.name
                st.session_state.processed_files = i
                st.session_state.current_stages[file.name] = ProcessingStage.UPLOAD
                st.session_state.completed_stages[file.name] = []
                
                # Save file temporarily
                temp_path = save_uploaded_file(file)
                if not temp_path:
                    continue
                
                # Mark upload complete
                st.session_state.completed_stages[file.name].append(ProcessingStage.UPLOAD)
                st.session_state.current_stages[file.name] = ProcessingStage.OCR
                
                # Define stage change callback
                def on_stage_change(stage: str, message: str):
                    # Map API stages to ProcessingStage
                    stage_map = {
                        "UPLOAD": ProcessingStage.UPLOAD,
                        "OCR": ProcessingStage.OCR,
                        "GRADING": ProcessingStage.GRADING,
                        "FEEDBACK": ProcessingStage.FEEDBACK,
                        "COMPLETE": ProcessingStage.COMPLETE
                    }
                    
                    if stage in stage_map:
                        # Mark previous stage as complete
                        if st.session_state.current_stages[file.name] != ProcessingStage.COMPLETE:
                            st.session_state.completed_stages[file.name].append(
                                st.session_state.current_stages[file.name]
                            )
                        
                        # Update current stage
                        st.session_state.current_stages[file.name] = stage_map[stage]
                
                # Extract student ID from filename
                student_id = Path(file.name).stem
                
                # Create and process submission
                result = pipeline.process_submission(
                    image_path=temp_path,
                    assignment_id=assignment['id'],
                    student_id=student_id,
                    on_stage_change=on_stage_change
                )
                
                # Update processed count
                if result:
                    st.session_state.processed_files += 1
                
                # Cleanup temp file
                os.remove(temp_path)
                
            except Exception as e:
                st.error(f"Error processing {file.name}: {str(e)}")
                continue
                
        # Clear current file when done
        st.session_state.current_file = None
            
    except Exception as e:
        st.error(f"Error in processing pipeline: {str(e)}")
    finally:
        # Cleanup temp directory
        temp_dir = Path("temp_uploads")
        if temp_dir.exists():
            for file in temp_dir.glob("*"):
                try:
                    file.unlink()
                except:
                    pass

def render_upload_page(storage: StorageService):
    st.header("Upload & Grade")
    
    # Initialize processing state
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'current_stages' not in st.session_state:
        st.session_state.current_stages = {}
    if 'completed_stages' not in st.session_state:
        st.session_state.completed_stages = {}
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = 0
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    
    try:
        # Get available assignments
        assignments = storage.list_assignments()
        if not assignments:
            show_no_assignments_warning()
            return
            
        # Create two columns for the main layout
        left_col, right_col = st.columns([2, 1])
        
        with left_col:
            # Assignment selection
            selected_assignment = st.selectbox(
                "Select Assignment",
                options=assignments,
                format_func=lambda x: x['name']
            )
            
            if selected_assignment:
                show_assignment_preview(selected_assignment)
            
            # File upload section
            st.markdown("""
                ℹ️ Name files with student identifiers (e.g., JohnSmith.jpg).
                The filename will be used as the student ID.
            """)
            
            st.subheader("Upload Images")
            
            # File upload section
            uploaded_files = st.file_uploader(
                "📷 Drop images here or click to choose",
                accept_multiple_files=True,
                type=['png', 'jpg', 'jpeg']
            )
            
            if uploaded_files:
                st.write("**Selected Files:**")
                for file in uploaded_files:
                    student_id = Path(file.name).stem  # Get student ID from filename
                    st.write(f"- {file.name} (Student ID: {student_id})")
                st.write(f"Total files: {len(uploaded_files)}")
            
            if uploaded_files:
                st.write("**Preview:**")
                show_upload_preview(uploaded_files)
                
                # Process button
                if st.button(
                    "Start Processing",
                    disabled=not uploaded_files or st.session_state.processing,
                    type="primary"
                ):
                    # Reset progress state
                    st.session_state.processing = True
                    st.session_state.processed_files = 0
                    st.session_state.current_stages = {}
                    st.session_state.completed_stages = {}
                    st.session_state.current_file = None
                    
                    # Start processing
                    process_submissions(
                        storage,
                        selected_assignment,
                        uploaded_files
                    )
                    
                    # Keep processing state until explicitly cleared
                    st.rerun()
        
        with right_col:
            # Show progress tracker during processing
            if st.session_state.processing:
                render_progress_tracker(
                    current_file=st.session_state.current_file,
                    total_files=len(uploaded_files) if uploaded_files else 0,
                    processed_files=st.session_state.processed_files,
                    current_stages=st.session_state.current_stages,
                    completed_stages=st.session_state.completed_stages
                )
                
                # Add completion check
                if st.session_state.processed_files == len(uploaded_files):
                    st.success("✨ All files processed successfully!")
                    if st.button("View Results", type="primary"):
                        st.session_state.processing = False  # Clear processing state
                        st.session_state.current_page = "Results"
                        st.rerun()
                
    except Exception as e:
        st.error("Error in upload page")
        st.error(str(e))
