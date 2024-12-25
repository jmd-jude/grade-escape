# app.py
import streamlit as st
from pages.upload import render_upload_page
from pages.assignments import render_assignment_page
from pages.results import render_results_page
from config.settings import get_settings
from services.storage import StorageService
from services.pipeline import ProcessingPipeline
from supabase import create_client, Client

# Initialize settings and services
settings = get_settings()
storage_service = StorageService()
pipeline = ProcessingPipeline()
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

# Page configuration
st.set_page_config(
    page_title="Grade Escape MVP",
    page_icon="📝",
    layout="wide"
)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Upload & Grade"

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
    
    # Sidebar navigation
    with st.sidebar:
        pages = {
            "Upload & Grade": "📝",
            "Assignment Management": "📚",
            "Results": "📊"
        }
        
        st.session_state.current_page = st.radio(
            "Navigation",
            list(pages.keys()),
            format_func=lambda x: f"{pages[x]} {x}",
            index=list(pages.keys()).index(st.session_state.current_page)
        )
        
        st.markdown("---")
        teacher_name = st.session_state.teacher.get('name', 'Teacher')
        st.caption(f"Logged in as: {teacher_name}")
        
        if st.button("Logout", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Render selected page
    if st.session_state.current_page == "Upload & Grade":
        render_upload_page(storage_service)
    elif st.session_state.current_page == "Assignment Management":
        render_assignment_page(storage_service)
    elif st.session_state.current_page == "Results":
        render_results_page(storage_service)
