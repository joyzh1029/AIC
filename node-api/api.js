const express = require('express');
const cors = require('cors');
const path = require('path');
const { ScheduleAgentService } = require('./schedule_service.js');
const { MCPStdioClient } = require('./mcp_stdio_client.js');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Service initialization - MCP server script path
const mcpServerPath = path.join(__dirname, '..', 'node-mcp-servers', 'todoist', 'todoist-mcp-node-server.js');
const mcpClient = new MCPStdioClient(mcpServerPath);
const scheduleService = new ScheduleAgentService(mcpClient);

// Global error handler for uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Helper function to ensure MCP connection
async function ensureMCPConnection() {
  if (!mcpClient.isConnected()) {
    console.log('MCP client not connected, attempting to connect...');
    await mcpClient.connect();
  }
}

// API Routes

// MCP server connection test
app.post('/api/mcp/todoist/connect', async (req, res) => {
  try {
    console.log('MCP connection request received');
    
    const result = await mcpClient.connect();
    console.log('MCP connection successful');
    
    res.json({
      success: true,
      message: 'MCP connection successful',
      result: result
    });
  } catch (error) {
    console.error('MCP connection failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get project list
app.get('/api/mcp/todoist/projects', async (req, res) => {
  try {
    console.log('Fetching project list');
    
    // Ensure MCP connection
    await ensureMCPConnection();
    
    const result = await mcpClient.callTool('get_projects', {});
    
    console.log('Project fetch result:', result);
    
    res.json({
      success: true,
      projects: result.projects || [],
      count: result.count || 0
    });
  } catch (error) {
    console.error('Project list fetch failed:', error);
    console.error('Error stack:', error.stack);
    res.status(500).json({
      success: false,
      error: error.message,
      details: 'Check server logs for more information'
    });
  }
});

// Get task list
app.get('/api/mcp/todoist/tasks', async (req, res) => {
  try {
    const { project_id, filter } = req.query;
    console.log('Fetching task list', { project_id, filter });
    
    // Ensure MCP connection
    await ensureMCPConnection();
    
    const params = {};
    if (project_id) params.project_id = project_id;
    if (filter) params.filter = filter;
    
    const result = await mcpClient.callTool('get_tasks', params);
    
    console.log('Task fetch result:', result);
    
    res.json({
      success: true,
      tasks: result.tasks || [],
      count: result.count || 0
    });
  } catch (error) {
    console.error('Task list fetch failed:', error);
    console.error('Error stack:', error.stack);
    res.status(500).json({
      success: false,
      error: error.message,
      details: 'Check server logs for more information'
    });
  }
});

// Create task
app.post('/api/mcp/todoist/tasks', async (req, res) => {
  try {
    const taskData = req.body;
    console.log('Creating task', taskData);
    
    // Ensure MCP connection
    await ensureMCPConnection();
    
    const result = await mcpClient.callTool('create_task', taskData);
    
    console.log('Task creation result:', result);
    
    res.json({
      success: true,
      task: result
    });
  } catch (error) {
    console.error('Task creation failed:', error);
    console.error('Error stack:', error.stack);
    res.status(500).json({
      success: false,
      error: error.message,
      details: 'Check server logs for more information'
    });
  }
});

// Complete task
app.post('/api/mcp/todoist/tasks/:taskId/complete', async (req, res) => {
  try {
    const { taskId } = req.params;
    console.log('Completing task', { taskId });
    
    // Ensure MCP connection
    await ensureMCPConnection();
    
    const result = await mcpClient.callTool('complete_task', { task_id: taskId });
    
    console.log('Task completion result:', result);
    
    res.json({
      success: true,
      result: result
    });
  } catch (error) {
    console.error('Task completion failed:', error);
    console.error('Error stack:', error.stack);
    res.status(500).json({
      success: false,
      error: error.message,
      details: 'Check server logs for more information'
    });
  }
});

// Update task
app.put('/api/mcp/todoist/tasks/:taskId', async (req, res) => {
  try {
    const { taskId } = req.params;
    const updates = req.body;
    console.log('Updating task', { taskId, updates });
    
    // Ensure MCP connection
    await ensureMCPConnection();
    
    const result = await mcpClient.callTool('update_task', { 
      task_id: taskId, 
      ...updates 
    });
    
    console.log('Task update result:', result);
    
    res.json({
      success: true,
      task: result
    });
  } catch (error) {
    console.error('Task update failed:', error);
    console.error('Error stack:', error.stack);
    res.status(500).json({
      success: false,
      error: error.message,
      details: 'Check server logs for more information'
    });
  }
});

// Delete task
app.delete('/api/mcp/todoist/tasks/:taskId', async (req, res) => {
  try {
    const { taskId } = req.params;
    console.log('Deleting task', { taskId });
    
    // Ensure MCP connection
    await ensureMCPConnection();
    
    const result = await mcpClient.callTool('delete_task', { task_id: taskId });
    
    console.log('Task deletion result:', result);
    
    res.json({
      success: true,
      result: result
    });
  } catch (error) {
    console.error('Task deletion failed:', error);
    console.error('Error stack:', error.stack);
    res.status(500).json({
      success: false,
      error: error.message,
      details: 'Check server logs for more information'
    });
  }
});

// Tool call
app.post('/api/mcp/todoist/tool/:toolName', async (req, res) => {
  const { toolName } = req.params;
  try {
    const params = req.body || {};
    
    console.log(`Calling tool: ${toolName}`, params);
    
    // Ensure MCP connection
    await ensureMCPConnection();
    
    const result = await mcpClient.callTool(toolName, params);
    
    console.log(`Tool ${toolName} result:`, result);
    
    res.json({
      success: true,
      result: result
    });
  } catch (error) {
    console.error(`Tool ${toolName || 'unknown'} call failed:`, error);
    console.error('Error stack:', error.stack);
    res.status(500).json({
      success: false,
      error: error.message,
      details: 'Check server logs for more information'
    });
  }
});

// Get tool list
app.get('/api/mcp/todoist/tools', async (req, res) => {
  try {
    console.log('Fetching tool list');
    
    // Ensure MCP connection
    await ensureMCPConnection();
    
    const tools = await mcpClient.listTools();
    
    console.log('Tool list result:', tools);
    
    res.json({
      success: true,
      tools: tools
    });
  } catch (error) {
    console.error('Tool list fetch failed:', error);
    console.error('Error stack:', error.stack);
    res.status(500).json({
      success: false,
      error: error.message,
      details: 'Check server logs for more information'
    });
  }
});

// Smart schedule agent
app.post('/api/schedule/agent', async (req, res) => {
  try {
    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({
        success: false,
        error: 'Message is required'
      });
    }
    
    console.log('Schedule agent request:', message);
    const result = await scheduleService.processMessage(message);
    
    res.json({
      success: true,
      result: result
    });
  } catch (error) {
    console.error('Schedule agent error:', error);
    console.error('Error stack:', error.stack);
    res.status(500).json({
      success: false,
      error: error.message,
      details: 'Check server logs for more information'
    });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    mcp_connected: mcpClient.isConnected()
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Node.js API server started on port ${PORT}`);
  console.log(`Todoist MCP Server`);
  console.log(`Health check available at: http://localhost:${PORT}/health`);
}); 