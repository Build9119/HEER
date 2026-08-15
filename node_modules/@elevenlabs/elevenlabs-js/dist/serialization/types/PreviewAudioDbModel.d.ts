import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PreviewAudioDbModel: core.serialization.ObjectSchema<serializers.PreviewAudioDbModel.Raw, ElevenLabs.PreviewAudioDbModel>;
export declare namespace PreviewAudioDbModel {
    interface Raw {
        voice_id?: string | null;
        text?: string | null;
        audio_url: string;
        hls_manifest_url?: string | null;
        dash_manifest_url?: string | null;
        is_auto_generated?: boolean | null;
        generated_at_unix?: number | null;
    }
}
