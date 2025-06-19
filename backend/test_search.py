#!/usr/bin/env python3
"""
测试搜索功能的简单脚本
"""

import requests
import json

def test_search_stream():
    """测试流式搜索端点"""
    url = "http://localhost:8181/search/stream"
    data = {
        "query": "Python是什么？",
        "initial_search_query_count": 2,
        "max_research_loops": 2,
        "reasoning_model": "gpt-4o-mini"
    }
    
    try:
        print("🔍 测试流式搜索端点...")
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ 流式搜索端点工作正常")
            print("响应内容预览:")
            print(response.text[:500])
        else:
            print(f"❌ 错误: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保后端服务器正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_search_query():
    """测试传统搜索端点"""
    url = "http://localhost:8181/search/query"
    data = {"query": "Python是什么？"}
    
    try:
        print("\n🔍 测试传统搜索端点...")
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 传统搜索端点工作正常")
            print(f"成功: {result.get('success')}")
            if result.get('success'):
                print(f"响应: {result.get('response', '')[:200]}...")
        else:
            print(f"❌ 错误: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保后端服务器正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🚀 开始测试搜索功能...")
    test_search_query()
    test_search_stream()
    print("\n✨ 测试完成") 