import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { MemoryEntrySearchResultSource } from "./MemoryEntrySearchResultSource";
export declare const MemoryEntrySearchResult: core.serialization.ObjectSchema<serializers.MemoryEntrySearchResult.Raw, ElevenLabs.MemoryEntrySearchResult>;
export declare namespace MemoryEntrySearchResult {
    interface Raw {
        entry_id: string;
        version: number;
        summary?: string | null;
        text?: string | null;
        source?: MemoryEntrySearchResultSource.Raw | null;
    }
}
