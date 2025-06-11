import WebSocket, { WebSocketServer } from 'ws';
import express from 'express';
import http from 'http';
import dotenv from 'dotenv';
import { messageTypes, responseTypes } from './constants/minimax-types.js';

dotenv.config();

const app = express();
const server = http.createServer(app);

// Create WebSocket server for frontend connections
const wss = new WebSocketServer({ 
    server,
    path: '/ws/realtime-chat'
});

// MiniMax API configuration
const MINIMAX_URL = "wss://api.minimax.chat/ws/v1/realtime?model=abab6.5s-chat";
const API_KEY = process.env.MINIMAX_API_KEY;

// Store client connections and corresponding MiniMax connections
const clientConnections = new Map();

// Audio buffer for accumulating audio chunks
const audioBuffers = new Map();

wss.on('connection', (clientWs, req) => {
    console.log('Frontend client connected successfully');
    
    // Create independent MiniMax connection for each client
    const minimaxWs = new WebSocket(MINIMAX_URL, {
        headers: {
            "Authorization": `Bearer ${API_KEY}`
        }
    });

    // Initialize audio buffer for this client
    audioBuffers.set(clientWs, []);

    // Store connection mapping
    clientConnections.set(clientWs, minimaxWs);

    // MiniMax connection event handling
    minimaxWs.on('open', () => {
        console.log('MiniMax connection established successfully');
        
        // 1. Send session.update to configure the session with Chinese instructions
        minimaxWs.send(JSON.stringify({
            type: messageTypes.SESSION_UPDATE,
            session: {
                modalities: ["text", "audio"],
                instructions: "You are an intelligent assistant. Please answer user questions in Chinese.",
                voice: "female-1",
                output_audio_format: "pcm16",
                temperature: 0.8,
                max_output_tokens: 4096
            }
        }));
        
        // Use setTimeout as suggested by user to sequence context creation and response request
        setTimeout(() => {
            // 2. Add initial context item (system message in Chinese)
            minimaxWs.send(JSON.stringify({
                type: messageTypes.CONVERSATION_ITEM_CREATE,
                item: {
                    type: "message",
                    role: "system",
                    content: [{
                        type: "text",
                        text: "You are a helpful AI assistant. Please respond in Chinese."
                    }]
                }
            }));
            
            // 3. Create response (request AI to speak)
            minimaxWs.send(JSON.stringify({
                type: messageTypes.RESPONSE_CREATE
            }));

            console.log('Initial context and response request sent to MiniMax.');

            // Forward connection status to frontend once setup is initiated
            // The actual 'ready' state might depend on Minimax's response (e.g., session.created)
            if (clientWs.readyState === WebSocket.OPEN) {
                clientWs.send(JSON.stringify({
                    type: 'connection_status',
                    connected: true, 
                    minimax_session_initiated: true, 
                    message: 'MiniMax session setup initiated.'
                }));
            }
        }, 100); 
    });

    minimaxWs.on('message', (data) => {
        try {
            const message = JSON.parse(data.toString());
            console.log('Received MiniMax message:', message.type);
            
            // Handle different message types from MiniMax
            switch (message.type) {
                case responseTypes.RESPONSE_AUDIO_TRANSCRIPT_DELTA:
                    console.log('Received RESPONSE_AUDIO_TRANSCRIPT_DELTA:', message.delta);
                    // Forward transcript delta to frontend
                    if (clientWs.readyState === WebSocket.OPEN) {
                        clientWs.send(JSON.stringify({
                            type: message.type,
                            delta: message.delta,
                            item_id: message.item_id,
                            output_index: message.output_index,
                            content_index: message.content_index
                        }));
                    }
                    break;

                case responseTypes.RESPONSE_AUDIO_DELTA:
                    // Accumulate audio chunks
                    if (message.delta && message.delta.audio) {
                        const audioBuffer = audioBuffers.get(clientWs) || [];
                        audioBuffer.push(message.delta.audio);
                        audioBuffers.set(clientWs, audioBuffer);
                    }
                    break;

                case responseTypes.RESPONSE_DONE:
                    // Send complete response with accumulated audio
                    if (clientWs.readyState === WebSocket.OPEN) {
                        const audioBuffer = audioBuffers.get(clientWs) || [];
                        const completeAudio = audioBuffer.join('');
                        
                        clientWs.send(JSON.stringify({
                            type: message.type,
                            response: message.response
                        }));
                        
                        // Clear audio buffer
                        audioBuffers.set(clientWs, []);
                    }
                    break;

                case responseTypes.ERROR:
                    // Forward error to frontend
                    if (clientWs.readyState === WebSocket.OPEN) {
                        clientWs.send(JSON.stringify({
                            type: 'error',
                            error: message.error,
                            message: message.error?.message || 'Unknown error occurred'
                        }));
                    }
                    break;

                default:
                    // Forward any other messages
                    if (clientWs.readyState === WebSocket.OPEN) {
                        clientWs.send(JSON.stringify(message));
                    }
                    break;
            }
        } catch (error) {
            console.error('Failed to parse MiniMax message:', error);
            if (clientWs.readyState === WebSocket.OPEN) {
                clientWs.send(JSON.stringify({
                    type: 'error',
                    message: 'Failed to process server response'
                }));
            }
        }
    });

    minimaxWs.on('error', (error) => {
        console.error('MiniMax connection error:', error);
        if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(JSON.stringify({
                type: 'error',
                message: `MiniMax connection failed: ${error.message}`
            }));
        }
    });

    minimaxWs.on('close', (code, reason) => {
        console.log('MiniMax connection closed:', code, reason);
        if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.send(JSON.stringify({
                type: 'connection_status',
                connected: false,
                model: 'abab6.5s-chat',
                message: `Connection closed: ${reason || 'Unknown reason'}`
            }));
        }
        // Clean up audio buffer
        audioBuffers.delete(clientWs);
    });

    // Frontend client message handling
    clientWs.on('message', (data) => {
        try {
            const message = JSON.parse(data.toString());
            console.log('Received frontend message:', message.type);
            
            // Handle different message types from frontend
            switch (message.type) {
                case messageTypes.INPUT_AUDIO_BUFFER_APPEND:
                    // Forward audio append to MiniMax
                    if (minimaxWs.readyState === WebSocket.OPEN) {
                        minimaxWs.send(JSON.stringify({
                            type: message.type,
                            audio: message.audio
                        }));
                    }
                    break;

                case messageTypes.INPUT_AUDIO_BUFFER_COMMIT:
                    // Forward audio commit to MiniMax
                    if (minimaxWs.readyState === WebSocket.OPEN) {
                        minimaxWs.send(JSON.stringify({
                            type: message.type
                        }));
                    }
                    break;

                case messageTypes.CONVERSATION_ITEM_CREATE:
                    // Create conversation item (text input)
                    if (minimaxWs.readyState === WebSocket.OPEN) {
                        minimaxWs.send(JSON.stringify({
                            type: message.type,
                            item: message.item
                        }));
                    }
                    break;

                case 'user_message':
                    // Handle text messages from user
                    if (minimaxWs.readyState === WebSocket.OPEN) {
                        minimaxWs.send(JSON.stringify({
                            type: messageTypes.CONVERSATION_ITEM_CREATE,
                            item: {
                                type: 'message',
                                role: 'user',
                                content: [
                                    {
                                        type: 'text',
                                        text: message.text
                                    }
                                ]
                            }
                        }));
                        
                        // Then request a response
                        minimaxWs.send(JSON.stringify({
                            type: messageTypes.RESPONSE_CREATE,
                            response: {
                                modalities: ["text", "audio"],
                                instructions: "Please respond in Korean.",
                                voice: "female-1",
                                output_audio_format: "pcm16",
                                temperature: 0.7,
                                max_output_tokens: 2048
                            }
                        }));
                    }
                    break;

                default:
                    // Forward any other messages directly
                    if (minimaxWs.readyState === WebSocket.OPEN) {
                        minimaxWs.send(JSON.stringify(message));
                    }
                    break;
            }
        } catch (error) {
            console.error('Failed to parse frontend message:', error);
            clientWs.send(JSON.stringify({
                type: 'error',
                message: 'Message format error'
            }));
        }
    });

    // Frontend client disconnect handling
    clientWs.on('close', () => {
        console.log('Frontend client disconnected');
        
        // Close corresponding MiniMax connection
        if (minimaxWs.readyState === WebSocket.OPEN) {
            minimaxWs.close();
        }
        
        // Clean up connection mapping and audio buffer
        clientConnections.delete(clientWs);
        audioBuffers.delete(clientWs);
    });

    clientWs.on('error', (error) => {
        console.error('Frontend client connection error:', error);
    });
});

// HTTP health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        connections: clientConnections.size
    });
});

// Start server
const PORT = process.env.PORT || 3003;
server.listen(PORT, () => {
    console.log(`MiniMax realtime chat proxy server running on port ${PORT}`);
    console.log(`WebSocket endpoint: ws://localhost:${PORT}/ws/realtime-chat`);
    console.log(`Health check: http://localhost:${PORT}/health`);
    
    if (!API_KEY) {
        console.warn('WARNING: MINIMAX_API_KEY not found in environment variables!');
    }
});

// Graceful shutdown handling
process.on('SIGTERM', () => {
    console.log('Received SIGTERM signal, shutting down server...');
    
    // Close all WebSocket connections
    clientConnections.forEach((minimaxWs, clientWs) => {
        if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.close(1000, 'Server shutting down');
        }
        if (minimaxWs.readyState === WebSocket.OPEN) {
            minimaxWs.close(1000, 'Server shutting down');
        }
    });
    
    // Clear audio buffers
    audioBuffers.clear();
    
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log('Received SIGINT signal, shutting down server...');
    process.emit('SIGTERM');
});