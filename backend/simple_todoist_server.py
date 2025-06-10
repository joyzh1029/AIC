#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Todoist API v1 Server
Direct HTTP interface for testing Todoist API integration
"""

import os
import json
import requests
import logging
from datetime import datetime
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# Log configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("todoist-api")

# Todoist API configuration (v1 endpoints)
TODOIST_API_URL = "https://api.todoist.com/api/v1"
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN", "")

app = Flask(__name__)
CORS(app)

def get_headers():
    """Get Todoist API request headers"""
    if not TODOIST_API_TOKEN:
        raise ValueError("TODOIST_API_TOKEN is not configured")
    return {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json"
    }

@app.route("/test", methods=["GET"])
def test_server():
    """Test server status"""
    return jsonify({
        "success": True,
        "message": "Todoist API server is running",
        "api_version": "v1",
        "timestamp": datetime.now().isoformat(),
        "api_token_configured": bool(TODOIST_API_TOKEN)
    })

@app.route("/connect", methods=["POST"])
def connect_todoist():
    """Connect to Todoist API"""
    global TODOIST_API_TOKEN
    
    data = request.get_json() or {}
    api_token = data.get("api_token", "")
    
    if api_token:
        TODOIST_API_TOKEN = api_token
        logger.info("Using provided API Token")
    
    if not TODOIST_API_TOKEN:
        return jsonify({
            "success": False,
            "error": "API Token not provided"
        }), 400
    
    try:
        logger.info("Testing Todoist API connection...")
        response = requests.get(
            f"{TODOIST_API_URL}/projects",
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            projects = response.json()
            return jsonify({
                "success": True,
                "message": "Successfully connected to Todoist API",
                "projects_count": len(projects),
                "api_url": TODOIST_API_URL
            })
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "error": f"API request failed: {response.status_code}"
            }), response.status_code
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/projects", methods=["GET"])
def get_projects():
    """Get all projects (v1 API compliant)"""
    if not TODOIST_API_TOKEN:
        return jsonify({
            "success": False,
            "error": "API Token not configured"
        }), 401
    
    try:
        logger.info("Fetching Todoist projects...")
        start_time = time.time()
        
        # Handle pagination as per v1 API
        cursor = request.args.get('cursor')
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
            return jsonify(result)
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "error": f"API request failed: {response.status_code}",
                "api_response_time": f"{elapsed_time:.2f}s"
            }), response.status_code
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/tasks", methods=["GET"])
def get_tasks():
    """Get tasks (v1 API compliant with proper filtering)"""
    if not TODOIST_API_TOKEN:
        return jsonify({
            "success": False,
            "error": "API Token not configured"
        }), 401
    
    try:
        project_id = request.args.get('project_id')
        filter_query = request.args.get('filter')
        cursor = request.args.get('cursor')
        
        logger.info(f"Fetching tasks with project_id={project_id}, filter={filter_query}")
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
            return jsonify(result)
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "error": f"API request failed: {response.status_code}",
                "api_response_time": f"{elapsed_time:.2f}s"
            }), response.status_code
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/tasks", methods=["POST"])
def create_task():
    """Create new task (v1 API compliant)"""
    if not TODOIST_API_TOKEN:
        return jsonify({
            "success": False,
            "error": "API Token not configured"
        }), 401
    
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400
    
    content = data.get("content", "")
    if not content:
        return jsonify({
            "success": False,
            "error": "Task content is required"
        }), 400
    
    try:
        logger.info(f"Creating task: {content}")
        start_time = time.time()
        
        # Build task data according to v1 API spec
        task_data = {
            "content": content
        }
        
        # Optional fields as per v1 API documentation
        if data.get("description"):
            task_data["description"] = data["description"]
        if data.get("project_id"):
            task_data["project_id"] = data["project_id"]
        if data.get("section_id"):
            task_data["section_id"] = data["section_id"]
        if data.get("parent_id"):
            task_data["parent_id"] = data["parent_id"]
        if data.get("order"):
            task_data["order"] = data["order"]
        if data.get("label_ids"):
            task_data["label_ids"] = data["label_ids"]
        if data.get("priority"):
            task_data["priority"] = data["priority"]
        if data.get("due_string"):
            task_data["due_string"] = data["due_string"]
        if data.get("due_date"):
            task_data["due_date"] = data["due_date"]
        if data.get("due_datetime"):
            task_data["due_datetime"] = data["due_datetime"]
        if data.get("due_lang"):
            task_data["due_lang"] = data["due_lang"]
        if data.get("assignee_id"):
            task_data["assignee_id"] = data["assignee_id"]
        
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
            return jsonify(result)
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "error": f"Task creation failed: {response.status_code}",
                "api_response_time": f"{elapsed_time:.2f}s"
            }), response.status_code
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/tasks/<task_id>/close", methods=["POST"])
def complete_task(task_id):
    """Complete task (v1 API compliant)"""
    if not TODOIST_API_TOKEN:
        return jsonify({
            "success": False,
            "error": "API Token not configured"
        }), 401
    
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
            return jsonify(result)
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "error": f"Task completion failed: {response.status_code}",
                "api_response_time": f"{elapsed_time:.2f}s"
            }), response.status_code
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/tasks/completed", methods=["GET"])
def get_completed_tasks():
    """Get completed tasks (v1 API compliant)"""
    if not TODOIST_API_TOKEN:
        return jsonify({
            "success": False,
            "error": "API Token not configured"
        }), 401
    
    try:
        cursor = request.args.get('cursor')
        params = {}
        if cursor:
            params['cursor'] = cursor
        
        logger.info("Fetching completed tasks...")
        start_time = time.time()
        
        response = requests.get(
            f"{TODOIST_API_URL}/tasks/completed",
            headers=get_headers(),
            params=params,
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"API call completed in {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            result = {
                "success": True,
                "completed_tasks": data.get("items", []),
                "count": len(data.get("items", [])),
                "next_cursor": data.get("next_cursor"),
                "api_response_time": f"{elapsed_time:.2f}s"
            }
            logger.info(f"Successfully fetched {result['count']} completed tasks")
            return jsonify(result)
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "error": f"API request failed: {response.status_code}",
                "api_response_time": f"{elapsed_time:.2f}s"
            }), response.status_code
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Simple Todoist API v1 Server Starting")
    print("="*50)
    print(f"API Version: v1")
    print(f"TODOIST_API_TOKEN: {'Configured' if TODOIST_API_TOKEN else 'Not Configured'}")
    print(f"Server will run on: http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  GET  /test - Server status")
    print("  POST /connect - Connect to Todoist API")
    print("  GET  /projects - Get projects")
    print("  GET  /tasks - Get tasks")
    print("  POST /tasks - Create task")
    print("  POST /tasks/<id>/close - Complete task")
    print("  GET  /tasks/completed - Get completed tasks")
    print("\n" + "="*50)
    
    app.run(host='0.0.0.0', port=5000, debug=True) 