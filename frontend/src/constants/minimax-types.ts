// Re-exported MiniMax constants and helper functions for frontend use.
// Source: node-mcp-servers/minimax-realtime/constants/minimax-types.js
// NOTE: Keep this file in sync with backend version if API changes.

// ================================
// CLIENT TO SERVER EVENT TYPES
// ================================
export const clientMessageTypes = {
  SESSION_START: 'session.start', // legacy
  SESSION_CREATE: 'session.create',
  SESSION_UPDATE: 'session.update',
  SESSION_END: 'session.end',
  CONVERSATION_ITEM_CREATE: 'conversation.item.create',
  CONVERSATION_ITEM_DELETE: 'conversation.item.delete',
  CONVERSATION_ITEM_TRUNCATE: 'conversation.item.truncate',
  INPUT_AUDIO_BUFFER_APPEND: 'input_audio_buffer.append',
  INPUT_AUDIO_BUFFER_COMMIT: 'input_audio_buffer.commit',
  INPUT_AUDIO_BUFFER_CLEAR: 'input_audio_buffer.clear',
  RESPONSE_CREATE: 'response.create',
  RESPONSE_CANCEL: 'response.cancel',
  REALTIME_INPUT_AUDIO_START: 'realtime.input_audio.start',
  REALTIME_INPUT_AUDIO_STOP: 'realtime.input_audio.stop'
} as const;

// ================================
// SERVER TO CLIENT EVENT TYPES
// ================================
export const serverResponseTypes = {
  CONNECTION_ESTABLISHED: 'connection.established',
  SESSION_CREATED: 'session.created',
  SESSION_UPDATED: 'session.updated',
  SESSION_ENDED: 'session.ended',
  CONVERSATION_CREATED: 'conversation.created',
  CONVERSATION_ITEM_CREATED: 'conversation.item.created',
  CONVERSATION_ITEM_DELETED: 'conversation.item.deleted',
  CONVERSATION_ITEM_TRUNCATED: 'conversation.item.truncated',
  CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED: 'conversation.item.input_audio_transcription.completed',
  CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_FAILED: 'conversation.item.input_audio_transcription.failed',
  RESPONSE_CREATED: 'response.created',
  RESPONSE_DONE: 'response.done',
  RESPONSE_CANCELLED: 'response.cancelled',
  RESPONSE_OUTPUT_ITEM_ADDED: 'response.output_item.added',
  RESPONSE_OUTPUT_ITEM_DONE: 'response.output_item.done',
  RESPONSE_CONTENT_PART_ADDED: 'response.content_part.added',
  RESPONSE_CONTENT_PART_DONE: 'response.content_part.done',
  RESPONSE_TEXT_DELTA: 'response.text.delta',
  RESPONSE_TEXT_DONE: 'response.text.done',
  RESPONSE_AUDIO_DELTA: 'response.audio.delta',
  RESPONSE_AUDIO_DONE: 'response.audio.done',
  RESPONSE_AUDIO_TRANSCRIPT_DELTA: 'response.audio_transcript.delta',
  RESPONSE_AUDIO_TRANSCRIPT_DONE: 'response.audio_transcript.done',
  RESPONSE_FUNCTION_CALL_ARGUMENTS_DELTA: 'response.function_call_arguments.delta',
  RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE: 'response.function_call_arguments.done',
  INPUT_AUDIO_BUFFER_COMMITTED: 'input_audio_buffer.committed',
  RATE_LIMITS_UPDATED: 'rate_limits.updated',
  ERROR: 'error'
} as const;

// ================================
// CONTENT TYPES & ITEM TYPES
// ================================
export const contentTypes = {
  INPUT_TEXT: 'input_text',
  INPUT_AUDIO: 'input_audio',
  TEXT: 'text',
  AUDIO: 'audio',
  FUNCTION_CALL: 'function_call',
  FUNCTION_CALL_OUTPUT: 'function_call_output'
} as const;

export const itemTypes = {
  MESSAGE: 'message',
  FUNCTION_CALL: 'function_call',
  TOOL_CALL: 'tool_call'
} as const;

// ================================
// ROLES & MODALITIES
// ================================
export const roles = {
  SYSTEM: 'system',
  USER: 'user',
  ASSISTANT: 'assistant'
} as const;

export const modalities = {
  TEXT: 'text',
  AUDIO: 'audio'
} as const;

// ================================
// AUDIO CONFIG
// ================================
export const audioFormats = {
  PCM16_24KHZ_MONO: 'pcm16',
  PCM16: 'pcm16'
} as const;

export const audioSpecs = {
  FORMAT: 'PCM',
  BITS: 16,
  SAMPLE_RATE: 24000,
  CHANNELS: 1,
  ENCODING: 'base64'
} as const;

// ================================
// STATES
// ================================
export const connectionStates = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTING: 'disconnecting',
  DISCONNECTED: 'disconnected',
  ERROR: 'error'
} as const;

export const sessionStates = {
  CREATING: 'creating',
  ACTIVE: 'active',
  ENDING: 'ending',
  ENDED: 'ended'
} as const;

export const responseStates = {
  GENERATING: 'generating',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
  FAILED: 'failed'
} as const;

// ================================
// HELPER VALIDATION FUNCTIONS
// ================================
export const isValidClientMessageType = (type: string): boolean => Object.values(clientMessageTypes).includes(type as any);
export const isValidServerResponseType = (type: string): boolean => Object.values(serverResponseTypes).includes(type as any);
export const isValidContentType = (type: string): boolean => Object.values(contentTypes).includes(type as any);
export const isValidRole = (role: string): boolean => Object.values(roles).includes(role as any);
export const isValidAudioFormat = (format: string): boolean => Object.values(audioFormats).includes(format as any);

// ================================
// UTILITY BUILDERS (minimal subset)
// ================================
export const createTextMessage = (text: string, role: keyof typeof roles = 'USER') => ({
  type: itemTypes.MESSAGE,
  role: roles[role],
  content: [{ type: contentTypes.INPUT_TEXT, text }],
  status: 'completed' // Required status field for MiniMax API
});

export const createAudioMessage = (audioBase64: string, role: keyof typeof roles = 'USER') => ({
  type: itemTypes.MESSAGE,
  role: roles[role],
  content: [{ type: contentTypes.INPUT_AUDIO, audio: audioBase64 }],
  status: 'completed' // Required status field for MiniMax API
});

export const createSessionStart = (opts: {
  instructions?: string;
  modalities?: string[];
  voice?: string;
  inputAudioFormat?: string;
  outputAudioFormat?: string;
  temperature?: number;
  maxResponseOutputTokens?: number;
} = {}) => ({
  type: clientMessageTypes.SESSION_CREATE,
  instructions: opts.instructions ?? 'Please assist the user.',
  modalities: opts.modalities ?? [modalities.TEXT],
  voice: opts.voice,
  input_audio_format: opts.inputAudioFormat ?? audioFormats.PCM16,
  output_audio_format: opts.outputAudioFormat ?? audioFormats.PCM16,
  temperature: opts.temperature,
  max_response_output_tokens: opts.maxResponseOutputTokens
});

export const createConversationItem = (item: any) => {
  // Ensure the item has the required type and status fields,
  // overriding any provided in 'item' to ensure API compliance for this helper.
  const finalItem = {
    ...item, // User-provided parts like role, content
    type: itemTypes.MESSAGE, // Ensure this is always 'message'
    status: 'completed'     // Ensure this is always 'completed'
  };
  return {
    type: clientMessageTypes.CONVERSATION_ITEM_CREATE, // This is 'conversation.item.create'
    item: finalItem
  };
};

export const createResponseCreate = (opts: {
  modalities?: string[];
  instructions?: string;
  voice?: string;
  outputAudioFormat?: string;
  temperature?: number;
  maxOutputTokens?: number;
} = {}) => ({
  type: clientMessageTypes.RESPONSE_CREATE,
  response: {
    modalities: opts.modalities ?? [modalities.TEXT],
    instructions: opts.instructions,
    voice: opts.voice,
    output_audio_format: opts.outputAudioFormat,
    temperature: opts.temperature,
    max_output_tokens: opts.maxOutputTokens
  }
});

export const validateAudioData = (audioBase64: string): { valid: boolean; error?: string } => {
  if (!audioBase64 || typeof audioBase64 !== 'string') return { valid: false, error: 'Audio must be base64 string' };
  const base64Regex = /^[A-Za-z0-9+/]*={0,2}$/;
  if (!base64Regex.test(audioBase64)) return { valid: false, error: 'Invalid base64 format' };
  return { valid: true };
};

// default export for convenience
export default {
  clientMessageTypes,
  serverResponseTypes,
  contentTypes,
  itemTypes,
  roles,
  modalities,
  audioFormats,
  audioSpecs,
  connectionStates,
  sessionStates,
  responseStates,
  isValidClientMessageType,
  isValidServerResponseType,
  createTextMessage,
  createAudioMessage,
  createSessionStart,
  createConversationItem,
  createResponseCreate,
  validateAudioData
};
