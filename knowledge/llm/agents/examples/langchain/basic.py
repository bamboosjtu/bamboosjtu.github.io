from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import CommaSeparatedListOutputParser

from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()


class TopicInfo(BaseModel):
    task_name: str = Field(description="概念名称")
    description: str = Field(description="概述解释")
    example: str = Field(description="代码示例")


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个黑客松教练。请用简洁、准确的方式回答。"),
        ("human", "请总结概念：{topic}"),
    ]
)

structured_llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
).with_structured_output(TopicInfo)

chain = prompt | structured_llm


result = chain.invoke({"topic": "LangChain 中的 ChatPromptTemplate"})

print(result.model_dump())
