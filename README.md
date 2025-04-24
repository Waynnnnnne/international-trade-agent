# International-Trade-Agent
This LLM agent aims to streamline the time-consuming and repetitive work processes for professionals in the international trade industry, enhancing efficiency and operational convenience

# Installation
uv add mcp graphrag pathlib pandas openpyxl googletrans==3.1.0a0

# Run
uv run client.py   

# Features
知识图谱
品名翻译
人民币价格转换美元价格

# TODO
合同制作 Excel MCP 
智能客服 记忆持久化
市场分析 自动化报表，SQL
选品    多模态

# LLM
私有化部署 
- ollma参考文档：https://ollama.org.cn/blog/openai-compatibility

API调用：
- 阿里百炼
- 硅基流动    

# 前端
streamlit: https://www.youtube.com/watch?v=4sVU4GfAYOA

# Citation 
外贸流程文档: https://zhuanlan.zhihu.com/p/131489851

# Prompt Examples
给出外贸行业的流程
读取外贸excel文件，使用工具将价格转化为美元
读取excel翻译中文品名为英文品名,只输出英文品名到表格中，不要添加额外的字符