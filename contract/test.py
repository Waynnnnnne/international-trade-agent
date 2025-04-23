import pandas as pd 
from googletrans import Translator




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
    
print(translate_chinese_to_english("滑雪服半大衣"))

excel_file = "./input/bom.xlsx"
df = pd.read_excel(excel_file, header=1) # 第一行作为价格 
product_columns = [col for col in df.columns if '品名' in col or '名称' in col or 'name' in col.lower()]
for col in product_columns:
    # 创建新的英文列
    english_col = col.replace('品名','英文名称')
    # 对每一行进行翻译
    df[english_col] = df[col].apply(translate_chinese_to_english)
    print(df[english_col])