import os 
from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import retrieval_qa
from dotenv import load_dotenv
from langchain_community.llms import Ollama
import pandas as pd


doc_json = {
  "text": [
    "| 티주리 对账单        | Unnamed: 1   | Unnamed: 2   | Unnamed: 3   |\n|:---------------------|:-------------|:-------------|:-------------|\n| 品名                 | 数量         | 单价         | 合计         |\n| 长款羽绒服           | 1            | 321          | 321          |\n| 滑雪服半大衣         | 418          | 203          | 84854        |\n| 中款棉服             | 21           | 182          | 3822         |\n| 长款棉服             | 211          | 196          | 41356        |\n| 摇粒绒               | 1144         | 84           | 96096        |\n| 条幅                 | 300          | 10           | 3000         |\n| 棒球服               | 16130        | 135          | 2177550      |\n| 春季工作服           | 69           | 120          | 8280         |\n| 空军夹克             | 65           | 134          | 8710         |\n| 卫衣（有帽，有拉链） | 743          | 89           | 66127        |\n| 卫衣（有帽，无拉链） | 30           | 87           | 2610         |\n| 合计                 | 19132        | nan          | 2492726      |\n\n\n\n\n\n"
  ]
}






def main():
    """
    step1: 读取bom.xlsx
    step2: 翻译为英文，转换为美元，指定或者获取实时汇率
    step3: 获取结果填充到excel的指定位置上
    """

    read_xlsx(doc_json)

    # # 加载环境变量
    # load_dotenv()

    # # 初始化Ollama客户端
    # ollama_base_url = os.getenv("OLLAMA_BASE_URL")
    # ollama_api_key = os.getenv("OLLAMA_API_KEY")
    # ollama_model_name = "deepseek-r1:7b"

    # llm = Ollama(
    #     base_url=ollama_base_url,
    #     api_key=ollama_api_key,
    #     model_name=ollama_model_name
    # )

    # loader = UnstructuredExcelLoader("input/bom.xlsx")
    # index=VectorstoreIndexCreator()
    # doc=index.from_loaders([loader])
    # chain=retrieval_qa.from_chain_type(
    #     llm=llm,
    #     chain_type="stuff",
    #     retriever=doc.vectorstore.as_retriever(),
    #     input_key="question"
    # )
    # query = "总共有多少中产品?"
    # response=chain({"question": query})
    # print(response["answer"])


if __name__ == "__main__":
    main()

