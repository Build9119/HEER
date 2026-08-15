import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PendingBlocksMetadataModel: core.serialization.ObjectSchema<serializers.PendingBlocksMetadataModel.Raw, ElevenLabs.PendingBlocksMetadataModel>;
export declare namespace PendingBlocksMetadataModel {
    interface Raw {
        target_global_offset_ms?: number | null;
        block_ids: string[];
    }
}
