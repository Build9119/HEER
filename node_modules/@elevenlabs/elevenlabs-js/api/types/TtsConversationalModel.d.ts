export declare const TtsConversationalModel: {
    /**
     * Deprecated: Use eleven_flash_v2 instead. */
    readonly ElevenTurboV2: "eleven_turbo_v2";
    /**
     * Deprecated: Use eleven_flash_v2_5 instead. */
    readonly ElevenTurboV25: "eleven_turbo_v2_5";
    readonly ElevenFlashV2: "eleven_flash_v2";
    readonly ElevenFlashV25: "eleven_flash_v2_5";
    readonly ElevenMultilingualV2: "eleven_multilingual_v2";
    readonly ElevenV3Conversational: "eleven_v3_conversational";
};
export type TtsConversationalModel = (typeof TtsConversationalModel)[keyof typeof TtsConversationalModel];
