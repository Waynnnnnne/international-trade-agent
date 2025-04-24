import pandas as pd
from mcp.server.fastmcp import FastMCP
from pathlib import Path
import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 初始化MCP服务器
mcp = FastMCP('translator_ML')
USER_AGENT = 'translator_ML-app/1,0'

# 初始化OpenAI客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL")
)

@mcp.tool()
async def translator_ML(input_file: str = "data/tmp.xlsx") -> str:
    """
    将Excel文件中的中文品名翻译为英文,不要输出思考过程，只需要英文品名结果
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
                        {"role": "system", "content": "你是一个专业的翻译助手，负责将中文商品名称翻译成英文。请确保翻译准确、专业，并符合国际贸易术语。"},
                        {"role": "user", "content": f"请将以下中文商品名称翻译成英文：{chinese_name}"}
                    ]
                )
                english_name = response.choices[0].message.content.strip()
                df.at[index, '英文品名'] = english_name
        
        # 保存翻译后的文件
        output_file = Path(input_file).parent / "output" / f"translated_{Path(input_file).name}"
        df.to_excel(output_file, index=False)
        
        return f"翻译完成！文件已保存至：{output_file}"
    
    except Exception as e:
        return f"翻译过程中出现错误：{str(e)}"

if __name__ == "__main__":
    # 启动MCP服务器
    mcp.run(transport='stdio') 