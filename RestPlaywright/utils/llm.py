import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm():
    """
       Loads environment variables and initializes a language model (LLM) client based on configuration.

       Returns:
           An instance of a chat model client (ChatGoogleGenerativeAI, ChatOpenAI, or other supported by langchain).
       """
    load_dotenv()
    model = os.getenv("LLM_MODEL")
    model_provider = os.getenv("LLM_MODEL_PROVIDER")
    print(f"LLM_MODEL={model} and LLM_MODEL_PROVIDER={model_provider}")

    if model_provider == "google_genai":
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
    if model_provider == "openai":
        return ChatOpenAI(
            model_name=model,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    return init_chat_model(model=model, model_provider=model_provider)


llm = get_llm()


def invoke(prompt: str) -> str:
    """
      Sends a prompt to the initialized LLM and returns the generated response.

      Args:
          prompt (str): The input prompt to send to the LLM.

      Returns:
          str: The LLM's response to the prompt.
      """
    return llm.invoke(prompt)
