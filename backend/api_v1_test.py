#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Todoist API v1 Compatibility Test
Based on https://developer.todoist.com/api/v1/
"""

import asyncio
import json
import requests
import time
from datetime import datetime

# Import our MCP server
import todoist_mcp_server

class TodoistAPIv1Test:
    def __init__(self):
        self.api_url = "https://api.todoist.com/api/v1"
        self.token = todoist_mcp_server.TODOIST_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
    def log_test(self, test_name, status, details=""):
        """Log test result"""
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {details}")
        
    async def test_mcp_server_functions(self):
        """Test MCP server functions against API v1 spec"""
        print("\n" + "="*60)
        print("TESTING MCP SERVER FUNCTIONS (API v1 Compatible)")
        print("="*60)
        
        # Test 1: Server Status
        print("\n1. Testing MCP Server Status...")
        try:
            result = await todoist_mcp_server.handle_test_server({})
            data = json.loads(result)
            if data['success'] and data['api_version'] == 'v1':
                self.log_test("MCP Server Status", "PASS", f"API v{data['api_version']} ready")
            else:
                self.log_test("MCP Server Status", "FAIL", "API version mismatch or error")
        except Exception as e:
            self.log_test("MCP Server Status", "FAIL", str(e))
        
        # Test 2: Connection Test
        print("\n2. Testing Todoist Connection...")
        try:
            result = await todoist_mcp_server.handle_connect_todoist({})
            data = json.loads(result)
            if data['success']:
                self.log_test("Todoist Connection", "PASS", f"Found {data['projects_count']} projects")
            else:
                self.log_test("Todoist Connection", "FAIL", data['error'])
        except Exception as e:
            self.log_test("Todoist Connection", "FAIL", str(e))
        
        # Test 3: Get Projects (with pagination support)
        print("\n3. Testing Get Projects (API v1 Pagination)...")
        try:
            result = await todoist_mcp_server.handle_get_projects({})
            data = json.loads(result)
            if data['success']:
                # Check for API v1 pagination format
                has_pagination = 'next_cursor' in data
                self.log_test("Get Projects", "PASS", 
                    f"Count: {data['count']}, Pagination: {'Yes' if has_pagination else 'No'}")
                if data['count'] > 0:
                    project = data['projects'][0]
                    self.log_test("Project Structure", "PASS", 
                        f"ID: {project['id']}, Name: {project['name']}")
            else:
                self.log_test("Get Projects", "FAIL", data['error'])
        except Exception as e:
            self.log_test("Get Projects", "FAIL", str(e))
        
        # Test 4: Get Tasks (with filtering)
        print("\n4. Testing Get Tasks (API v1 Format)...")
        try:
            result = await todoist_mcp_server.handle_get_tasks({})
            data = json.loads(result)
            if data['success']:
                # Check for API v1 format
                has_pagination = 'next_cursor' in data
                self.log_test("Get Tasks", "PASS", 
                    f"Count: {data['count']}, Pagination: {'Yes' if has_pagination else 'No'}")
                if data['count'] > 0:
                    task = data['tasks'][0]
                    self.log_test("Task Structure", "PASS", 
                        f"ID: {task['id']}, Content: {task['content'][:50]}...")
            else:
                self.log_test("Get Tasks", "FAIL", data['error'])
        except Exception as e:
            self.log_test("Get Tasks", "FAIL", str(e))
        
        # Test 5: Create Task (API v1 full parameters)
        print("\n5. Testing Create Task (API v1 Full Parameters)...")
        try:
            task_data = {
                "content": "API v1 Compatibility Test Task",
                "description": "Testing all API v1 parameters",
                "priority": 2,
                "due_string": "tomorrow"
            }
            result = await todoist_mcp_server.handle_create_task(task_data)
            data = json.loads(result)
            if data['success']:
                task = data['task']
                self.log_test("Create Task", "PASS", 
                    f"ID: {task['id']}, Priority: {task['priority']}")
                
                # Test 6: Complete Task (API v1 endpoint)
                print("\n6. Testing Complete Task (API v1 /close endpoint)...")
                result = await todoist_mcp_server.handle_complete_task({"task_id": task['id']})
                data = json.loads(result)
                if data['success']:
                    self.log_test("Complete Task", "PASS", "Task completed successfully")
                else:
                    self.log_test("Complete Task", "FAIL", data['error'])
            else:
                self.log_test("Create Task", "FAIL", data['error'])
        except Exception as e:
            self.log_test("Create Task", "FAIL", str(e))
    
    def test_direct_api_compliance(self):
        """Test direct API compliance with v1 specification"""
        print("\n" + "="*60)
        print("TESTING DIRECT API v1 COMPLIANCE")
        print("="*60)
        
        # Test 1: Projects endpoint
        print("\n1. Testing /api/v1/projects endpoint...")
        try:
            response = requests.get(f"{self.api_url}/projects", headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Check if it's paginated response or direct array
                if isinstance(data, list):
                    self.log_test("Projects API", "PASS", f"Direct array: {len(data)} projects")
                elif isinstance(data, dict) and 'results' in data:
                    self.log_test("Projects API", "PASS", f"Paginated: {len(data['results'])} projects")
                else:
                    self.log_test("Projects API", "WARN", "Unknown response format")
            else:
                self.log_test("Projects API", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Projects API", "FAIL", str(e))
        
        # Test 2: Tasks endpoint
        print("\n2. Testing /api/v1/tasks endpoint...")
        try:
            response = requests.get(f"{self.api_url}/tasks", headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Check API v1 format
                if isinstance(data, list):
                    self.log_test("Tasks API", "PASS", f"Direct array: {len(data)} tasks")
                elif isinstance(data, dict) and 'results' in data:
                    self.log_test("Tasks API", "PASS", f"Paginated: {len(data['results'])} tasks")
                else:
                    self.log_test("Tasks API", "WARN", "Unknown response format")
            else:
                self.log_test("Tasks API", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Tasks API", "FAIL", str(e))
        
        # Test 3: Filter endpoint (API v1 specific)
        print("\n3. Testing /api/v1/tasks/filter endpoint...")
        try:
            params = {"filter": "today"}
            response = requests.get(f"{self.api_url}/tasks/filter", 
                                  headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Filter API", "PASS", f"Filter works: {len(data) if isinstance(data, list) else 'paginated'}")
            else:
                self.log_test("Filter API", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Filter API", "FAIL", str(e))
        
        # Test 4: Task creation with full v1 parameters
        print("\n4. Testing task creation with API v1 parameters...")
        try:
            task_data = {
                "content": "Direct API v1 Test Task",
                "description": "Testing direct API v1 task creation",
                "priority": 3,
                "due_string": "next week"
            }
            response = requests.post(f"{self.api_url}/tasks", 
                                   headers=self.headers, json=task_data, timeout=10)
            if response.status_code == 200:
                task = response.json()
                self.log_test("Create Task API", "PASS", f"Task created: {task['id']}")
                
                # Test completion with v1 endpoint
                close_response = requests.post(f"{self.api_url}/tasks/{task['id']}/close",
                                             headers=self.headers, timeout=10)
                if close_response.status_code == 204:
                    self.log_test("Close Task API", "PASS", "Task closed successfully (204)")
                else:
                    self.log_test("Close Task API", "FAIL", f"HTTP {close_response.status_code}")
            else:
                self.log_test("Create Task API", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Create Task API", "FAIL", str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✅ PASS: Test completed successfully")
        print("❌ FAIL: Test failed")
        print("⚠️  WARN: Test completed with warnings")
        print("\nAll tests validate compatibility with Todoist API v1 specification")
        print("Documentation: https://developer.todoist.com/api/v1/")
        print("="*60)

async def main():
    """Run all tests"""
    print("Todoist API v1 Compatibility Test Suite")
    print("Based on official documentation")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    tester = TodoistAPIv1Test()
    
    # Test MCP server functions
    await tester.test_mcp_server_functions()
    
    # Test direct API compliance
    tester.test_direct_api_compliance()
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main()) 