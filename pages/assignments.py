import streamlit as st
import json
from services.storage import StorageService
from models.assignment import Assignment, RubricRequirement, RubricStructure, RubricMetadata

# Initialize storage service
storage = StorageService()

# Main page render
st.header("Assignment Management")

tab1, tab2 = st.tabs(["Create Assignment", "View Assignments"])

with tab1:
    # Initialize session state
    if 'requirements' not in st.session_state:
        st.session_state.requirements = []
    if 'input_key_counter' not in st.session_state:
        st.session_state.input_key_counter = 0
    if 'rubric_notes' not in st.session_state:
        st.session_state.rubric_notes = ""
    if 'rubric_examples' not in st.session_state:
        st.session_state.rubric_examples = []
    
    with st.container():
        st.subheader("Create New Assignment")
        
        # Create two columns for the main layout
        left_col, right_col = st.columns([2, 1])
        
        with left_col:
            # Display existing requirements with remove buttons OUTSIDE the form
            st.subheader("Rubric Requirements")
            total_points = 0
            for i, req in enumerate(st.session_state.requirements):
                cols = st.columns([3, 0.5])
                with cols[0]:
                    st.text(f"{req['text']} ({req['points']} points)")
                with cols[1]:
                    if st.button("🗑️", key=f"remove_{i}"):
                        st.session_state.requirements.pop(i)
                        st.rerun()
                total_points += req['points']
            
            # Assignment Details Section
            with st.form("assignment_form"):
                name = st.text_input("Assignment Name")
                question = st.text_area("Question Text", height=150)
                
                # New requirement inputs
                st.subheader("Add Requirement")
                req_cols = st.columns([3, 1])
                with req_cols[0]:
                    new_req = st.text_input(
                        "New Requirement",
                        key=f"new_req_{st.session_state.input_key_counter}"
                    )
                with req_cols[1]:
                    points = st.number_input(
                        "Points",
                        min_value=1,
                        value=1,
                        key=f"points_{st.session_state.input_key_counter}"
                    )
                
                # Add Requirement button right after requirements input
                if st.form_submit_button("Add Requirement", type="secondary"):
                    if new_req:
                        st.session_state.requirements.append({
                            "text": new_req,
                            "points": points
                        })
                        st.session_state.input_key_counter += 1
                        st.rerun()
                
                # Rubric metadata section
                st.subheader("Rubric Metadata")
                notes = st.text_area(
                    "Grading Notes",
                    value=st.session_state.rubric_notes,
                    help="Add any notes about how to grade this assignment"
                )
                
                # Example management
                st.write("Example Answers")
                for i, example in enumerate(st.session_state.rubric_examples):
                    cols = st.columns([4, 1])
                    with cols[0]:
                        st.text(f"Example {i+1}: {example}")
                
                new_example = st.text_area("Add Example Answer", height=100)
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.form_submit_button("Add Example", type="secondary"):
                        if new_example:
                            st.session_state.rubric_examples.append(new_example)
                            st.rerun()
                
                st.write(f"Total Points: {total_points}")
                
                # Main submit button
                if st.form_submit_button("Create Assignment", type="primary"):
                    try:
                        if not st.session_state.requirements:
                            st.error("Please add at least one requirement")
                            st.stop()
                        
                        # Create proper RubricRequirement objects
                        requirements = [
                            RubricRequirement(text=req['text'], points=req['points'])
                            for req in st.session_state.requirements
                        ]
                        
                        # Create the full RubricStructure with metadata
                        rubric_structure = RubricStructure(
                            requirements=requirements,
                            metadata=RubricMetadata(
                                notes=notes,
                                examples=st.session_state.rubric_examples,
                                version=1
                            )
                        )
                        
                        # Create and save assignment
                        assignment = Assignment(
                            name=name,
                            question_text=question,
                            points_possible=total_points,
                            rubric_structure=rubric_structure
                        )
                        
                        storage.create_assignment(assignment)
                        
                        # Clear form and state
                        st.session_state.requirements = []
                        st.session_state.input_key_counter = 0
                        st.session_state.rubric_notes = ""
                        st.session_state.rubric_examples = []
                        st.success("Assignment created successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error creating assignment: {str(e)}")
        
        with right_col:
            # Preview Section
            with st.container():
                st.subheader("Preview")
                if name:
                    st.write(f"**{name}**")
                if question:
                    st.write(question)
                if st.session_state.requirements:
                    st.write("\n**Rubric:**")
                    for req in st.session_state.requirements:
                        st.write(f"- {req['text']} ({req['points']} pts)")
                if notes or st.session_state.rubric_examples:
                    st.write("\n**Metadata:**")
                    if notes:
                        st.write("*Grading Notes:*")
                        st.write(notes)
                    if st.session_state.rubric_examples:
                        st.write("*Example Answers:*")
                        for i, example in enumerate(st.session_state.rubric_examples, 1):
                            st.write(f"{i}. {example}")

with tab2:
    def render_assignments_list(storage: StorageService):
        st.subheader("Your Assignments")
        
        try:
            assignments = storage.list_assignments()
            
            if not assignments:
                st.info("No assignments created yet. Use the Create Assignment tab to get started!")
                return
                
            # Create a clean table layout
            for assignment in assignments:
                with st.expander(f"{assignment['name']} ({assignment['points_possible']} points)"):
                    cols = st.columns([3, 1])
                    with cols[0]:
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
                        
                        # Display metadata if present
                        if rubric.get('metadata'):
                            if rubric['metadata'].get('notes'):
                                st.write("\n**Grading Notes:**")
                                st.write(rubric['metadata']['notes'])
                            if rubric['metadata'].get('examples'):
                                st.write("\n**Example Answers:**")
                                for i, example in enumerate(rubric['metadata']['examples'], 1):
                                    st.write(f"{i}. {example}")
                    
                    with cols[1]:
                        st.button(
                            "Edit",
                            key=f"edit_{assignment['id']}",
                            disabled=True,
                            help="Coming soon!"
                        )
                        
        except Exception as e:
            st.error(f"Error loading assignments: {str(e)}")
    
    render_assignments_list(storage)
