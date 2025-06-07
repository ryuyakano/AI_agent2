import os
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType, Tool
from langfuse.callback import CallbackHandler  # ← v2系用の正しいimport
from agent.prompts import contract_generation_prompt

# LangfuseのCallbackHandlerを初期化（v2系）
handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

# LLM初期化（OpenAIキーを明示）
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    callbacks=[handler],
)

# 契約書生成ツール
def generate_contract(instruction: str) -> str:
    return contract_generation_prompt.format(instruction=instruction)

tools = [
    Tool(
        name="ContractGenerator",
        func=generate_contract,
        description="指定された指示に基づいて契約書を生成します",
    )
]

def build_agent():
    return initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
    )
