import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const AudioIsolationHistoryItemResponseModel: core.serialization.ObjectSchema<serializers.AudioIsolationHistoryItemResponseModel.Raw, ElevenLabs.AudioIsolationHistoryItemResponseModel>;
export declare namespace AudioIsolationHistoryItemResponseModel {
    interface Raw {
        id: string;
        title?: string | null;
        created_at_unix: number;
        format: string;
        duration_seconds?: number | null;
        download_url?: string | null;
        icon_url?: string | null;
        source_video_url?: string | null;
        supports_video: boolean;
        processing: boolean;
        video_processing_failed: boolean;
        preview_b64?: string | null;
    }
}
