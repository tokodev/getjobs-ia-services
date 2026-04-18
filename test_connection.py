import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

def test_ai_connection(model_name: str):
    print(f"\n--- Testando conexão com modelo: {model_name} ---")
    
    # FORÇANDO LOCALHOST PARA TESTE FORA DO DOCKER
    base_url = "http://localhost:4000/v1"
    api_key = "sk-litellm-getjobs-2026-master-key"
    
    print(f"URL: {base_url}")
    
    try:
        chat = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model_name,
            temperature=0.1
        )

        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Connection test. Respond with 'OK' and the model name you received.")
        ]
        
        response = chat.invoke(messages)
        print(f"✅ Sucesso! Resposta: {response.content}")
        return True
    except Exception as e:
        print(f"❌ Falha: {str(e)}")
        return False

if __name__ == "__main__":
    test_ai_connection("groq/llama-3.1-8b-instant")
    test_ai_connection("llama-3.1-8b-instant")
    test_ai_connection("cv-parser-delegate")
