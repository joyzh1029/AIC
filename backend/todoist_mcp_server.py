#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Todoist MCP Server - Standard MCP Python SDK
Enhanced for Todoist API v1 compatibility
"""

import asyncio
import os
import json
import requests
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import time

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Resource,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,  
    ReadResourceResult,
    TextResourceContents,
    Prompt,
    ListPromptsRequest,
    ListPromptsResult,
    GetPromptRequest,
    GetPromptResult,
    PromptMessage,
    Role
)
import mcp.server.stdio

# Log configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("todoist-mcp")

# Todoist API configuration (v1 endpoints)
TODOIST_API_URL = "https://api.todoist.com/api/v1"
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN", "")

print("Todoist MCP Server Initializing")
print("Standard MCP SDK Version - API v1 Compatible")
print(f"API Token Status: {'Configured' if TODOIST_API_TOKEN else 'Not Configured'}")

def get_headers():
    """Get Todoist API request headers"""
    if not TODOIST_API_TOKEN:
        raise ValueError("TODOIST_API_TOKEN is not configured")
    return {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json"
    }

# Create server instance
server = Server("todoist-mcp")

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="connect_todoist",
                description="Connect to Todoist API and set API Token",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_token": {
                            "type": "string",
                            "description": "Todoist API token"
                        }
                    }
                }
            ),
            Tool(
                name="get_projects",
                description="Get all project list",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cursor": {
                            "type": "string",
                            "description": "Pagination cursor for next page"
                        }
                    }
                }
            ),
            Tool(
                name="get_tasks",
                description="Get task list (by project ID or filter)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "Project ID to filter tasks"
                        },
                        "filter_query": {
                            "type": "string", 
                            "description": "Filter query (e.g., 'today', 'overdue')"
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Pagination cursor for next page"
                        }
                    }
                }
            ),
            Tool(
                name="create_task",
                description="Create new task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Task content"
                        },
                        "description": {
                            "type": "string",
                            "description": "Task description"
                        },
                        "project_id": {
                            "type": "string",
                            "description": "Project ID to add task to"
                        },
                        "section_id": {
                            "type": "string",
                            "description": "Section ID to add task to"
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "Parent task ID (for subtasks)"
                        },
                        "order": {
                            "type": "integer",
                            "description": "Task order"
                        },
                        "label_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of label IDs"
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Task priority (1=highest, 4=lowest)",
                            "minimum": 1,
                            "maximum": 4
                        },
                        "due_string": {
                            "type": "string",
                            "description": "Due date string (e.g., 'tomorrow', 'next monday')"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date in YYYY-MM-DD format"
                        },
                        "due_datetime": {
                            "type": "string",
                            "description": "Due datetime in RFC3339 format"
                        },
                        "due_lang": {
                            "type": "string",
                            "description": "Language for parsing due_string"
                        },
                        "assignee_id": {
                            "type": "string",
                            "description": "User ID to assign task to"
                        }
                    },
                    "required": ["content"]
                }
            ),
            Tool(
                name="complete_task",
                description="Mark task as completed",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to complete"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            Tool(
                name="test_server",
                description="Test server connection and status",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    )

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Call a tool"""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "connect_todoist":
            return CallToolResult(content=[TextContent(type="text", text=await handle_connect_todoist(arguments))])
        elif name == "get_projects":
            return CallToolResult(content=[TextContent(type="text", text=await handle_get_projects(arguments))])
        elif name == "get_tasks":
            return CallToolResult(content=[TextContent(type="text", text=await handle_get_tasks(arguments))])
        elif name == "create_task":
            return CallToolResult(content=[TextContent(type="text", text=await handle_create_task(arguments))])
        elif name == "complete_task":
            return CallToolResult(content=[TextContent(type="text", text=await handle_complete_task(arguments))])
        elif name == "test_server":
            return CallToolResult(content=[TextContent(type="text", text=await handle_test_server(arguments))])
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"success": False, "error": f"Unknown tool: {name}"}, ensure_ascii=False))],
                isError=True
            )
    except Exception as e:
        logger.error(f"Tool {name} error: {str(e)}")
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))],
            isError=True
        )

# Tool implementation functions using successful Flask server logic
async def handle_connect_todoist(arguments: dict) -> str:
    """Handle Todoist connection - Flask server logic"""
    global TODOIST_API_TOKEN
    
    logger.info("connect_todoist tool called")
    
    api_token = arguments.get("api_token", "")
    if api_token:
        TODOIST_API_TOKEN = api_token
        logger.info("Using provided API Token")
    
    if not TODOIST_API_TOKEN:
        return json.dumps({
            "success": False,
            "error": "API Token not provided",
            "message": "Please set TODOIST_API_TOKEN environment variable or provide api_token parameter"
        }, ensure_ascii=False)
    
    try:
        logger.info("Testing Todoist API connection...")
        response = requests.get(
            f"{TODOIST_API_URL}/projects",
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            projects = response.json()
            # Handle both list and paginated response formats
            project_count = len(projects) if isinstance(projects, list) else len(projects.get("results", []))
            result = {
                "success": True,
                "message": "Successfully connected to Todoist API",
                "projects_count": project_count,
                "server_name": "todoist-mcp",
                "api_url": TODOIST_API_URL
            }
            logger.info(f"Todoist connection successful, found {project_count} projects")
            return json.dumps(result, ensure_ascii=False)
        else:
            error_msg = f"API request failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
    except Exception as e:
        error_msg = f"Connection error: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)

async def handle_get_projects(arguments: dict) -> str:
    """Get all project list - Flask server logic"""
    logger.info("get_projects tool called")
    
    if not TODOIST_API_TOKEN:
        return json.dumps({
            "success": False,
            "error": "API Token not configured, please call connect_todoist tool first"
        }, ensure_ascii=False)
    
    try:
        logger.info("Fetching Todoist projects...")
        start_time = time.time()
        
        # Handle pagination as per v1 API
        cursor = arguments.get("cursor", "")
        params = {}
        if cursor:
            params['cursor'] = cursor
        
        response = requests.get(
            f"{TODOIST_API_URL}/projects",
            headers=get_headers(),
            params=params,
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"API call completed in {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle the actual v1 API response format
            # API returns pagination object with 'results' and 'next_cursor'
            if isinstance(data, dict) and "results" in data:
                projects = data["results"]
                next_cursor = data.get("next_cursor")
                result = {
                    "success": True,
                    "projects": projects,
                    "count": len(projects),
                    "next_cursor": next_cursor,
                    "api_response_time": f"{elapsed_time:.2f}s"
                }
            elif isinstance(data, list):
                # Direct array response (non-paginated)
                result = {
                    "success": True,
                    "projects": data,
                    "count": len(data),
                    "api_response_time": f"{elapsed_time:.2f}s"
                }
            else:
                # Unknown format, pass through
                result = {
                    "success": True,
                    "projects": data,
                    "count": len(data) if isinstance(data, list) else 1,
                    "api_response_time": f"{elapsed_time:.2f}s"
                }
            
            logger.info(f"Successfully fetched {result['count']} projects")
            return json.dumps(result, ensure_ascii=False)
        else:
            error_msg = f"API request failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "api_response_time": f"{elapsed_time:.2f}s"
            }, ensure_ascii=False)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)

async def handle_get_tasks(arguments: dict) -> str:
    """Get task list - Flask server logic"""
    project_id = arguments.get("project_id", "")
    filter_query = arguments.get("filter_query", "")
    cursor = arguments.get("cursor", "")
    
    logger.info(f"get_tasks tool called with project_id={project_id}, filter_query={filter_query}")
    
    if not TODOIST_API_TOKEN:
        return json.dumps({
            "success": False,
            "error": "API Token not configured, please call connect_todoist tool first"
        }, ensure_ascii=False)
    
    try:
        logger.info(f"Fetching tasks with project_id={project_id}, filter_query={filter_query}")
        start_time = time.time()
        
        # Use correct v1 API endpoints
        if filter_query:
            # Use dedicated filter endpoint for v1 API
            endpoint = f"{TODOIST_API_URL}/tasks/filter"
            params = {"filter": filter_query}
        else:
            # Use standard tasks endpoint
            endpoint = f"{TODOIST_API_URL}/tasks"
            params = {}
            if project_id:
                params["project_id"] = project_id
        
        # Add pagination support
        if cursor:
            params["cursor"] = cursor
        
        logger.info(f"Making request to: {endpoint} with params: {params}")
        
        response = requests.get(
            endpoint,
            headers=get_headers(),
            params=params,
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"API call completed in {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle the actual v1 API response format
            # API returns pagination object with 'results' and 'next_cursor'
            if isinstance(data, dict) and "results" in data:
                tasks = data["results"]
                next_cursor = data.get("next_cursor")
                result = {
                    "success": True,
                    "tasks": tasks,
                    "count": len(tasks),
                    "next_cursor": next_cursor,
                    "api_response_time": f"{elapsed_time:.2f}s"
                }
            elif isinstance(data, list):
                # Direct array response (non-paginated)
                result = {
                    "success": True,
                    "tasks": data,
                    "count": len(data),
                    "api_response_time": f"{elapsed_time:.2f}s"
                }
            else:
                # Unknown format, pass through
                result = {
                    "success": True,
                    "tasks": data,
                    "count": len(data) if isinstance(data, list) else 1,
                    "api_response_time": f"{elapsed_time:.2f}s"
                }
            
            logger.info(f"Successfully fetched {result['count']} tasks")
            return json.dumps(result, ensure_ascii=False)
        else:
            error_msg = f"API request failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "api_response_time": f"{elapsed_time:.2f}s"
            }, ensure_ascii=False)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)

async def handle_create_task(arguments: dict) -> str:
    """Create new task - Flask server logic"""
    content = arguments.get("content", "")
    
    logger.info(f"create_task tool called with content={content}")
    
    if not TODOIST_API_TOKEN:
        return json.dumps({
            "success": False,
            "error": "API Token not configured, please call connect_todoist tool first"
        }, ensure_ascii=False)
    
    if not content:
        return json.dumps({
            "success": False,
            "error": "Task content is required"
        }, ensure_ascii=False)
    
    try:
        logger.info(f"Creating task: {content}")
        start_time = time.time()
        
        # Build task data according to v1 API spec
        task_data = {
            "content": content
        }
        
        # Optional fields as per v1 API documentation
        if arguments.get("description"):
            task_data["description"] = arguments["description"]
        if arguments.get("project_id"):
            task_data["project_id"] = arguments["project_id"]
        if arguments.get("section_id"):
            task_data["section_id"] = arguments["section_id"]
        if arguments.get("parent_id"):
            task_data["parent_id"] = arguments["parent_id"]
        if arguments.get("order"):
            task_data["order"] = arguments["order"]
        if arguments.get("label_ids"):
            task_data["label_ids"] = arguments["label_ids"]
        if arguments.get("priority"):
            task_data["priority"] = arguments["priority"]
        if arguments.get("due_string"):
            task_data["due_string"] = arguments["due_string"]
        if arguments.get("due_date"):
            task_data["due_date"] = arguments["due_date"]
        if arguments.get("due_datetime"):
            task_data["due_datetime"] = arguments["due_datetime"]
        if arguments.get("due_lang"):
            task_data["due_lang"] = arguments["due_lang"]
        if arguments.get("assignee_id"):
            task_data["assignee_id"] = arguments["assignee_id"]
        
        logger.info(f"Task data: {task_data}")
        
        response = requests.post(
            f"{TODOIST_API_URL}/tasks",
            headers=get_headers(),
            json=task_data,
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"API call completed in {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            task = response.json()
            result = {
                "success": True,
                "task": task,
                "message": f"Task '{content}' created successfully",
                "api_response_time": f"{elapsed_time:.2f}s"
            }
            logger.info(f"Task created successfully: {task['id']}")
            return json.dumps(result, ensure_ascii=False)
        else:
            error_msg = f"Task creation failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "api_response_time": f"{elapsed_time:.2f}s"
            }, ensure_ascii=False)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)

async def handle_complete_task(arguments: dict) -> str:
    """Mark task as completed - Flask server logic"""
    task_id = arguments.get("task_id", "")
    
    logger.info(f"complete_task tool called with task_id={task_id}")
    
    if not TODOIST_API_TOKEN:
        return json.dumps({
            "success": False,
            "error": "API Token not configured, please call connect_todoist tool first"
        }, ensure_ascii=False)
    
    if not task_id:
        return json.dumps({
            "success": False,
            "error": "Task ID is required"
        }, ensure_ascii=False)
    
    try:
        logger.info(f"Completing task: {task_id}")
        start_time = time.time()
        
        # Use correct v1 API endpoint
        response = requests.post(
            f"{TODOIST_API_URL}/tasks/{task_id}/close",
            headers=get_headers(),
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"API call completed in {elapsed_time:.2f} seconds")
        
        # v1 API returns 204 No Content for successful completion
        if response.status_code == 204:
            result = {
                "success": True,
                "message": f"Task {task_id} completed successfully",
                "api_response_time": f"{elapsed_time:.2f}s"
            }
            logger.info(f"Task {task_id} completed successfully")
            return json.dumps(result, ensure_ascii=False)
        else:
            error_msg = f"Task completion failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "api_response_time": f"{elapsed_time:.2f}s"
            }, ensure_ascii=False)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)

async def handle_test_server(arguments: dict) -> str:
    """Test server connection and status - Flask server logic"""
    logger.info("test_server tool called")
    
    try:
        result = {
            "success": True,
            "message": "Standard MCP server is running normally",
            "server_name": "todoist-mcp",
            "version": "1.9.3",
            "timestamp": datetime.now().isoformat(),
            "transport": "stdio",
            "api_token_status": "configured" if TODOIST_API_TOKEN else "not configured",
            "api_endpoint": TODOIST_API_URL,
            "api_version": "v1"
        }
        logger.info("Server test successful")
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"test_server error: {str(e)}")
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

# Resources
@server.list_resources()
async def list_resources() -> ListResourcesResult:
    """List available resources"""
    return ListResourcesResult(
        resources=[
            Resource(
                uri="todoist://status",
                name="Server Status",
                description="Display server status and configuration information",
                mimeType="text/markdown"
            ),
            Resource(
                uri="todoist://today",
                name="Today's Tasks",
                description="Get all today's tasks",
                mimeType="text/markdown"
            )
        ]
    )

@server.read_resource()
async def read_resource(uri: str) -> ReadResourceResult:
    """Read a resource"""
    if uri == "todoist://status":
        content = "# Todoist MCP Server Status\n\n"
        content += f"- **Server Name**: todoist-mcp\n"
        content += f"- **SDK**: Standard MCP Python SDK\n"
        content += f"- **API Version**: v1\n"
        content += f"- **API Token**: {'Configured' if TODOIST_API_TOKEN else 'Not Configured'}\n"
        content += f"- **Status**: Running\n"
        content += f"- **Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        content += "## Available Tools\n\n"
        content += "1. `connect_todoist` - Connect to Todoist API\n"
        content += "2. `get_projects` - Get project list\n" 
        content += "3. `get_tasks` - Get task list\n"
        content += "4. `create_task` - Create new task\n"
        content += "5. `complete_task` - Complete task\n"
        content += "6. `test_server` - Test server connection\n"
        
        return ReadResourceResult(contents=[TextResourceContents(uri=uri, mimeType="text/markdown", text=content)])
    
    elif uri == "todoist://today":
        if not TODOIST_API_TOKEN:
            content = "# Error\n\nAPI Token not configured, please call connect_todoist tool first."
        else:
            try:
                response = requests.get(
                    f"{TODOIST_API_URL}/tasks",
                    headers=get_headers(),
                    params={"filter": "today"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Handle both list and paginated formats
                    tasks = data if isinstance(data, list) else data.get("results", [])
                    
                    content = "# Today's Tasks\n\n"
                    content += f"Total {len(tasks)} tasks\n\n"
                    
                    if tasks:
                        for task in tasks:
                            priority_text = {1: "HIGH", 2: "MEDIUM", 3: "LOW", 4: "NORMAL"}
                            content += f"[{priority_text.get(task['priority'], 'NORMAL')}] **{task['content']}**\n"
                            if task.get('description'):
                                content += f"   {task['description']}\n"
                            if task.get('due'):
                                content += f"   Due: {task['due']['string']}\n"
                            content += f"   ID: {task['id']}\n\n"
                    else:
                        content += "No tasks for today, enjoy your rest!\n"
                else:
                    content = f"# Error\n\nCannot get today's tasks: {response.status_code}"
            except Exception as e:
                content = f"# Error\n\n{str(e)}"
        
        return ReadResourceResult(contents=[TextResourceContents(uri=uri, mimeType="text/markdown", text=content)])
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

# Prompts  
@server.list_prompts()
async def list_prompts() -> ListPromptsResult:
    """List available prompts"""
    return ListPromptsResult(
        prompts=[
            Prompt(
                name="daily_planning",
                description="Help with daily planning",
                arguments=[]
            ),
            Prompt(
                name="quick_task",
                description="Quick task creation prompt",
                arguments=[
                    {
                        "name": "task_content",
                        "description": "Content of the task to create",
                        "required": True
                    }
                ]
            )
        ]
    )

@server.get_prompt()
async def get_prompt(name: str, arguments: dict) -> GetPromptResult:
    """Get a prompt"""
    if name == "daily_planning":
        messages = [
            PromptMessage(
                role=Role.user,
                content=TextContent(
                    type="text",
                    text="""I'll help you plan your day.

Steps:
1. First, use get_tasks(filter_query="today") to check existing tasks for today
2. Ask about main goals and priorities  
3. Based on your answer, use create_task to create appropriate tasks and set priorities
4. Assign reasonable time to each task
5. Finally, provide overview and suggestions for today's plan

Check items:
- Are task descriptions clear and specific?
- Is priority setting reasonable (1 is highest, 4 is lowest)?
- Is time allocation reasonable with buffer time?
- Did you consider dependencies between tasks?"""
                )
            )
        ]
        
        return GetPromptResult(messages=messages)
    
    elif name == "quick_task":
        task_content = arguments.get("task_content", "")
        messages = [
            PromptMessage(
                role=Role.user,
                content=TextContent(
                    type="text",
                    text=f"""I'll help you create a task: {task_content}

Please let me know:
1. What is the detailed description of the task?
2. What priority would you like? (1=highest, 4=lowest)  
3. Is there a deadline?

I'll use the create_task tool to create this task for you."""
                )
            )
        ]
        
        return GetPromptResult(messages=messages)
    
    else:
        raise ValueError(f"Unknown prompt: {name}")

async def main():
    """Main function"""
    print("\n" + "="*50)
    print("Todoist MCP Server Starting (Standard SDK)")
    print("="*50)
    print(f"Transport Protocol: stdio")
    print(f"Registered Tools: 6")
    print(f"Registered Resources: 2")
    print(f"Registered Prompts: 2")
    print(f"API Version: v1")
    print(f"TODOIST_API_TOKEN: {'Configured' if TODOIST_API_TOKEN else 'Not Configured'}")
    print("\nServer ready for client connections...")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Server startup failed: {e}")
        import traceback
        traceback.print_exc() 