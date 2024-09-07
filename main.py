import json
import chainlit as cl
import logging
import os

from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain_community.chat_models import ChatOllama
from chroma_db_manager import ChromaDBManager
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

# Configuration
CHROMA_DB_PATH = "./chroma_db"
DOC_TO_ADD_FOLDER = "./docs_folders/doc_to_add"
MODE = os.getenv('MODE')
JWT_SECRET = os.getenv('JWT_SECRET')
MODEL = os.getenv('MODEL')

if not JWT_SECRET:
    raise ValueError("JWT secret is not set. Please set JWT_SECRET in your .env file.")

# Load messages configuration
with open('personnalisation/messages.json', 'r') as f:
    messages_config = json.load(f)

# Validate mode
if MODE not in messages_config:
    raise ValueError(f"Mode {MODE} is not a valid mode. Available modes: {', '.join(messages_config.keys())}")

mode_messages = messages_config[MODE]

# Load available models
with open('personnalisation/modeles_dispo.json', 'r') as f:
    available_models = json.load(f)["models"]

# Validate the model
if MODEL not in available_models:
    raise ValueError(f"Model {MODEL} is not a valid model. Available models: {', '.join(available_models)}")

# Initialize ChromaDBManager
chroma_manager = ChromaDBManager(CHROMA_DB_PATH)
chroma_db = chroma_manager.check_or_create_chroma_db(DOC_TO_ADD_FOLDER)

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username, password) == ("admin", "admin"):
        print(f"Authenticated admin")
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None

def setup_runnable():
    retriever = chroma_db.as_retriever()

    # Initialize message history for conversation
    message_history = ChatMessageHistory()

    # Memory for conversational context
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )

    # Create a chain that uses the Chroma vector store
    chain = ConversationalRetrievalChain.from_llm(
        ChatOllama(model=MODEL),
        chain_type="stuff",
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
    )

    cl.user_session.set("chain", chain)

@cl.on_chat_start
async def on_chat_start():
    user = cl.user_session.get("user")
    if not user:
        await cl.Message(content="Authentication failed. Please log in again.").send()
        return

    logging.info("Début du démarrage de l'application")

    welcome_message = cl.Message(
        content=mode_messages["welcome_message"]["content"],
        elements=[
            cl.Image(name="start_image", display="inline", path=mode_messages["welcome_message"]["image"])
        ]
    )
    await welcome_message.send()

    setup_runnable()

@cl.on_chat_resume
async def on_chat_resume(thread: cl.ThreadDict):
    memory = ConversationBufferMemory(return_messages=True)
    root_messages = [m for m in thread["steps"] if m["parentId"] is None]
    for message in root_messages:
        if message["type"] == "user_message":
            memory.chat_memory.add_user_message(message["output"])
        else:
            memory.chat_memory.add_ai_message(message["output"])

    cl.user_session.set("memory", memory)

    setup_runnable()

@cl.on_message
async def on_message(message: cl.Message):
    user = cl.user_session.get("user")
    if not user:
        await cl.Message(content="Authentication failed. Please log in again.").send()
        return

    chain = cl.user_session.get("chain")
    cb = cl.AsyncLangchainCallbackHandler()

    # Envoyer un message avec une image avant que l'IA réfléchisse
    thinking_message = cl.Message(
        content=mode_messages["thinking_message"]["content"],
        elements=[
            cl.Image(name="thinking_image", display="inline", path=mode_messages["thinking_message"]["image"])
        ]
    )
    await thinking_message.send()

    res = await chain.ainvoke(message.content, callbacks=[cb])
    answer = res["answer"]
    source_documents = res["source_documents"]

    text_elements = []

    if source_documents:
        for source_idx, source_doc in enumerate(source_documents):
            source_name = f"source_{source_idx}"
            text_elements.append(
                cl.Text(content=source_doc.page_content, name=source_name)
            )
        source_names = [text_el.name for text_el in text_elements]

        if source_names:
            answer += f"\nSources: {', '.join(source_names)}"
        else:
            answer += "\nNo sources found"

    await cl.Message(content=answer, elements=text_elements).send()

    result_message = cl.Message(
        content=mode_messages["result_message"]["content"],
        elements=[
            cl.Image(name="result_image", display="inline", path=mode_messages["result_message"]["image"])
        ]
    )
    await result_message.send()
