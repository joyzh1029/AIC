export const messageTypes = {
    RESPONSE_CREATE: 'response.create',
    INPUT_AUDIO_BUFFER_APPEND: 'input_audio_buffer.append',
    INPUT_AUDIO_BUFFER_COMMIT: 'input_audio_buffer.commit',
    CONVERSATION_ITEM_CREATE: 'conversation.item.create'
};

export const responseTypes = {
    RESPONSE_AUDIO_TRANSCRIPT_DELTA: 'response.audio_transcript.delta',
    RESPONSE_AUDIO_DELTA: 'response.audio.delta',
    RESPONSE_DONE: 'response.done',
    ERROR: 'error'
};
