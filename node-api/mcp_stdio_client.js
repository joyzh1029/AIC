// mcp_stdio_client.js - MCP Stdio Client
const { spawn } = require('child_process');
const { EventEmitter } = require('events');

class MCPStdioClient extends EventEmitter {
  constructor(serverScript) {
    super();
    this.serverScript = serverScript;
    this.process = null;
    this.connected = false;
    this.initialized = false;
    this.requestId = 1;
    this.pendingRequests = new Map();
    this.initializationDelay = 3000; // 3 seconds delay after initialization
  }

  async connect() {
    if (this.connected) {
      return;
    }

    try {
      console.log('MCP Stdio connection initializing...');
      
      // Start Python process
      this.process = spawn('node', [this.serverScript], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: process.cwd(),
        env: {
          ...process.env,
          TODOIST_API_TOKEN: process.env.TODOIST_API_TOKEN || '103641f989a0cec1464700543323965e77e78e85'
        }
      });

      // Handle data reception
      let buffer = '';
      this.process.stdout.on('data', (data) => {
        buffer += data.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep last incomplete line

        for (const line of lines) {
          if (line.trim()) {
            try {
              const message = JSON.parse(line);
              this.handleMessage(message);
            } catch (error) {
              console.log('Server log:', line);
            }
          }
        }
      });

      this.process.stderr.on('data', (data) => {
        console.log('Server stderr:', data.toString());
      });

      this.process.on('exit', (code) => {
        console.log(`MCP server process exited: ${code}`);
        this.connected = false;
        this.initialized = false;
      });

      // Wait for server to start up
      console.log('Waiting for server startup...');
      await this.delay(2000);

      // Initialize request
      const initResult = await this.sendRequest('initialize', {
        protocolVersion: '2024-11-05',
        capabilities: {
          roots: { listChanged: true },
          sampling: {}
        },
        clientInfo: {
          name: 'nodejs-stdio-client',
          version: '1.0.0'
        }
      });

      console.log('MCP Stdio initialization successful:', initResult);
      this.connected = true;
      this.initialized = true;

      // Wait additional time for server to fully complete initialization
      console.log('Waiting for server to fully initialize...');
      await this.delay(this.initializationDelay);
      console.log('Server ready for requests');

      return initResult;
    } catch (error) {
      console.error('MCP Stdio connection failed:', error);
      throw error;
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  handleMessage(message) {
    if (message.id && this.pendingRequests.has(message.id)) {
      const resolve = this.pendingRequests.get(message.id);
      this.pendingRequests.delete(message.id);
      
      if (message.error) {
        resolve({ error: message.error });
      } else {
        resolve({ result: message.result });
      }
    }
  }

  sendRequest(method, params = {}) {
    return new Promise((resolve, reject) => {
      if (!this.process || this.process.killed) {
        reject(new Error('MCP process is not running'));
        return;
      }

      const id = this.requestId++;
      const request = {
        jsonrpc: '2.0',
        id: id,
        method: method,
        params: params
      };

      this.pendingRequests.set(id, resolve);

      try {
        this.process.stdin.write(JSON.stringify(request) + '\n');
        
        // Set timeout with longer timeout for tool calls and initialization
        let timeout;
        if (method === 'initialize') {
          timeout = 15000; // 15 seconds for initialization
        } else if (method === 'tools/call') {
          timeout = 60000; // 60 seconds for tool calls (was 30)
        } else {
          timeout = 30000; // 30 seconds for other methods
        }
        
        setTimeout(() => {
          if (this.pendingRequests.has(id)) {
            this.pendingRequests.delete(id);
            console.log(`Request timeout for ${method} with params:`, JSON.stringify(params, null, 2));
            reject(new Error(`Request timeout: ${method}`));
          }
        }, timeout);
      } catch (error) {
        this.pendingRequests.delete(id);
        reject(error);
      }
    });
  }

  async callTool(toolName, params = {}) {
    if (!this.connected || !this.initialized) {
      await this.connect();
    }

    // Add retry logic for tool calls
    const maxRetries = 3;
    let lastError;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`Calling tool: ${toolName} (attempt ${attempt}/${maxRetries})`, params);
        
        const response = await this.sendRequest('tools/call', {
          name: toolName,
          arguments: params
        });

        if (response.error) {
          throw new Error(`MCP tool error: ${response.error.message}`);
        }

        return response.result;
      } catch (error) {
        lastError = error;
        console.error(`Tool ${toolName} call failed (attempt ${attempt}):`, error.message);
        
        if (attempt < maxRetries) {
          console.log(`Retrying in ${attempt * 1000}ms...`);
          await this.delay(attempt * 1000);
        }
      }
    }

    throw lastError;
  }

  async listTools() {
    if (!this.connected || !this.initialized) {
      await this.connect();
    }

    try {
      const response = await this.sendRequest('tools/list');
      
      if (response.error) {
        throw new Error(`MCP tool list error: ${response.error.message}`);
      }

      return response.result;
    } catch (error) {
      console.error('Tool list fetch failed:', error);
      throw error;
    }
  }

  disconnect() {
    if (this.process && !this.process.killed) {
      this.process.kill();
    }
    this.connected = false;
    this.initialized = false;
    this.pendingRequests.clear();
  }

  isConnected() {
    return this.connected && this.initialized;
  }
}

module.exports = { MCPStdioClient }; 