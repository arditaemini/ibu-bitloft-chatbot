
# import os
# from dotenv import load_dotenv
# from langchain_community.document_loaders import PyPDFDirectoryLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_groq import ChatGroq
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Fixed: was checking GOOGLE_API_KEY but using GROQ

# GREETINGS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
# FAREWELLS = ["bye", "goodbye", "see you", "see ya", "take care", "quit", "exit"]


# def is_greeting(text):
#     # Fixed: only treat as pure greeting if the message is short and contains no question
#     lowered = text.lower().strip()
#     return any(lowered == g or lowered == g + "!" for g in GREETINGS)


# def is_farewell(text):
#     return any(f in text.lower() for f in FAREWELLS)


# def load_documents():
#     print("Loading your university PDFs... (this may take a minute)")

#     if not os.path.exists("docs") or not os.listdir("docs"):
#         print("Error: 'docs/' folder is empty or missing. Please add PDF files to it.")
#         return None

#     loader = PyPDFDirectoryLoader("docs/")
#     documents = loader.load()

#     if not documents:
#         print("Error: No pages could be loaded from the PDFs.")
#         return None

#     splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
#     chunks = splitter.split_documents(documents)
#     print(f"Loaded {len(documents)} pages, split into {len(chunks)} chunks.")
#     return chunks


# def build_vectorstore(chunks):
#     print("Building search index... (first time may take a few minutes)")
#     embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
#     vectorstore = FAISS.from_documents(chunks, embeddings)
#     vectorstore.save_local("faiss_index")
#     print("Index built and saved!")
#     return vectorstore


# def load_vectorstore():
#     embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
#     vectorstore = FAISS.load_local(
#         "faiss_index", embeddings, allow_dangerous_deserialization=True
#     )
#     return vectorstore


# def ask(question, vectorstore, llm, chat_history):
#     docs = vectorstore.similarity_search(question, k=10)
#     context = "\n\n".join([doc.page_content for doc in docs])

#     # Format chat history cleanly
#     history_text = "\n".join(chat_history[-6:]) if chat_history else "None"

#     prompt = ChatPromptTemplate.from_messages([
#         ("system", """You are a helpful university assistant for International Balkan University (IBU). Answer the user's question based on the context below.
#         If you can find partial information that helps answer the question, share what you know confidently rather than saying you don't have the information.
#         Do not say you couldn't find something if you can clearly see the answer in the context.

# Context:
# {context}

# Chat history:
# {chat_history}"""),
#         ("human", "{question}")
#     ])

#     chain = prompt | llm | StrOutputParser()
#     response = chain.invoke({
#         "context": context,
#         "chat_history": history_text,
#         "question": question
#     })
#     return response


# def main():
#     print("University Chatbot")
#     print("=" * 40)

#     # Fixed: validate the correct key (GROQ, not GOOGLE)
#     if not GROQ_API_KEY:
#         print("No API key found! Make sure your .env file has: GROQ_API_KEY=your_key_here")
#         return

#     # Load or build the vector index
#     if os.path.exists("faiss_index"):
#         print("Found existing index, loading it...")
#         try:
#             vectorstore = load_vectorstore()
#             print("Index loaded!")
#         except Exception as e:
#             print(f"Failed to load index ({e}). Rebuilding from docs...")
#             chunks = load_documents()
#             if not chunks:
#                 return
#             vectorstore = build_vectorstore(chunks)
#     else:
#         chunks = load_documents()
#         if not chunks:
#             return
#         vectorstore = build_vectorstore(chunks)

#     # Initialize LLM with error handling
#     try:
#         llm = ChatGroq(
#             model="llama-3.1-8b-instant",
#             api_key=GROQ_API_KEY,
#             temperature=0.3
#         )
#     except Exception as e:
#         print(f"Failed to initialize the language model: {e}")
#         return

#     chat_history = []
#     print("\nChatbot ready! Type your question (or 'bye' to exit)\n")

#     while True:
#         try:
#             user_input = input("You: ").strip()
#         except (KeyboardInterrupt, EOFError):
#             print("\nBot: Goodbye! Have a great day!")
#             break

#         if not user_input:
#             continue

#         if is_farewell(user_input):
#             print("Bot: Goodbye! Have a great day!")
#             break

#         # Fixed: only intercept pure greetings, not messages that also contain a question
#         if is_greeting(user_input):
#             print("Bot: Hello! I'm the university assistant. How can I help you today?")
#             continue

#         # Answer the question using RAG
#         try:
#             answer = ask(user_input, vectorstore, llm, chat_history)
#         except Exception as e:
#             print(f"Bot: Sorry, something went wrong while answering: {e}\n")
#             continue

#         chat_history.append(f"User: {user_input}")
#         chat_history.append(f"Bot: {answer}")
#         print(f"Bot: {answer}\n")


# if __name__ == "__main__":
#     main()

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GREETINGS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
FAREWELLS = ["bye", "goodbye", "see you", "see ya", "take care", "quit", "exit"]


def is_greeting(text):
    lowered = text.lower().strip()
    return any(lowered == g or lowered == g + "!" for g in GREETINGS)


def is_farewell(text):
    return any(f in text.lower() for f in FAREWELLS)


def load_documents():
    print("Loading your university PDFs... (this may take a minute)")

    if not os.path.exists("docs") or not os.listdir("docs"):
        print("Error: 'docs/' folder is empty or missing. Please add PDF files to it.")
        return None

    loader = PyPDFDirectoryLoader("docs/")
    documents = loader.load()

    if not documents:
        print("Error: No pages could be loaded from the PDFs.")
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
    chunks = splitter.split_documents(documents)
    print(f"Loaded {len(documents)} pages, split into {len(chunks)} chunks.")
    return chunks


def build_vectorstore(chunks):
    print("Building search index... (first time may take a few minutes)")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local("faiss_index")
    print("Index built and saved!")
    return vectorstore


def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local(
        "faiss_index", embeddings, allow_dangerous_deserialization=True
    )
    return vectorstore


def ask(question, vectorstore, llm, chat_history):
    docs = vectorstore.similarity_search(question, k=20)
    context = "\n\n".join([doc.page_content for doc in docs])

    history_text = "\n".join(chat_history[-6:]) if chat_history else "None"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful university assistant chatbot for International Balkan University (IBU).
Answer the user's question based on the context below.
If you can find partial information that helps answer the question, share what you know confidently rather than saying you don't have the information.
Do not say you couldn't find something if you can clearly see the answer in the context.
You are a chatbot assistant. Never refer to yourself as a person from the staff directory. Never claim to be a staff member, student, or anyone listed in the university records.
When asked who created you, only use the answer found in the context — do not rephrase it in first person as if you are the creator.
If asked about a full list of staff or professors, provide what you can find in the context and mention that the list may not be exhaustive.

Context:
{context}

Chat history:
{chat_history}"""),
        ("human", "{question}")
    ])

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({
        "context": context,
        "chat_history": history_text,
        "question": question
    })
    return response


def main():
    print("University Chatbot")
    print("=" * 40)

    if not GROQ_API_KEY:
        print("No API key found! Make sure your .env file has: GROQ_API_KEY=your_key_here")
        return

    if os.path.exists("faiss_index"):
        print("Found existing index, loading it...")
        try:
            vectorstore = load_vectorstore()
            print("Index loaded!")
        except Exception as e:
            print(f"Failed to load index ({e}). Rebuilding from docs...")
            chunks = load_documents()
            if not chunks:
                return
            vectorstore = build_vectorstore(chunks)
    else:
        chunks = load_documents()
        if not chunks:
            return
        vectorstore = build_vectorstore(chunks)

    try:
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=GROQ_API_KEY,
            temperature=0.3
        )
    except Exception as e:
        print(f"Failed to initialize the language model: {e}")
        return

    chat_history = []
    print("\nChatbot ready! Type your question (or 'bye' to exit)\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBot: Goodbye! Have a great day!")
            break

        if not user_input:
            continue

        if is_farewell(user_input):
            print("Bot: Goodbye! Have a great day!")
            break

        if is_greeting(user_input):
            print("Bot: Hello! I'm the university assistant. How can I help you today?")
            continue

        try:
            answer = ask(user_input, vectorstore, llm, chat_history)
        except Exception as e:
            print(f"Bot: Sorry, something went wrong while answering: {e}\n")
            continue

        chat_history.append(f"User: {user_input}")
        chat_history.append(f"Bot: {answer}")
        print(f"Bot: {answer}\n")


if __name__ == "__main__":
    main()