/**
 * Context for sound effect clips.
 */
export interface SfxSourceContext {
    soundGenerationHistoryItemId?: string;
    text?: string;
    generationConfig?: Record<string, unknown>;
}
