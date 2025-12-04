import streamlit as st
import time
# ASSUMING:
# display_topic, load_content are in 'website.py'
# get_adaptive_quiz_data is in 'website.py' OR 'src/quiz_generator.py'

# We'll use the 'website' module placeholder for the import
from website import display_topic, load_content, get_adaptive_quiz_data 

# --- Initialize Session State (Centralized State Management) ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'tutorial'
if 'topic_key' not in st.session_state:
    st.session_state['topic_key'] = 'variables'
if 'quiz_submitted' not in st.session_state:
    st.session_state['quiz_submitted'] = False
if 'current_quiz' not in st.session_state: 
    st.session_state['current_quiz'] = None
if 'give_up' not in st.session_state:
    st.session_state['give_up'] = False
if 'attempt_count' not in st.session_state: # NEW: Track attempts for the current question
    st.session_state['attempt_count'] = 0
if 'show_hint' not in st.session_state: 
    st.session_state['show_hint'] = False


st.title("🎓 Smart Python Tutor")

# Sidebar Navigation
topic = st.sidebar.selectbox(
    "Choose a Topic to Learn:",
    ["Variables","Conditional", "Loops", "Functions", "Oops", ],
    key='sidebar_topic'
)

# State Reset Logic (when user changes the topic)
if topic.lower() != st.session_state['topic_key']:
    st.session_state['topic_key'] = topic.lower()
    st.session_state['page'] = 'tutorial'
    st.session_state['quiz_submitted'] = False 
    st.session_state['current_quiz'] = None 
    st.session_state['give_up'] = False
    st.session_state['attempt_count'] = 0 # Reset attempts


# --- Main Content Renderer ---
st.divider()

if st.session_state['page'] == 'tutorial':
    # Tutorial View
    display_topic(st.session_state['topic_key'])
    st.markdown("---")
    
    if st.button("🧠 Take Quiz: Test Your Knowledge!"):
        st.session_state['page'] = 'quiz'
        st.session_state['quiz_submitted'] = False 
        st.session_state['current_quiz'] = None 
        st.session_state['give_up'] = False
        st.session_state['attempt_count'] = 0
        st.rerun()
elif st.session_state['page'] == 'quiz':
    
    # --- Data Fetching Logic (Called only when cache is empty) ---
    if st.session_state['current_quiz'] is None:
        with st.spinner(f"Generating adaptive question for {st.session_state['topic_key']}..."):
            quiz_data = get_adaptive_quiz_data(st.session_state['topic_key'])
            st.session_state['current_quiz'] = quiz_data
    
    quiz_data = st.session_state['current_quiz']

    # --- Error Handling ---
    if 'error' in quiz_data:
        st.error(f"Could not load quiz: {quiz_data['error']}")
        if st.button("⬅️ Back to Tutorial", key='quiz_error_back'):
            st.session_state['page'] = 'tutorial'
            st.rerun()

    # Prepare data for display
    question = quiz_data["question"]
    options = quiz_data.get("options", [])
    correct_index = quiz_data.get("answer_index")
    
    # Validation check for required MCQ components
    if not options or correct_index is None:
        st.error("Quiz data is improperly formatted. Missing options or answer index.")
        if st.button("⬅️ Back to Tutorial", key='quiz_data_error_back'):
            st.session_state['page'] = 'tutorial'
            st.rerun()


    # --- Display UI ---
    st.header(f"🧠 Quiz: {st.session_state['topic_key'].capitalize()} Challenge")
    
    # Display the adaptive state
    if 'difficulty_chosen' in quiz_data:
        st.info(f"💡 **Tutor State:** Level **{quiz_data['difficulty_chosen'].upper()}**")

    st.subheader(question)

    # Use radio buttons for MCQ options
    radio_key = f"quiz_options_{hash(question)}"
    
    # Use previous selection if available and not submitted
    initial_index = st.session_state.get('user_choice') if not st.session_state['quiz_submitted'] else None

    user_choice_index = st.radio(
        "Select your answer:",
        options=range(len(options)),
        format_func=lambda i: options[i],
        index=initial_index,
        key=radio_key,
        disabled=st.session_state['quiz_submitted']
    )
    st.session_state['user_choice'] = user_choice_index


    # --- Action Buttons ---
    col1, col2 = st.columns(2) 

    with col1:
        # Submit is only enabled if not yet submitted AND an option is selected
        submit_disabled = st.session_state['quiz_submitted'] or user_choice_index is None
        if st.button("Submit Answer", disabled=submit_disabled, key='submit_quiz'):
            st.session_state['quiz_submitted'] = True
            st.session_state['show_hint'] = False
            st.rerun() 
    
    with col2:
        # Hint button
        if 'hint' in quiz_data and quiz_data['hint']:
            if st.button("Show Hint ❓", disabled=st.session_state['quiz_submitted'], key='show_hint_btn'):
                st.session_state['show_hint'] = not st.session_state['show_hint']
                st.rerun() 
            
    # Display Hint if toggled
    if st.session_state.get('show_hint') and 'hint' in quiz_data:
        st.warning(f"**Hint:** {quiz_data['hint']}")


    # --- Results Section ---
    if st.session_state['quiz_submitted']:
        st.markdown("---")
        
        user_choice_index = st.session_state['user_choice']
        is_correct = (user_choice_index == correct_index)
        
        # 1. Feedback
        if is_correct: 
            st.success("✅ **Correct!** Excellent solution. You've earned a mastery point!")
            
        else:
            # Incorrect: Reveal answer immediately (no retry)
            st.error("❌ **Incorrect.** The correct solution is revealed below.")

        # 2. Show Solution/Explanation (Always shown after submission)
        st.markdown("### 🔑 Correct Solution:")
        st.info(f"The correct option was: **{quiz_data['answer']}**") 
        st.code(f"Explanation: {quiz_data['explanation']}", language="markdown")
        
        # 3. Next Step Button
        st.markdown("---")
        if st.button("➡️ Move to Next Question/Topic", key='next_quiz_btn'):
            # Clear all temporary quiz state variables to load a new question
            st.session_state['current_quiz'] = None 
            st.session_state['quiz_submitted'] = False
            st.session_state['user_choice'] = None
            st.session_state['show_hint'] = False
            st.rerun()

    # Button to exit the quiz page
    st.markdown("---")
    if st.button("⬅️ Back to Tutorial", key='back_to_tutorial'):
        st.session_state['page'] = 'tutorial'
        # Clean up quiz state
        st.session_state['quiz_submitted'] = False
        st.session_state['current_quiz'] = None
        st.session_state['user_choice'] = None
        st.session_state['show_hint'] = False
        st.rerun()