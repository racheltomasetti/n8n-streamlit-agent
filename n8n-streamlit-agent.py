import streamlit as st
import requests
import uuid
from supabase import create_client, Client

# Supabase setup
SUPABASE_URL = "INSERT YOUR SUPABASE URL"
SUPABASE_KEY = "INSERT YOUR SUPABASE KEY"

# Webhook URLs for different agents
AGENT_WEBHOOKS = {
    "AGENT NAME": "YOUR WEBHOOK URLS"
}
 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def login(email: str, password: str):
    try:
        return supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return None

def signup(email: str, password: str):
    try:
        return supabase.auth.sign_up({"email": email, "password": password})
    except Exception as e:
        st.error(f"Signup failed: {str(e)}")
        return None
    
def init_session_state():
    if "auth" not in st.session_state:
        st.session_state.auth = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_agent" not in st.session_state:
        st.session_state.current_agent = "AI Assistant"

def clear_chat():
    st.session_state.messages = []
    st.rerun()

def display_chat():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_chat_input(prompt, webhook_url):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    payload = {
        "chatInput": prompt,
        "sessionId": st.session_state.session_id
    }
    
    headers = {
        "Authorization": f"Bearer {st.session_state.auth.session.access_token}"
    }
    
    with st.spinner("Processing..."):
        response = requests.post(webhook_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        ai_message = response.json().get("output", "Sorry, I couldn't generate a response.")
        st.session_state.messages.append({"role": "assistant", "content": ai_message})
        with st.chat_message("assistant"):
            st.markdown(ai_message)
    else:
        st.error(f"Error: {response.status_code} - {response.text}")

def auth_ui():
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            auth = login(email, password)
            if auth:
                st.session_state.auth = auth
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()

    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign Up"):
            auth = signup(email, password)
            if auth:
                st.success("Sign up successful! Please log in.")

def main():
    st.title("Welcome back!")
    init_session_state()

    if st.session_state.auth is None:
        auth_ui()
    else:
        st.sidebar.success(f"Logged in as {st.session_state.auth.user.email}")
        if st.sidebar.button("Logout"):
            st.session_state.auth = None
            st.session_state.session_id = None
            st.session_state.messages = []
            st.rerun()

        #agent select menu --> user can switch between the agents they are interacting with 
        #                      depending on their desired action 
        with st.container():
            col1, col2,  = st.columns([3, 1])
            with col1:
                current_agent = st.selectbox(
                    "Select Agent",
                    options=list(AGENT_WEBHOOKS.keys()),
                    label_visibility="collapsed"
                )
            with col2:
                if st.button("Clear Chat", type="secondary"):
                    clear_chat()

        if current_agent != st.session_state.current_agent:
            st.session_state.previous_agent = st.session_state.current_agent
            st.session_state.current_agent = current_agent
            clear_chat()
            
        display_chat()
        
        if prompt := st.chat_input(f"Chat with {st.session_state.current_agent}"):
            handle_chat_input(prompt, AGENT_WEBHOOKS[st.session_state.current_agent])

if __name__ == "__main__":
    main()