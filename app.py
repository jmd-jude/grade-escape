# app.py
import streamlit as st
from config.settings import get_settings
from services.storage import StorageService
from services.pipeline import ProcessingPipeline
from supabase import create_client, Client

# Initialize settings and services
settings = get_settings()
storage_service = StorageService()
pipeline = ProcessingPipeline()
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

# Page configuration - sidebar collapsed by default for login
if 'user' not in st.session_state:
    st.set_page_config(
        page_title="Grade Escape MVP",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
else:
    st.set_page_config(
        page_title="Grade Escape MVP",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Main application layout
if 'user' not in st.session_state:
    # Login form in main content area
    st.title("Welcome to Grade Escape")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                # Store session
                st.session_state.user = response.user
                st.session_state.access_token = response.session.access_token
                st.session_state.refresh_token = response.session.refresh_token
                
                # Get teacher info
                teacher = supabase.table('teachers') \
                    .select('*') \
                    .eq('email', email) \
                    .single() \
                    .execute()
                
                if teacher and teacher.data:
                    st.session_state.teacher = teacher.data
                    st.rerun()
                else:
                    st.error("Teacher record not found")
            except Exception as e:
                st.error("Login failed. Please check your credentials.")
else:
    # Main title
    st.title("Grade Escape MVP")
    
    # Display user info in sidebar
    with st.sidebar:
        teacher_name = st.session_state.teacher.get('name', 'Teacher')
        st.caption(f"Logged in as: {teacher_name}")
        
        if st.button("Logout", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Main page content
    st.write("# Welcome to Grade Escape! 🎓")
    st.write("Here's how to get started:")

    # Quick Start Guide using columns for better layout
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("### 1. 📚 Create an Assignment")
        st.markdown("""
        - Click "Assignment Management"
        - Define requirements and rubric
        - Set grading criteria
        """)

    with col2:
        st.write("### 2. 📝 Grade Student Work")
        st.markdown("""
        - Use "Upload & Grade"
        - Name files with student IDs
        - Get instant feedback
        """)

    with col3:
        st.write("### 3. 📊 Review Results")
        st.markdown("""
        - Access "Results" page
        - Filter by assignment
        - View detailed feedback
        """)

    # Tips section at the bottom
    st.markdown("---")
    st.write("### 💡 Pro Tips")
    st.info("""
    - Name your files like 'StudentName.jpg' for automatic student ID detection
    - Preview the rubric before uploading submissions
    - Check grading results immediately after processing
    """)
