from pathlib import Path
from pprint import pprint
import pandas as pd 
from typing import Any 
from mcp.server.fastmcp import FastMCP
import os 
import requests
from datetime import datetime
from googletrans import Translator

# init mcp server 
mcp = FastMCP('excel_ML')
USER_AGENT = 'excel_ML-app/1,0'

def get_exchange_rate() -> float:
    """
    获取当前人民币兑美元汇率
    """
    try:
        response = requests.get(
            'https://api.exchangerate-api.com/v4/latest/CNY',
            headers={'User-Agent': USER_AGENT}
        )
        data = response.json()
        return data['rates']['USD']
    except Exception as e:
        print(f"获取汇率失败: {e}")
        return 0.14  # 默认汇率

def translate_chinese_to_english(text: str) -> str:
    """
    将中文翻译为英文
    """
    try:
        if not isinstance(text, str):
            return str(text)
            
        # 检查是否包含中文字符
        if not any('\u4e00' <= char <= '\u9fff' for char in text):
            return text
            
        translator = Translator()
        result = translator.translate(text, src='zh-cn', dest='en')
        return result.text
    except Exception as e:
        print(f"翻译失败: {e}")
        return text

@mcp.tool()
async def excel_ML(query: str) -> str:
    """
    用于读取外贸行业中的excel文件
    任务1:支持人民币转美元价格转换
    任务2：中文品名翻译为英文
    :param query: 用户提出的具体问题
    :return: 最终获取的答案
    """
    try:
        PROJECT_DIRECTORY = "./contract/input"
        excel_files = [
            os.path.join(PROJECT_DIRECTORY, item) 
            for item in os.listdir(PROJECT_DIRECTORY)
            if item.endswith(('.xlsx', '.xls'))
        ]

        if not excel_files:
            return "未找到Excel文件"

        # 读取第一个Excel文件
        df = pd.read_excel(excel_files[0], header=1)
        
        # 获取当前汇率
        exchange_rate = get_exchange_rate()
        
        # 查找包含价格的列
        price_columns = [col for col in df.columns if '单价' in col or '合计' in col or 'price' in col.lower()]
        
        if not price_columns:
            return "未找到价格列"
            
        # 转换价格
        for col in price_columns:
            df[col] = df[col] * exchange_rate
        
        # 查找品名列并翻译
        product_columns = [col for col in df.columns if '品名' in col or '名称' in col or 'name' in col.lower()]
        for col in product_columns:
            # 创建新的英文列
            english_col = col.replace('品名', '英文名称').replace('名称', '英文名称')
            # 对每一行进行翻译
            df[english_col] = df[col].apply(translate_chinese_to_english)
        
        # 保存转换后的文件
        output_dir = "./contract/output"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        df.to_excel(output_file, index=False)
        
        return f"文件处理完成，已保存到: {output_file}\n当前汇率: 1 CNY = {exchange_rate:.4f} USD"
        
    except Exception as e:
        return f"处理Excel文件时出错: {str(e)}"

if __name__ == "__main__":
    # server 和 client在同一个节点上可以使用stdio
    # 不在同一个服务器考虑使用sse
    mcp.run(transport='stdio')
