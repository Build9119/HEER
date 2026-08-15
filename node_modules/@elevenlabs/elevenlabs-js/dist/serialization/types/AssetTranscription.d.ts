import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AssetTranscriptionData } from "./AssetTranscriptionData";
import { AssetTranscriptionStatus } from "./AssetTranscriptionStatus";
export declare const AssetTranscription: core.serialization.ObjectSchema<serializers.AssetTranscription.Raw, ElevenLabs.AssetTranscription>;
export declare namespace AssetTranscription {
    interface Raw {
        status: AssetTranscriptionStatus.Raw;
        data?: AssetTranscriptionData.Raw | null;
        updated_at_ms?: number | null;
    }
}
