import streamlit as st
import time
# ASSUMING:
# display_topic, load_content are in 'website.py'
# get_adaptive_quiz_data, fetch_data are in 'website.py' OR 'src/quiz_generator.py'

# We'll use the 'website' module placeholder for the import
from website import display_topic, load_content, get_adaptive_quiz_data, fetch_data

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
if 'attempt_count' not in st.session_state: # Track attempts for the current question
    st.session_state['attempt_count'] = 0
if 'show_hint' not in st.session_state: 
    st.session_state['show_hint'] = False
if 'current_level' not in st.session_state: 
    st.session_state['current_level'] = 'easy'  # Default starting level
if 'first_quiz_load' not in st.session_state: # Track if this is the very first question for the topic
    st.session_state['first_quiz_load'] = True
if 'new_topic_triggered' not in st.session_state: # Stores the topic key if a topic change is triggered
    st.session_state['new_topic_triggered'] = None

# --- NEW STATE VARIABLES ---
if 'question_start_time' not in st.session_state:
    st.session_state['question_start_time'] = time.time() # Start time of the current question
if 'time_spent_sec' not in st.session_state:
    st.session_state['time_spent_sec'] = 0.0 # Time taken to answer the current question
if 'last_answer_correct' not in st.session_state:
    st.session_state['last_answer_correct'] = None # Stores True/False/None for the last attempt
# Store the feedback for the submitted question
if 'last_feedback' not in st.session_state:
    st.session_state['last_feedback'] = None


st.title("🎓 Smart Python Tutor")

# Sidebar Navigation
topic = st.sidebar.selectbox(
    "Choose a Topic to Learn:",
    ["Variables","Conditional", "Loops", "Functions", "Oops", ],
    key='sidebar_topic'
)

# State Reset Logic (when user changes the topic via sidebar)
if topic.lower() != st.session_state['topic_key']:
    st.session_state['topic_key'] = topic.lower()
    st.session_state['page'] = 'tutorial'
    st.session_state['quiz_submitted'] = False 
    st.session_state['current_quiz'] = None 
    st.session_state['give_up'] = False
    st.session_state['attempt_count'] = 0 # Reset attempts
    st.session_state['first_quiz_load'] = True # Reset first load flag when topic changes
    st.session_state['new_topic_triggered'] = None # Clear triggered topic
    st.session_state['last_answer_correct'] = None # Reset success status
    st.session_state['last_feedback'] = None # Reset feedback


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
        st.session_state['first_quiz_load'] = True # SET TO TRUE upon entering quiz flow
        st.session_state['new_topic_triggered'] = None # Ensure no topic change is pending
        st.session_state['question_start_time'] = time.time() # START TIMER
        st.rerun()

# --- Topic Change Explanation Page ---
elif st.session_state['page'] == 'topic_change_explanation':
    
    new_topic = st.session_state['new_topic_triggered']
    
    st.header(f"🚀 Topic Transition: Introducing **{new_topic.capitalize()}**")
    st.markdown("---")
    
    st.info(f"Based on your excellent performance on **{st.session_state['topic_key'].capitalize()}** quizzes, the tutor recommends you advance!")
    st.subheader(f"New Topic: {new_topic.capitalize()}")
    
    # Display introductory content for the new topic
    display_topic(new_topic) 
    
    st.markdown("---")
    
    if st.button(f"➡️ Proceed to Quiz on {new_topic.capitalize()}", key='proceed_to_new_quiz'):
        # 1. Finalize the state change
        st.session_state['topic_key'] = new_topic
        # 2. Reset the quiz variables
        st.session_state['current_quiz'] = None 
        st.session_state['quiz_submitted'] = False
        st.session_state['user_choice'] = None
        st.session_state['show_hint'] = False
        st.session_state['first_quiz_load'] = True
        st.session_state['new_topic_triggered'] = None # Clear the trigger
        st.session_state['question_start_time'] = time.time() # START TIMER for the new question
        # 3. Move to the quiz page
        st.session_state['page'] = 'quiz'
        st.rerun()

# --- Quiz Page Logic (Updated) ---
elif st.session_state['page'] == 'quiz':
    
    # --- Data Fetching Logic (Called only when current_quiz is empty) ---
    if st.session_state['current_quiz'] is None:
        with st.spinner(f"Generating question for {st.session_state['topic_key']}..."):
            
            # Use fetch_data for the very first question of a new topic flow
            if st.session_state['first_quiz_load']:
                quiz_data = fetch_data(st.session_state['topic_key'], st.session_state['current_level'], "neutral")
                st.session_state['first_quiz_load'] = False # Next question will not be a 'first load'
            else:
                # Use the adaptive function for all subsequent questions
                # In a real system, last_feedback would be passed to influence the next question difficulty
                quiz_data = get_adaptive_quiz_data(
                    st.session_state['topic_key'],
                    st.session_state['current_level'],
                    st.session_state['last_feedback'],
                    st.session_state['last_answer_correct'],
                    st.session_state['time_spent_sec']
                    # Here you would pass st.session_state['last_feedback'] to the adaptive model
                )
            
            
            # --- CRITICAL TOPIC CHANGE CHECK (AFTER ADAPTIVE CALL) ---
            new_topic_key = quiz_data.get('topic_key')
            
            if new_topic_key and new_topic_key != st.session_state['topic_key']:
                st.session_state['new_topic_triggered'] = new_topic_key
                if 'difficulty_chosen' in quiz_data:
                    st.session_state['current_level'] = quiz_data['difficulty_chosen']
                st.session_state['current_quiz'] = None
                st.session_state['page'] = 'topic_change_explanation'
                st.rerun()
                
            # If no topic change (or for the initial fetch_data call):
            st.session_state['current_quiz'] = quiz_data # Store the fetched data
            if 'difficulty_chosen' in quiz_data:
                 st.session_state['current_level'] = quiz_data['difficulty_chosen']
            
            # Reset timer and success status for the NEW question
            st.session_state['question_start_time'] = time.time()
            st.session_state['last_answer_correct'] = None
            st.session_state['time_spent_sec'] = 0.0 # Clear previous time
            st.session_state['last_feedback'] = None # Reset feedback for the new question
            
    quiz_data = st.session_state['current_quiz']

    # --- Error Handling ---
    if 'error' in quiz_data:
        st.error(f"Could not load quiz: {quiz_data['error']}")
        if st.button("⬅️ Back to Tutorial", key='quiz_error_back'):
            st.session_state['page'] = 'tutorial'
            st.rerun()
        st.stop()

    question = quiz_data["question"]
    options = quiz_data.get("options", [])
    correct_index = quiz_data.get("answer_index")
    
    # Validation check for required MCQ components
    if not options or correct_index is None:
        st.error("Quiz data is improperly formatted. Missing options or answer index.")
        if st.button("⬅️ Back to Tutorial", key='quiz_data_error_back'):
            st.session_state['page'] = 'tutorial'
            st.rerun()
        st.stop()


    # --- Display UI ---
    st.header(f"🧠 Quiz: {st.session_state['topic_key'].capitalize()} Challenge")
    
    # Display the adaptive state
    if 'difficulty_chosen' in quiz_data:
        st.info(f"💡 **Tutor State:** Level **{st.session_state['current_level'].upper()}**")

    st.subheader(question)

    # Use radio buttons for MCQ options
    radio_key = f"quiz_options_{hash(question)}"
    
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
            
            # --- TIMER STOP & SUCCESS STATUS CAPTURE ---
            time_taken = time.time() - st.session_state['question_start_time']
            st.session_state['time_spent_sec'] = time_taken
            
            user_choice_index = st.session_state['user_choice']
            is_correct = (user_choice_index == correct_index)
            st.session_state['last_answer_correct'] = is_correct # CAPTURE SUCCESS STATUS
            
            st.session_state['quiz_submitted'] = True
            st.session_state['show_hint'] = False
            st.rerun() 
    
    with col2:
        # Hint button
        if 'hint' in quiz_data and quiz_data['hint']:
            if st.button("Show Hint", disabled=st.session_state['quiz_submitted'], key='show_hint_btn'):
                st.session_state['show_hint'] = not st.session_state['show_hint']
                st.rerun() 
            
    # Display Hint if toggled
    if st.session_state.get('show_hint') and 'hint' in quiz_data:
        st.warning(f"**Hint:** {quiz_data['hint']}")


    # --- Results Section ---
    if st.session_state['quiz_submitted']:
        st.markdown("---")
        
        is_correct = st.session_state['last_answer_correct']
        time_display = f"{st.session_state['time_spent_sec']:.2f} seconds"
        
        # 1. Feedback
        if is_correct: 
            st.success(f" **Correct!** Excellent solution. (Time: {time_display})")
            
        else:
            st.error(f"**Incorrect.** The correct solution is revealed below. (Time: {time_display})")

        # 2. Show Solution/Explanation (Always shown after submission)
        st.markdown("### Correct Solution:")
        correct_answer_text = options[correct_index] if correct_index < len(options) else "N/A"
        st.info(f"The correct option was: **{correct_answer_text}**") 
        st.code(f"Explanation: {quiz_data.get('explanation', 'No explanation provided.')}", language="markdown")
        
        # --- NEW: Question-Specific Feedback ---
        st.markdown("### Quick Feedback: How was this question?")
        # Ensure the radio button key is unique per question load cycle
        feedback_key = f"q_feedback_{hash(question)}"
        question_difficulty = st.radio(
            "Help the tutor improve the next question:",
            options=["Too Easy", "Just Right", "Too Hard", "Unclear Question"],
            key=feedback_key
        )
        # Store the selected feedback before proceeding
        st.session_state['last_feedback'] = question_difficulty

        # 3. Next Step Button
        st.markdown("---")
        
        if st.button("➡️ Move to Next Question/Topic", key='next_quiz_btn'):
            # In a real system, st.session_state['last_feedback'] is used 
            # by the get_adaptive_quiz_data call in the next run.
            
            st.session_state['current_quiz'] = None 
            st.session_state['quiz_submitted'] = False
            st.session_state['user_choice'] = None
            st.session_state['show_hint'] = False
            st.rerun()

    # Button to exit the quiz page
    st.markdown("---")
    if st.button("⬅️ Back to Tutorial", key='back_to_tutorial'):
        st.session_state['page'] = 'tutorial'
        # Clean up quiz state and reset for next time
        st.session_state['quiz_submitted'] = False
        st.session_state['current_quiz'] = None
        st.session_state['user_choice'] = None
        st.session_state['show_hint'] = False
        st.session_state['first_quiz_load'] = True 
        st.session_state['new_topic_triggered'] = None
        st.session_state['last_feedback'] = None
        st.rerun()