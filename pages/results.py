import streamlit as st
from services.storage import StorageService

# Initialize storage service
storage = StorageService()

try:
    st.header("Grading Results")
    
    # Get all assignments for filtering
    assignments = storage.list_assignments()
    
    # Filters
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_assignment = st.selectbox(
            "Filter by Assignment",
            options=[a['id'] for a in assignments],
            format_func=lambda x: next((a['name'] for a in assignments if a['id'] == x), x),
            key="results_assignment_filter"
        )
    
    if selected_assignment:
        # Get submissions for selected assignment
        submissions = storage.get_submissions_by_assignment(selected_assignment)
        if submissions:
            # Summary table view
            st.write(f"Total Submissions: {len(submissions)}")
            
            # Create table data
            table_data = []
            for submission in submissions:
                score = submission.get('score')
                status = "✅" if score and score.get('teacher_score') else "⏳"
                table_data.append({
                    "Student": submission.get('student_id', 'Unknown'),
                    "Score": score.get('teacher_score', '--') if score else '--',
                    "Status": status,
                    "ID": submission.get('id')
                })
            
            # Display table
            st.write("**Submissions Overview**")
            st.table(table_data)
        
            # Detailed view
            st.write("**Detailed Submissions**")
            for submission in submissions:
                with st.expander(f"Student: {submission.get('student_id', 'Unknown')} (Score: {submission.get('score', {}).get('teacher_score', '--')})", expanded=False):
                    # Three column layout
                    img_col, response_col, grade_col = st.columns([1, 2, 1])
                    
                    with img_col:
                        # Original image
                        st.subheader("Original Work")
                        if submission.get('image_path'):
                            st.image(submission['image_path'], use_container_width=True)
                    
                    with response_col:
                        # Original response
                        st.subheader("Transcribed Response")
                        st.write(submission['ocr_text'])
                        
                        # Feedback
                        st.subheader("Feedback")
                        if submission.get('feedback_md'):
                            st.markdown(submission['feedback_md'])
                        else:
                            st.info("No feedback generated yet")
                    
                    with grade_col:
                        # Score and rubric points
                        st.subheader("Grading Details")
                        if submission.get('score'):
                            score_data = submission['score']
                            
                            # Score metrics
                            st.metric("Final Score", score_data.get('teacher_score', 'N/A'))
                            
                            # Rubric evaluation
                            if score_data.get('rubric_points_evaluation'):
                                st.write("**Rubric Points:**")
                                st.markdown("---")
                                total_points = len(score_data['rubric_points_evaluation'])
                                points_earned = sum(1 for earned in score_data['rubric_points_evaluation'].values() if earned)
                                
                                for point, earned in score_data['rubric_points_evaluation'].items():
                                    st.write(f"{'✅' if earned else '❌'} {point}")
                            
                            # Areas for improvement
                            if score_data.get('misconceptions'):
                                st.write("")  # Add spacing
                                st.write("**Areas for Improvement:**")
                                st.markdown("---")
                                for m in score_data['misconceptions']:
                                    st.write(f"- {m}")
                        else:
                            st.info("No grading data available")
                    
                    # Add visual separator
                    st.write("---")
        else:
            st.info("No submissions found for this assignment")
    else:
        st.info("Select an assignment to view results")
        
except Exception as e:
    st.error(f"Error rendering results page: {str(e)}")
    st.error("Please try refreshing the page")
