import pandas as pd
from langchain_ollama import ChatOllama

local_llm = "deepseek-r1:7b"
llm = ChatOllama(model=local_llm, temperature=0)
llm_json_mode = ChatOllama(model=local_llm, temperature=0, format="json")