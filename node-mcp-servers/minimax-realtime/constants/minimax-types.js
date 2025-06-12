export const messageTypes = {
    SESSION_UPDATE: 'session.update',
    RESPONSE_CREATE: 'response.create',
    INPUT_AUDIO_BUFFER_APPEND: 'input_audio_buffer.append',
    INPUT_AUDIO_BUFFER_COMMIT: 'input_audio_buffer.commit',
    CONVERSATION_ITEM_CREATE: 'conversation.item.create'
};

export const responseTypes = {
    SESSION_CREATED: 'session.created',
    SESSION_UPDATED: 'session.updated',
    CONVERSATION_ITEM_CREATED: 'conversation.item.created',
    RESPONSE_CREATED: 'response.created',
    RESPONSE_DONE: 'response.done',
    RESPONSE_OUTPUT_ITEM_ADDED: 'response.output_item.added',
    RESPONSE_OUTPUT_ITEM_DONE: 'response.output_item.done',
    RESPONSE_TEXT_DELTA: 'response.text.delta',
    RESPONSE_TEXT_DONE: 'response.text.done',
    RESPONSE_AUDIO_TRANSCRIPT_DELTA: 'response.audio_transcript.delta',
    RESPONSE_AUDIO_TRANSCRIPT_DONE: 'response.audio_transcript.done',
    RESPONSE_AUDIO_DELTA: 'response.audio.delta',
    RESPONSE_AUDIO_DONE: 'response.audio.done',
    ERROR: 'error'
};
