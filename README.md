# ChienGPT

**Date:** May-June 2024  
**Team Size:** 1  
**Technologies:** Python, Chainlit, LangChain, ChromaDB, Ollama, RAG

## Project Overview

ChienGPT is an application designed to enhance the capabilities of Large Language Models (LLMs) through **Retrieval Augmented Generation (RAG)**. The system leverages the power of LLMs, along with the **Chainlit** library, and integrates with **Ollama** to manage multiple models effectively.

This project was developed as part of my **Master 1 Final Project**, in collaboration with [Corentin Leandre](https://github.com/corentinleandre), under the supervision of [Germain Forestier](https://github.com/forestier).

### Key Features:
- **Retrieval Augmented Generation (RAG):** Improves the accuracy of LLMs by providing relevant data retrieved from external sources.
- **Chainlit Integration:** Utilizes Chainlit to streamline the management of LLMs and their interactions.
- **ChromaDB:** Converts a collection of PDFs into a **ChromaDB** database, allowing for effective data storage and retrieval.
- **Multi-LLM Support:** Uses **Ollama** to integrate and manage multiple large language models.

## Technologies Used
- **Python**: The primary programming language for the project.
- **Chainlit**: A framework for managing and enhancing LLM capabilities.
- **LangChain**: Facilitates connections between LLMs and external data sources.
- **ChromaDB**: A vector database used to store and retrieve information from PDF collections.
- **Ollama**: Manages the integration of multiple LLMs.

## RAG (Retrieval Augmented Generation) Details

### Libraries
- **Chainlit**: Version `1.1.202` is required. For more information, refer to the [Chainlit documentation](https://docs.chainlit.io).
- **LiteralAI**: Version `0.0.606` is essential for proper functionality.  
  **Note:** By default, `pip` may install version `0.0.601` of `literal_ai`, but you must ensure version `0.0.606` is installed for the application to work correctly.

## Running the Application

1. **Install Ollama:**
   - Download and install Ollama from [here](https://ollama.com/download).
   - Download the LLMs models you want to use via Ollama.

2. **Create a `.env` File:**
   - Create a `.env` file in the root directory of the project with the following environment variables:

     ```env
     CHAINLIT_AUTH_SECRET=<your_chainlit_auth_secret>  # Check the Chainlit documentation for instructions on creating an app
     JWT_SECRET=<your_jwt_secret>  # Generate this using Python or terminal (see details below)
     MODEL=<your_model>  # Choose from models listed in "personnalisation/modeles_dispo.json". These models should correspond to the models downloaded in Ollama
     MODE=<your_mode>    # Choose from modes listed in "personnalisation/messages.json". These messages and images personalize the user experience
     LITERAL_API_KEY=<your_literal_api_key>  # Optional, used for data persistence with Literal AI
     ```

   - **JWT_SECRET Generation:**
     - You can generate a secure JWT secret using Python or terminal. For example, in Python:

       ```python
       import secrets
       print(secrets.token_urlsafe(32))
       ```

3. **Add PDFs for Future Database:**
   - The core of this application is to feed data extracted from PDFs to a LLM model. To do so, please add the desired PDFs to the folder `docs_folders/doc_to_add`. At the start of the application, these PDFs will be processed, converted into a permanent ChromaDB database, and moved to the `docs_folders/processed_docs` folder.

4. **Run the Application:**
   - Use the following command to start the application:

     ```bash
     chainlit run main.py -h --port <port_number>
     ```

   - **Options:**
     - `-w`: Enables real-time updates.
     - `-h`: Prevents opening a new browser window automatically.
     - `--port`: Specifies a custom port (e.g., `8111`).

### **Data Persistence**
- The data is persisted online via **LiteralAI** at: [https://literalai.com/](https://literalai.com/).
- To **disable data persistence**, omit the **Literal AI key** from your `.env` file.
- To connect to another data history, create a project on **LiteralAI** and include the key in your `.env` file.

## Credits
- **Developed by:** [Pierre Albertini](https://github.com/Moumours)
- **Collaborator:** [Corentin Leandre](https://github.com/corentinleandre)
- **Supervisor:** [Germain Forestier](https://github.com/forestier)
