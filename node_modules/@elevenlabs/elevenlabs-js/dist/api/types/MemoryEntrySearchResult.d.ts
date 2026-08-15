import type * as ElevenLabs from "../index";
export interface MemoryEntrySearchResult {
    entryId: string;
    version: number;
    summary?: string;
    text?: string;
    source?: ElevenLabs.MemoryEntrySearchResultSource;
}
