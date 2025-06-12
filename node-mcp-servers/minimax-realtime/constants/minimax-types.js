// MiniMax Realtime API Types and Constants
// Based on MiniMax API documentation and server implementation

// ================================
// CLIENT TO SERVER EVENT TYPES
// ================================

export const clientMessageTypes = {
    // Session management
    SESSION_START: 'session.start',
    SESSION_UPDATE: 'session.update',
    SESSION_END: 'session.end',
    
    // Conversation management
    CONVERSATION_ITEM_CREATE: 'conversation.item.create',
    CONVERSATION_ITEM_DELETE: 'conversation.item.delete',
    CONVERSATION_ITEM_TRUNCATE: 'conversation.item.truncate',
    
    // Audio input buffer management
    INPUT_AUDIO_BUFFER_APPEND: 'input_audio_buffer.append',
    INPUT_AUDIO_BUFFER_COMMIT: 'input_audio_buffer.commit',
    INPUT_AUDIO_BUFFER_CLEAR: 'input_audio_buffer.clear',
    
    // Response management
    RESPONSE_CREATE: 'response.create',
    RESPONSE_CANCEL: 'response.cancel',
    
    // Real-time audio streaming
    REALTIME_INPUT_AUDIO_START: 'realtime.input_audio.start',
    REALTIME_INPUT_AUDIO_STOP: 'realtime.input_audio.stop'
};

// ================================
// SERVER TO CLIENT EVENT TYPES
// ================================

export const serverResponseTypes = {
    // Connection events
    CONNECTION_ESTABLISHED: 'connection.established',
    
    // Session events
    SESSION_CREATED: 'session.created',
    SESSION_UPDATED: 'session.updated',
    SESSION_ENDED: 'session.ended',
    
    // Conversation events
    CONVERSATION_CREATED: 'conversation.created',
    CONVERSATION_ITEM_CREATED: 'conversation.item.created',
    CONVERSATION_ITEM_DELETED: 'conversation.item.deleted',
    CONVERSATION_ITEM_TRUNCATED: 'conversation.item.truncated',
    
    // Audio transcription events
    CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED: 'conversation.item.input_audio_transcription.completed',
    CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_FAILED: 'conversation.item.input_audio_transcription.failed',
    
    // Audio buffer events
    INPUT_AUDIO_BUFFER_COMMITTED: 'input_audio_buffer.committed',
    INPUT_AUDIO_BUFFER_CLEARED: 'input_audio_buffer.cleared',
    INPUT_AUDIO_BUFFER_SPEECH_STARTED: 'input_audio_buffer.speech_started',
    INPUT_AUDIO_BUFFER_SPEECH_STOPPED: 'input_audio_buffer.speech_stopped',
    
    // Response events
    RESPONSE_CREATED: 'response.created',
    RESPONSE_DONE: 'response.done',
    RESPONSE_CANCELLED: 'response.cancelled',
    
    // Response output events
    RESPONSE_OUTPUT_ITEM_ADDED: 'response.output_item.added',
    RESPONSE_OUTPUT_ITEM_DONE: 'response.output_item.done',
    
    // Response content part events
    RESPONSE_CONTENT_PART_ADDED: 'response.content_part.added',
    RESPONSE_CONTENT_PART_DONE: 'response.content_part.done',
    
    // Text response events
    RESPONSE_TEXT_DELTA: 'response.text.delta',
    RESPONSE_TEXT_DONE: 'response.text.done',
    
    // Audio response events
    RESPONSE_AUDIO_DELTA: 'response.audio.delta',
    RESPONSE_AUDIO_DONE: 'response.audio.done',
    RESPONSE_AUDIO_TRANSCRIPT_DELTA: 'response.audio_transcript.delta',
    RESPONSE_AUDIO_TRANSCRIPT_DONE: 'response.audio_transcript.done',
    
    // Function call events
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DELTA: 'response.function_call_arguments.delta',
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE: 'response.function_call_arguments.done',
    
    // Rate limit events
    RATE_LIMITS_UPDATED: 'rate_limits.updated',
    
    // Error event
    ERROR: 'error'
};

// ================================
// CONTENT TYPES
// ================================

export const contentTypes = {
    // Input content types
    INPUT_TEXT: 'input_text',
    INPUT_AUDIO: 'input_audio',
    
    // Output content types
    TEXT: 'text',
    AUDIO: 'audio',
    
    // Function call content types
    FUNCTION_CALL: 'function_call',
    FUNCTION_CALL_OUTPUT: 'function_call_output'
};

// ================================
// ITEM TYPES
// ================================

export const itemTypes = {
    MESSAGE: 'message',
    FUNCTION_CALL: 'function_call',
    FUNCTION_CALL_OUTPUT: 'function_call_output'
};

// ================================
// ROLES
// ================================

export const roles = {
    SYSTEM: 'system',
    USER: 'user',
    ASSISTANT: 'assistant'
};

// ================================
// MODALITIES
// ================================

export const modalities = {
    TEXT: 'text',
    AUDIO: 'audio'
};

// ================================
// AUDIO FORMATS
// ================================

export const audioFormats = {
    // MiniMax supports PCM 16-bit 24kHz mono
    PCM16_24KHZ_MONO: 'pcm16',
    PCM16: 'pcm16'
};

// ================================
// AUDIO SPECIFICATIONS
// ================================

export const audioSpecs = {
    FORMAT: 'PCM',
    BITS: 16,
    SAMPLE_RATE: 24000,
    CHANNELS: 1, // Mono
    ENCODING: 'base64'
};

// ================================
// MODELS
// ================================

export const models = {
    ABAB6_5S_CHAT: 'abab6.5s-chat'
};

// ================================
// CONNECTION STATES
// ================================

export const connectionStates = {
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    DISCONNECTING: 'disconnecting',
    DISCONNECTED: 'disconnected',
    ERROR: 'error'
};

// ================================
// SESSION STATES
// ================================

export const sessionStates = {
    CREATING: 'creating',
    ACTIVE: 'active',
    ENDING: 'ending',
    ENDED: 'ended'
};

// ================================
// RESPONSE STATES
// ================================

export const responseStates = {
    GENERATING: 'generating',
    COMPLETED: 'completed',
    CANCELLED: 'cancelled',
    FAILED: 'failed'
};

// ================================
// ERROR CODES
// ================================

export const errorCodes = {
    // Authentication errors
    INVALID_API_KEY: 'invalid_api_key',
    INSUFFICIENT_QUOTA: 'insufficient_quota',
    
    // Connection errors
    CONNECTION_FAILED: 'connection_failed',
    CONNECTION_TIMEOUT: 'connection_timeout',
    
    // Session errors
    SESSION_NOT_FOUND: 'session_not_found',
    SESSION_EXPIRED: 'session_expired',
    
    // Request errors
    INVALID_REQUEST: 'invalid_request',
    INVALID_AUDIO_FORMAT: 'invalid_audio_format',
    AUDIO_TOO_LONG: 'audio_too_long',
    
    // Rate limit errors
    RATE_LIMIT_EXCEEDED: 'rate_limit_exceeded',
    
    // Server errors
    INTERNAL_ERROR: 'internal_error',
    SERVICE_UNAVAILABLE: 'service_unavailable'
};

// ================================
// VALIDATION FUNCTIONS
// ================================

/**
 * Validate if a message type is a valid client message type
 * @param {string} type - The message type to validate
 * @returns {boolean} - True if valid
 */
export function isValidClientMessageType(type) {
    return Object.values(clientMessageTypes).includes(type);
}

/**
 * Validate if a response type is a valid server response type
 * @param {string} type - The response type to validate
 * @returns {boolean} - True if valid
 */
export function isValidServerResponseType(type) {
    return Object.values(serverResponseTypes).includes(type);
}

/**
 * Validate if a content type is valid
 * @param {string} type - The content type to validate
 * @returns {boolean} - True if valid
 */
export function isValidContentType(type) {
    return Object.values(contentTypes).includes(type);
}

/**
 * Validate if a role is valid
 * @param {string} role - The role to validate
 * @returns {boolean} - True if valid
 */
export function isValidRole(role) {
    return Object.values(roles).includes(role);
}

/**
 * Validate if a modality is valid
 * @param {string} modality - The modality to validate
 * @returns {boolean} - True if valid
 */
export function isValidModality(modality) {
    return Object.values(modalities).includes(modality);
}

/**
 * Validate if an audio format is valid
 * @param {string} format - The audio format to validate
 * @returns {boolean} - True if valid
 */
export function isValidAudioFormat(format) {
    return Object.values(audioFormats).includes(format);
}

/**
 * Validate if a model is valid
 * @param {string} model - The model to validate
 * @returns {boolean} - True if valid
 */
export function isValidModel(model) {
    return Object.values(models).includes(model);
}

// ================================
// UTILITY FUNCTIONS
// ================================

/**
 * Create a text message item
 * @param {string} text - The text content
 * @param {string} role - The role (user, assistant, system)
 * @returns {Object} - Message item object
 */
export function createTextMessage(text, role = roles.USER) {
    return {
        type: itemTypes.MESSAGE,
        role: role,
        content: [{
            type: contentTypes.INPUT_TEXT,
            text: text
        }]
    };
}

/**
 * Create an audio message item
 * @param {string} audioBase64 - Base64 encoded audio data
 * @param {string} role - The role (user, assistant, system)
 * @returns {Object} - Message item object
 */
export function createAudioMessage(audioBase64, role = roles.USER) {
    return {
        type: itemTypes.MESSAGE,
        role: role,
        content: [{
            type: contentTypes.INPUT_AUDIO,
            audio: audioBase64
        }]
    };
}

/**
 * Create a session start message
 * @param {Object} options - Session options
 * @returns {Object} - Session start message
 */
export function createSessionStart(options = {}) {
    return {
        type: clientMessageTypes.SESSION_START,
        instructions: options.instructions || 'Please assist the user.',
        modalities: options.modalities || [modalities.TEXT],
        voice: options.voice,
        input_audio_format: options.inputAudioFormat || audioFormats.PCM16,
        output_audio_format: options.outputAudioFormat || audioFormats.PCM16,
        input_audio_transcription: options.inputAudioTranscription,
        turn_detection: options.turnDetection,
        tools: options.tools,
        tool_choice: options.toolChoice,
        temperature: options.temperature,
        max_response_output_tokens: options.maxResponseOutputTokens
    };
}

/**
 * Create a conversation item create message
 * @param {Object} item - The item to create
 * @returns {Object} - Conversation item create message
 */
export function createConversationItem(item) {
    return {
        type: clientMessageTypes.CONVERSATION_ITEM_CREATE,
        item: item
    };
}

/**
 * Create a response create message
 * @param {Object} options - Response options
 * @returns {Object} - Response create message
 */
export function createResponseCreate(options = {}) {
    return {
        type: clientMessageTypes.RESPONSE_CREATE,
        response: {
            modalities: options.modalities || [modalities.TEXT],
            instructions: options.instructions,
            voice: options.voice,
            output_audio_format: options.outputAudioFormat,
            tools: options.tools,
            tool_choice: options.toolChoice,
            temperature: options.temperature,
            max_output_tokens: options.maxOutputTokens
        }
    };
}

/**
 * Parse base64 audio to ensure it meets MiniMax specifications
 * @param {string} audioBase64 - Base64 encoded audio
 * @returns {Object} - Validation result
 */
export function validateAudioData(audioBase64) {
    if (!audioBase64 || typeof audioBase64 !== 'string') {
        return { valid: false, error: 'Audio data must be a base64 string' };
    }
    
    // Basic base64 validation
    const base64Regex = /^[A-Za-z0-9+/]*={0,2}$/;
    if (!base64Regex.test(audioBase64)) {
        return { valid: false, error: 'Invalid base64 format' };
    }
    
    return { valid: true };
}

// ================================
// LEGACY COMPATIBILITY
// ================================

// Keep original naming for backward compatibility
export const messageTypes = clientMessageTypes;
export const responseTypes = serverResponseTypes;
export const isValidMessageType = isValidClientMessageType;
export const isValidResponseType = isValidServerResponseType;

// ================================
// DEFAULT EXPORTS
// ================================

export default {
    clientMessageTypes,
    serverResponseTypes,
    contentTypes,
    itemTypes,
    roles,
    modalities,
    audioFormats,
    audioSpecs,
    models,
    connectionStates,
    sessionStates,
    responseStates,
    errorCodes,
    
    // Validation functions
    isValidClientMessageType,
    isValidServerResponseType,
    isValidContentType,
    isValidRole,
    isValidModality,
    isValidAudioFormat,
    isValidModel,
    
    // Utility functions
    createTextMessage,
    createAudioMessage,
    createSessionStart,
    createConversationItem,
    createResponseCreate,
    validateAudioData,
    
    // Legacy compatibility
    messageTypes,
    responseTypes,
    isValidMessageType,
    isValidResponseType
};