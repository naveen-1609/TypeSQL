# app.py
import streamlit as st
import uuid
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, AIMessage
from config import OPENAI_API_KEY
from db_utils import (store_message_in_db, retrieve_messages_from_db, retrieve_session_names,
                      delete_session_from_db, delete_all_sessions_from_db)
from er_diagram_utils import generate_er_diagram
from log_config import configure_logging

# Initialize logging
configure_logging()

# Initialize session state for session memories
if "session_memories" not in st.session_state:
    st.session_state["session_memories"] = {}

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())  # Create a unique session ID for each conversation
    st.session_state["session_name"] = "Session 1"  # Initial session name
    st.session_state["memory"] = ConversationBufferMemory(return_messages=True)

# Sidebar for previous sessions
with st.sidebar:
    st.title("Previous Sessions")
    
    # Load previous sessions from the database
    try:
        sessions = retrieve_session_names()
        if not sessions:
            st.write("No sessions found.")
        else:
            session_names = [f"{name} (ID: {sid})" for sid, name in sessions]
            selected_session = st.selectbox("Select a session to load", ["New Session"] + session_names)

            if selected_session != "New Session":
                selected_session_id = selected_session.split(" (ID: ")[-1][:-1]
                selected_session_name = [name for sid, name in sessions if sid == selected_session_id][0]
                
                if selected_session_id not in st.session_state["session_memories"]:
                    st.session_state["session_memories"][selected_session_id] = ConversationBufferMemory(return_messages=True)
                
                if st.session_state["session_id"] != selected_session_id:
                    st.session_state["session_id"] = selected_session_id
                    st.session_state["session_name"] = selected_session_name
                    st.session_state["memory"] = st.session_state["session_memories"][selected_session_id]
                
                st.success(f"Loaded session: {st.session_state['session_name']}")
    
    except Exception as e:
        st.error(f"Error loading sessions: {str(e)}")

    new_session_name = st.text_input("Enter a name for a new session:", key="new_session_name")
    if st.button("Create New Session"):
        if new_session_name:
            new_session_id = str(uuid.uuid4())
            st.session_state["session_id"] = new_session_id
            st.session_state["session_name"] = new_session_name
            st.session_state["memory"] = ConversationBufferMemory(return_messages=True)
            st.session_state["session_memories"][new_session_id] = st.session_state["memory"]
            st.session_state["schema"] = ""
            st.success(f"New session created: {new_session_name}")
        else:
            st.error("Please enter a session name.")

    if st.button("Delete Current Session"):
        if "session_id" in st.session_state and st.session_state["session_id"] in st.session_state["session_memories"]:
            delete_session_from_db(st.session_state["session_id"])
            st.session_state["session_memories"].pop(st.session_state["session_id"], None)
            st.success(f"Deleted session: {st.session_state['session_name']}")
            st.experimental_rerun()

    if st.button("Delete All Sessions"):
        delete_all_sessions_from_db()
        st.session_state["session_memories"].clear()
        st.success("All sessions deleted.")
        st.experimental_rerun()

# Define the prompt template
prompt_template_name = PromptTemplate(
    input_variables=['text'],
    template="You are a bot that converts user text into SQL statements. The given text may or may not contain the schema. If there is a schema, consider it strictly and proceed with the query; otherwise, based on the user input, create your own schema. Here is the user text: {text}"
)

# Initialize LLMChain
def initialize_chain():
    return LLMChain(
        llm=ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_API_KEY),
        prompt=prompt_template_name,
        memory=st.session_state["memory"]
    )

# Main app layout
st.title("Type SQL")
st.write(f"Current Session: {st.session_state['session_name']}")

schema = st.session_state.get("schema", "")
uploaded_file = st.file_uploader("Upload a schema file (optional)", type=["txt"])
if uploaded_file:
    schema = uploaded_file.read().decode("utf-8")
    st.session_state["schema"] = schema
    st.success("Schema uploaded successfully!")

text_input = st.text_area("Enter your text for SQL generation")
chain = initialize_chain()

if st.button("Generate SQL"):
    combined_text = f"Schema: {schema} {text_input}" if schema else text_input
    st.session_state["memory"].chat_memory.add_message(HumanMessage(content=combined_text))
    store_message_in_db(st.session_state["session_id"], st.session_state["session_name"], "User", combined_text)

    response = chain.run(text=combined_text)
    st.session_state["memory"].chat_memory.add_message(AIMessage(content=response))
    store_message_in_db(st.session_state["session_id"], st.session_state["session_name"], "Bot", response)

    if "CREATE TABLE" in response:
        st.session_state["schema"] += f"\n{response}"

    st.write("Generated SQL query:")
    st.code(response)

if st.button("View Memory"):
    messages = retrieve_messages_from_db(st.session_state["session_id"])
    if messages:
        for role, content in messages:
            st.write(f"{role}: {content}")
    else:
        st.write("No conversation history found.")

if st.button("Generate ER Diagram"):
    if schema:
        er_diagram = generate_er_diagram(st.session_state["schema"])
        st.graphviz_chart(er_diagram)
    else:
        st.warning("No schema available to generate ER diagram.")
