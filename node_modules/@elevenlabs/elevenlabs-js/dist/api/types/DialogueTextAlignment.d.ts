/**
 * Character-level alignment data (field names use snake_case in JSON).
 */
export interface DialogueTextAlignment {
    chars?: string[];
    charStartTimesMs?: number[];
    charDurationsMs?: number[];
}
