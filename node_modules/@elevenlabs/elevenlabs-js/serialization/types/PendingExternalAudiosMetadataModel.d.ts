import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PendingExternalAudiosMetadataModel: core.serialization.ObjectSchema<serializers.PendingExternalAudiosMetadataModel.Raw, ElevenLabs.PendingExternalAudiosMetadataModel>;
export declare namespace PendingExternalAudiosMetadataModel {
    interface Raw {
        target_global_offset_ms?: number | null;
        external_audio_ids: string[];
    }
}
