import pandas as pd
from mcp.server.fastmcp import FastMCP
from pathlib import Path
import os
from dotenv import load_dotenv
from openai import OpenAI
import re

# 加载环境变量
load_dotenv()

# 初始化MCP服务器
mcp = FastMCP('translator')

# 初始化OpenAI客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL")
)

def clean_translation(text: str) -> str:
    """清理翻译结果，只保留英文商品名"""
    # 如果包含引号，提取引号中的内容
    quote_match = re.search(r'"([^"]+)"', text)
    if quote_match:
        return quote_match.group(1)
    
    # 如果有解释性文字，通常在第一个句号、逗号或换行前的是翻译结果
    text = text.split('.')[0].split(',')[0].split('\n')[0]
    
    # 去除可能的前缀说明
    text = re.sub(r'^(translation:|translated as:|the translation is:|英文翻译：|翻译：)', '', text, flags=re.IGNORECASE)
    
    return text.strip()

@mcp.tool()
async def translate_excel(input_file: str = "data/tmp.xlsx") -> str:
    """
    将Excel文件中的中文品名翻译为英文
    :param input_file: Excel文件路径
    :return: 翻译结果信息
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(input_file)
        
        # 检查是否包含中文品名列
        if '品名' not in df.columns:
            return "错误：Excel文件中没有找到'品名'列"
        
        # 创建新的英文品名列
        df['英文品名'] = ''
        
        # 遍历每一行进行翻译
        for index, row in df.iterrows():
            chinese_name = str(row['品名']).strip()
            if chinese_name:
                # 调用OpenAI API进行翻译
                response = client.chat.completions.create(
                    model=os.getenv("MODEL"),
                    messages=[
                        {"role": "system", "content": "你是一个专业的翻译助手。请直接输出英文翻译结果，不要包含任何解释或额外信息。确保使用国际贸易中常用的专业术语。"},
                        {"role": "user", "content": f"请将这个商品名称翻译成英文：{chinese_name}"}
                    ],
                    temperature=0.1  # 降低温度以获得更确定的答案
                )
                
                # 获取翻译结果并清理
                english_name = clean_translation(response.choices[0].message.content)
                df.at[index, '英文品名'] = english_name
        
        # 保存翻译后的文件
        output_file = Path(input_file).parent / "output" / f"translated_bom.xlsx"
        df.to_excel(output_file, index=False)
        
        return f"翻译完成！文件已保存至：{output_file}"
    
    except Exception as e:
        return f"翻译过程中出现错误：{str(e)}"

if __name__ == "__main__":
    # 启动MCP服务器
    mcp.run(transport='stdio') 