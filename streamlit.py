import streamlit as st
import time
# ASSUMING:
# display_topic, load_content are in 'website.py'
# get_adaptive_quiz_data, fetch_data are in 'website.py' OR 'src/quiz_generator.py'

# We'll use the 'website' module placeholder for the import
from website import display_topic, load_content, get_adaptive_quiz_data, fetch_data # ADDED fetch_data

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
if 'new_topic_triggered' not in st.session_state: # NEW: Stores the topic key if a topic change is triggered
    st.session_state['new_topic_triggered'] = None


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
        st.rerun()

# --- NEW PAGE: Topic Change Explanation ---
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
        st.session_state['first_quiz_load'] = True # Ensure fetch_data is called for the *first* question of the new topic
        st.session_state['new_topic_triggered'] = None # Clear the trigger
        # 3. Move to the quiz page
        st.session_state['page'] = 'quiz'
        st.rerun()

# --- Existing Quiz Page Logic ---
elif st.session_state['page'] == 'quiz':
    
    # --- Data Fetching Logic (Called only when current_quiz is empty) ---
    if st.session_state['current_quiz'] is None:
        with st.spinner(f"Generating question for {st.session_state['topic_key']}..."):
            
            # Use fetch_data for the very first question of a new topic flow
            if st.session_state['first_quiz_load']:
                # Assuming 'current_emotion' is a static value 'neutral' for this initial call
                quiz_data = fetch_data(st.session_state['topic_key'], st.session_state['current_level'], "neutral")
                st.session_state['first_quiz_load'] = False # Next question will not be a 'first load'
            else:
                # Use the adaptive function for all subsequent questions
                quiz_data = get_adaptive_quiz_data(st.session_state['topic_key'],st.session_state['current_level'])
            
            print("quiz data:",quiz_data)
            
            # --- CRITICAL TOPIC CHANGE CHECK (AFTER ADAPTIVE CALL) ---
            new_topic_key = quiz_data.get('topic_key')
            
            if new_topic_key and new_topic_key != st.session_state['topic_key']:
                # Topic change triggered! Set up the transition page.
                st.session_state['new_topic_triggered'] = new_topic_key
                # Also capture the new level determined by the quiz generator
                if 'difficulty_chosen' in quiz_data:
                    st.session_state['current_level'] = quiz_data['difficulty_chosen']
                # Reset temporary quiz data
                st.session_state['current_quiz'] = None
                # Change the page state to the new explanation page
                st.session_state['page'] = 'topic_change_explanation'
                st.rerun()
                
            # If no topic change (or for the initial fetch_data call):
            st.session_state['current_quiz'] = quiz_data # Store the fetched data
            # Safely update current_level if the key exists
            if 'difficulty_chosen' in quiz_data:
                 st.session_state['current_level'] = quiz_data['difficulty_chosen']
            
    quiz_data = st.session_state['current_quiz']

    # --- Error Handling & Display UI (Rest of the quiz page logic remains the same) ---
    if 'error' in quiz_data:
        st.error(f"Could not load quiz: {quiz_data['error']}")
        if st.button("⬅️ Back to Tutorial", key='quiz_error_back'):
            st.session_state['page'] = 'tutorial'
            st.rerun()
        st.stop()


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
        st.stop()


    # --- Display UI ---
    st.header(f"🧠 Quiz: {st.session_state['topic_key'].capitalize()} Challenge")
    
    # Display the adaptive state
    if 'difficulty_chosen' in quiz_data:
        st.info(f"💡 **Tutor State:** Level **{quiz_data['difficulty_chosen'].upper()}**")

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
        
        user_choice_index = st.session_state['user_choice']
        is_correct = (user_choice_index == correct_index)
        
        # 1. Feedback
        if is_correct: 
            st.success(" **Correct!** Excellent solution. You've earned a mastery point!")
            
        else:
            st.error("**Incorrect.** The correct solution is revealed below.")

        # 2. Show Solution/Explanation (Always shown after submission)
        st.markdown("### Correct Solution:")
        correct_answer_text = options[correct_index] if correct_index < len(options) else "N/A"
        st.info(f"The correct option was: **{correct_answer_text}**") 
        st.code(f"Explanation: {quiz_data.get('explanation', 'No explanation provided.')}", language="markdown")
        
        # 3. Next Step Button
        st.markdown("---")
        if st.button("➡️ Move to Next Question/Topic", key='next_quiz_btn'):
            # This call will run the data fetching logic again and trigger the topic change check if applicable
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
        st.session_state['first_quiz_load'] = True # Reset for the next time the user enters the quiz
        st.session_state['new_topic_triggered'] = None
        st.rerun()