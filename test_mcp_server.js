// Test MCP Server Connection
const { MCPStdioClient } = require('./node-api/mcp_stdio_client.js');

async function testMCP() {
  console.log('Starting MCP server test...');
  
  const serverPath = './backend/todoist_mcp_server.py';
  console.log('MCP server path:', serverPath);
  
  const client = new MCPStdioClient(serverPath);
  
  try {
    console.log('Attempting connection...');
    const result = await client.connect();
    console.log('Connection successful:', result);
    
    console.log('Fetching tool list...');
    const tools = await client.listTools();
    console.log('Available tools:', tools);
    
    console.log('Test successful');
  } catch (error) {
    console.log('Test failed:', error);
  } finally {
    console.log('Test complete');
    client.disconnect();
  }
}

testMCP(); 