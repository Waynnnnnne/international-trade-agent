from pathlib import Path
from pprint import pprint

import pandas as pd 
import graphrag.api as api
import graphrag.config.load_config as load_config
from graphrag.index.typing.pipeline_run_result import PipelineRunResult

from typing import Any 
from mcp.server.fastmcp import FastMCP

# init mcp server 
mcp = FastMCP('rag_ML')
USER_AGENT = 'rag_ML-app/1,0'

@mcp.tool()
async def rag_ML(query: str) -> str:
    """
    用于查询外贸行业的流程
    :pram query: 用户提出的具体问题
    :return: 最终获取的答案
    """
    PROJECT_DIRECTORY = "./"
    graphrag_config = load_config(Path(PROJECT_DIRECTORY))

    # 加载实体 & 社区 & 社区报告
    entities = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/entities.parquet")
    communities = pd.read_parquet(f"{PROJECT_DIRECTORY}/output/communities.parquet")
    community_reports = pd.read_parquet(
        f"{PROJECT_DIRECTORY}/output/community_reports.parquet"
    )

    # 全局搜索
    response, context = await api.global_search(
        config=graphrag_config,
        entities=entities,
        communities=communities,
        community_reports=community_reports,
        community_level=2, # 这是啥？
        dynamic_community_selection=False,
        response_type="Multiple Paragraphs",
        query=query,
    )
    return response

if __name__ == "__main__":
    # server 和 client在同一个节点上可以使用stdio
    # 不在同一个服务器考虑使用sse
    mcp.run(transport='stdio')
    

