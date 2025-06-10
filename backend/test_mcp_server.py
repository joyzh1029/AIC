#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for updated Todoist MCP Server
"""

import asyncio
import json
from todoist_mcp_server import (
    handle_connect_todoist,
    handle_get_projects, 
    handle_get_tasks,
    handle_create_task,
    handle_complete_task,
    handle_test_server
)

async def test_mcp_functions():
    """Test all MCP server functions"""
    print("="*50)
    print("Testing Updated Todoist MCP Server Functions")
    print("="*50)
    
    # Test server status
    print("\n1. Testing server status...")
    result = await handle_test_server({})
    data = json.loads(result)
    print(f"✅ Server test: {data['success']}")
    
    # Test connection (using existing token)
    print("\n2. Testing API connection...")
    result = await handle_connect_todoist({})
    data = json.loads(result)
    print(f"✅ Connection: {data['success']}")
    if data['success']:
        print(f"   Projects found: {data.get('projects_count', 0)}")
    
    # Test get projects
    print("\n3. Testing get projects...")
    result = await handle_get_projects({})
    data = json.loads(result)
    print(f"✅ Get projects: {data['success']}")
    if data['success']:
        print(f"   Projects count: {data['count']}")
        print(f"   Response time: {data['api_response_time']}")
        if data.get('next_cursor'):
            print(f"   Has more pages: {data['next_cursor']}")
    
    # Test get tasks
    print("\n4. Testing get tasks...")
    result = await handle_get_tasks({})
    data = json.loads(result)
    print(f"✅ Get tasks: {data['success']}")
    if data['success']:
        print(f"   Tasks count: {data['count']}")
        print(f"   Response time: {data['api_response_time']}")
    
    # Test create task
    print("\n5. Testing create task...")
    task_data = {
        "content": "Test task from updated MCP server",
        "description": "Testing API v1 compatibility improvements",
        "priority": 2
    }
    result = await handle_create_task(task_data)
    data = json.loads(result)
    print(f"✅ Create task: {data['success']}")
    if data['success']:
        print(f"   Task created: {data['task']['id']}")
        print(f"   Response time: {data['api_response_time']}")
        
        # Test complete task
        print("\n6. Testing complete task...")
        task_id = data['task']['id']
        result = await handle_complete_task({"task_id": task_id})
        data = json.loads(result)
        print(f"✅ Complete task: {data['success']}")
        if data['success']:
            print(f"   Response time: {data['api_response_time']}")
    
    # Test filter tasks
    print("\n7. Testing filter tasks (today)...")
    result = await handle_get_tasks({"filter_query": "today"})
    data = json.loads(result)
    print(f"✅ Filter tasks: {data['success']}")
    if data['success']:
        print(f"   Today's tasks count: {data['count']}")
    
    print("\n" + "="*50)
    print("All tests completed!")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(test_mcp_functions()) 