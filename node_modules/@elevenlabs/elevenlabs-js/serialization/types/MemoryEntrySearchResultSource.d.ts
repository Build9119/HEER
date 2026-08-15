import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationSource } from "./ConversationSource";
import { ManualSource } from "./ManualSource";
export declare const MemoryEntrySearchResultSource: core.serialization.Schema<serializers.MemoryEntrySearchResultSource.Raw, ElevenLabs.MemoryEntrySearchResultSource>;
export declare namespace MemoryEntrySearchResultSource {
    type Raw = ConversationSource.Raw | ManualSource.Raw;
}
