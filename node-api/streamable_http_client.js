// streamable-http-client.js - MCP StreamableHTTP Protocol Client
const fetch = require('node-fetch');

class StreamableHttpClient {
  constructor(serverUrl) {
    this.serverUrl = serverUrl;
    this.connected = false;
    this.sessionId = null;
    this.initialized = false;
    
    // Ensure URL points to correct MCP endpoint
    if (!this.serverUrl.endsWith('/mcp')) {
      this.serverUrl = this.serverUrl.replace(/\/$/, '') + '/mcp';
    }
  }

  // Initialize MCP StreamableHTTP
  async connect() {
    try {
      console.log('MCP StreamableHTTP connection initializing...');
      
      // MCP StreamableHTTP initialization request
      const initResponse = await fetch(this.serverUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/event-stream'  // FastMCP requires both types simultaneously
        },
        body: JSON.stringify({
          "jsonrpc": "2.0",
          "id": 1,
          "method": "initialize",
          "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
              "roots": {
                "listChanged": true
              },
              "sampling": {}
            },
            "clientInfo": {
              "name": "nodejs-streamable-http-client",
              "version": "1.0.0"
            }
          }
        }),
        timeout: 15000
      });
      
      console.log('Initialization response status:', initResponse.status, initResponse.statusText);
      
      if (!initResponse.ok) {
        const errorText = await initResponse.text();
        throw new Error(`Initialization failed: ${initResponse.status} ${initResponse.statusText}\n${errorText}`);
      }
      
      // Get session ID
      this.sessionId = initResponse.headers.get('mcp-session-id') || initResponse.headers.get('x-session-id');
      console.log('Session ID:', this.sessionId);
      
      // Check response type and handle appropriately
      const contentType = initResponse.headers.get('content-type');
      let initResult;
      
      if (contentType && contentType.includes('text/event-stream')) {
        // SSE format response
        const responseText = await initResponse.text();
        console.log('SSE response:', responseText.substring(0, 300) + '...');
        
        // Parse SSE format
        const lines = responseText.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              initResult = JSON.parse(line.substring(6));
              break;
            } catch (e) {
              // Continue trying next line
            }
          }
        }
      } else {
        // Standard JSON response
        initResult = await initResponse.json();
      }
      
      console.log('MCP StreamableHTTP initialization response:', initResult);
      
      // Check response format
      if (initResult && initResult.result) {
        this.initialized = true;
        this.connected = true;
        console.log('StreamableHTTP connection setup successful');
        return initResult.result;
      } else if (initResult && initResult.error) {
        throw new Error(`MCP initialization error: ${initResult.error.message}`);
      } else {
        throw new Error('Invalid initialization response format');
      }
      
    } catch (error) {
      console.error('StreamableHTTP connection failed:', error);
      this.connected = false;
      this.initialized = false;
      throw error;
    }
  }

  // MCP tool call - StreamableHTTP method
  async callTool(toolName, params = {}) {
    if (!this.connected || !this.initialized) {
      await this.connect();
    }
    
    try {
      console.log(`Calling tool: ${toolName}`, params);
      
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'  // FastMCP requirement
      };
      
      // Add session ID (if available)
      if (this.sessionId) {
        headers['mcp-session-id'] = this.sessionId;
      }
      
      const response = await fetch(this.serverUrl, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          "jsonrpc": "2.0",
          "id": Date.now(),
          "method": "tools/call",
          "params": {
            "name": toolName,
            "arguments": params
          }
        }),
        timeout: 60000
      });
      
      console.log('Tool call response status:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Tool call failed: ${response.status} ${response.statusText}\n${errorText}`);
      }
      
      // Response handling (JSON or SSE format possible)
      const contentType = response.headers.get('content-type');
      let result;
      
      if (contentType && contentType.includes('text/event-stream')) {
        // SSE format response
        const responseText = await response.text();
        console.log('Tool call SSE response:', responseText.substring(0, 300) + '...');
        
        // Parse SSE format
        const lines = responseText.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonData = JSON.parse(line.substring(6));
              if (jsonData.id && (jsonData.result !== undefined || jsonData.error)) {
                result = jsonData;
                break;
              }
            } catch (e) {
              // Continue trying next line
            }
          }
        }
      } else {
        // Standard JSON response
        result = await response.json();
      }
      
      console.log('Tool call parsing result:', JSON.stringify(result, null, 2));
      
      if (result && result.error) {
        throw new Error(`MCP tool error: ${result.error.message}`);
      }
      
      return result ? result.result : null;
    } catch (error) {
      console.error(`Tool ${toolName} call failed:`, error);
      throw error;
    }
  }

  // MCP resource reading - StreamableHTTP method
  async getResource(resourceUri) {
    if (!this.connected || !this.initialized) {
      await this.connect();
    }
    
    try {
      const response = await fetch(this.serverUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/event-stream'
        },
        body: JSON.stringify({
          "jsonrpc": "2.0",
          "id": Date.now(),
          "method": "resources/read",
          "params": {
            "uri": resourceUri
          }
        }),
        timeout: 30000
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Resource read failed: ${response.status} ${response.statusText}\n${errorText}`);
      }
      
      const result = await response.json();
      
      if (result && result.error) {
        throw new Error(`MCP resource error: ${result.error.message}`);
      }
      
      return result ? result.result : null;
    } catch (error) {
      console.error('Resource read failed:', error);
      throw error;
    }
  }

  // Get tool list - StreamableHTTP method
  async listTools() {
    if (!this.connected || !this.initialized) {
      await this.connect();
    }
    
    try {
      console.log('Fetching tool list...');
      
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
      };
      
      if (this.sessionId) {
        headers['mcp-session-id'] = this.sessionId;
      }
      
      const response = await fetch(this.serverUrl, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          "jsonrpc": "2.0",
          "id": Date.now(),
          "method": "tools/list"
        }),
        timeout: 30000
      });
      
      console.log('Tool list response status:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Tool list fetch failed: ${response.status} ${response.statusText}\n${errorText}`);
      }
      
      // Response processing (JSON or SSE format possible)
      const contentType = response.headers.get('content-type');
      let result;
      
      if (contentType && contentType.includes('text/event-stream')) {
        const responseText = await response.text();
        console.log('Tool list SSE response:', responseText.substring(0, 300) + '...');
        
        const lines = responseText.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonData = JSON.parse(line.substring(6));
              if (jsonData.id && (jsonData.result !== undefined || jsonData.error)) {
                result = jsonData;
                break;
              }
            } catch (e) {
              // Continue trying next line
            }
          }
        }
      } else {
        result = await response.json();
      }
      
      console.log('Tool list result:', JSON.stringify(result, null, 2));
      
      if (result && result.error) {
        throw new Error(`MCP tool list error: ${result.error.message}`);
      }
      
      return result ? result.result : null;
    } catch (error) {
      console.error('Tool list fetch failed:', error);
      throw error;
    }
  }

  // Ping test
  async ping() {
    try {
      const response = await fetch(this.serverUrl.replace('/mcp', '/health'), {
        method: 'GET',
        timeout: 5000
      });
      
      return response.ok;
    } catch (error) {
      console.log('Ping failed:', error.message);
      return false;
    }
  }

  // Disconnect
  disconnect() {
    this.connected = false;
    this.initialized = false;
    this.sessionId = null;
  }

  // Check connection status
  isConnected() {
    return this.connected && this.initialized;
  }
}

module.exports = { StreamableHttpClient }; 