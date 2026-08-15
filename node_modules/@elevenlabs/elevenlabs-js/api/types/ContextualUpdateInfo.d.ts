export interface ContextualUpdateInfo {
    /** Client-supplied identifier grouping related contextual updates. */
    contextId: string;
    /** True when this contextual update has been replaced by a newer update with the same context_id. */
    isSuperseded?: boolean;
}
