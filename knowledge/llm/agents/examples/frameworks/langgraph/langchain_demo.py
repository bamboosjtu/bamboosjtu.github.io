from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

template = """
为{product}产品取一个有创意的名字，用于小红书种草。
"""

prompt = PromptTemplate(template=template, input_variables=["product"])


llm = ChatOpenAI(
    model=os.getenv("MODELSCOPE_MODEL_ID", "Qwen/Qwen3-14B"),
    api_key=os.getenv("MODELSCOPE_API_KEY"),
    base_url=os.getenv("MODELSCOPE_BASE_URL"),
    temperature=0.7,
)


basic_chain = prompt | llm


res = basic_chain.invoke({"product": "Switch2"})
print(res)
