import asyncio 
import json
import os
from typing import Optional, Dict
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from openai import OpenAI
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# 记载.env文件
load_dotenv()

class MultiServerMCPClient:
    def __init__(self):
        """初始化MCP客户端,可管理多个MCP服务器的客户端"""
        self.exit_stack = AsyncExitStack()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.model = os.getenv("MODEL")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set, please set OPENAI_API_KEY in .env file")
        self.client = OpenAI(api_key=self.openai_api_key, base_url=self.base_url)
        self.session: Dict[str, ClientSession] = {} # server_name -> ClientSession 
        self.tools_by_session: Dict[str, list] = {} # 每个session的工具列表
        self.all_tools = [] # 工具列表
    
    async def transform_json(self, json2_data):
        """Claude Function Calling参数格式转化为OpenAI参数格式"""
        result = []
        for item in json2_data:
            # 确保有type 和 function两个关键字段
            if not isinstance(item, dict) or "type" not in item or "function" not in item:
                continue
            old_func = item["function"]
            # 确保function字段是一个字典
            if not isinstance(old_func, dict) or "name" not in old_func or "description" not in old_func:
                continue
            
            # 处理function字段
            new_func = {
                "name": old_func["name"],
                "description": old_func["description"],
                "parameters": {},
            }

            if "input_schema" in old_func and isinstance(old_func["input_schema"], dict):
                old_schema = old_func["input_schema"]
                
                new_func['parameters']['type'] = old_schema.get('type', 'object')
                new_func['parameters']['properties'] = old_schema.get('properties', {})
                new_func['parameters']['required'] = old_schema.get('required', [])
            
            new_item = {
                "type": item["type"],
                "function": new_func,
            }
            result.append(new_item)
        return result
    
    async def connect_to_servers(self, servers: dict):
        """
        同时启动多个服务器并获取工具
        servers: {"rag": "rag_server.py", "weather": "weather_server.py"}
        """
        
        for server_name, script_path in servers.items():
            session = await self._start_one_server(script_path)
            self.session[server_name] = session

            # 列出此服务器的工具
            resp = await session.list_tools()
            self.tools_by_session[server_name] = resp.tools # 当前session的工具列表

            for tool in resp.tools:
                # OpenAI Function Calling格式
                function_name = f"{server_name}_{tool.name}"
                self.all_tools.append({
                    "type": "function",
                    "function": {
                        "name": function_name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                })

        # function calling 
        self.all_tools = await self.transform_json(self.all_tools)
        print("\n已连接到下列服务器:")
        for name in servers:
            print(f" - {name}: {servers[name]}")
        print("\n工具汇总：")

        for t in self.all_tools:
            print(f" - {t['function']['name']}")

    async def _start_one_server(self, script_path: str) -> ClientSession:
        """启动单个MCP服务器子进程，返回ClientSession"""
        is_python = script_path.endswith(".py")
        is_js = script_path.endswith(".js")
        if not is_python and not is_js:
            raise ValueError("script_path must end with .py or .js")
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[script_path],
            env=None 
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        read_stream, write_stream = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()
        return session
    
    async def chat_base(self, messages: list) -> list:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.all_tools
        )
        print(response.choices[0].finish_reason)   
        if response.choices[0].finish_reason == "tool_calls":
            while True:
                messages = await self.create_function_response_messages(messages, response)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.all_tools
                )
                if response.choices[0].finish_reason != "tool_calls":
                    break
        return response 
        
    async def create_function_response_messages(self, messages, response):
        function_call_messages = response.choices[0].message.tool_calls
        messages.append(response.choices[0].message.model_dump())

        for function_call_message in function_call_messages:
            tool_name = function_call_message.function.name
            tool_args = json.loads(function_call_message.function.arguments)
            print("tool_name: ", tool_name)
            print("tool_args: ", tool_args)

            function_response = await self._call_mcp_tool(tool_name, tool_args)
            messages.append({
                "role": "tool",
                "content": function_response,
                "tool_call_id": function_call_message.id, # 添加tool_call_id
            })
        return messages


    async def process_query(self, user_query: str) -> str:
        """
        OpenAI 最新FunctionCalling逻辑：
        1. 发送用户信息 + tools 信息
        2. 模型`finish_reason=="tool_calls"`解析toolcalls并执行相应MCP工具
        3. 调用结果返回给OpenAI 模型生成最终回答
        """
        messages = [{"role": "user", "content": user_query}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.all_tools
        )
        content = response.choices[0]
        print(content)
        print(self.all_tools)

        if content.finish_reason == "tool_calls":
            # 需要使用工具，那么解析工具
            tool_call = content.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            print(f"\n[ 调用工具: {tool_name}, 参数: {tool_args} ]\n")

            # 执行MCP工具
            result = await self._call_mcp_tool(tool_name, tool_args)

            # 工具调用历史写进messages
            messages.append(content.message.model_dump())
            messages.append({
                "role": "tool",
                "content": result,
                "tool_call_id": tool_call.id, # 添加tool_call_id
            })

            # 第二次请求 模型整合工具结果 生成最终回答
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return response.choices[0].message.content
        return content.message.content
    
    async def _call_mcp_tool(self, tool_full_name: str, tool_args: dict) -> str:
        """
        根据 serverName_toolName 调用相应的服务器工具
        """
        parts = tool_full_name.split("_", 1)
        if len(parts) != 2:
            return f"无效的工具名称: {tool_full_name}"
        
        server_name, tool_name = parts
        session = self.session.get(server_name)
        if not session:
            return f"未找到服务器: {server_name}"
        
        try:
            # 执行MCP工具
            resp = await session.call_tool(tool_name, tool_args)
            if isinstance(resp.content, (list, dict)):
                return json.dumps(resp.content, ensure_ascii=False)
            return str(resp.content) if resp.content else "工具执行无输出"
        except Exception as e:
            return f"工具执行错误: {str(e)}"
    
    async def chat_loop(self):
        """交互式聊天"""
        print("\n多服务器MCP + 最新FunctionCalling客户端已启动！输入'quit'退出")
        messages = []

        while True:
            query = input("\n你: ").strip()
            if query.lower() == "quit":
                break
            try:
                messages.append({"role": "user", "content": query})
                messages = messages[-20:]
                print("bp1...")
                response = await self.chat_base(messages)
                print("bp2...")
                messages.append(response.choices[0].message.model_dump())
                result = response.choices[0].message.content
                print(f"\nAI: {result}")
            except Exception as e:
                print(f"\n发生错误1: {e}")

    async def cleanup(self):
        """清理资源"""
        if hasattr(self, "exit_stack") and self.exit_stack:
            await self.exit_stack.aclose()
    

async def main():
    # 服务器脚本
    servers = {
        "rag": "./rag/rag_server.py",
        "excel": "./excel/excel_server.py",
        "translator": "./translator/translator_server.py"
    }
    
    client = MultiServerMCPClient()
    try:
        print("正在连接服务器...")
        await client.connect_to_servers(servers)
        await client.chat_loop()
    except Exception as e:
        print(f"\n发生错误2: {e}")
    finally:
        print("清理资源...")
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())     
