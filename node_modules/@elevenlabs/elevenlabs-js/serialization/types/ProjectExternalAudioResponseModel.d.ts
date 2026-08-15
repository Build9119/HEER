import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AssetTranscription } from "./AssetTranscription";
import { AudioAnalysis } from "./AudioAnalysis";
import { PendingBlocksMetadataModel } from "./PendingBlocksMetadataModel";
import { PendingClipTask } from "./PendingClipTask";
import { PendingExternalAudiosMetadataModel } from "./PendingExternalAudiosMetadataModel";
import { ProjectExternalAudioResponseModelSourceContext } from "./ProjectExternalAudioResponseModelSourceContext";
export declare const ProjectExternalAudioResponseModel: core.serialization.ObjectSchema<serializers.ProjectExternalAudioResponseModel.Raw, ElevenLabs.ProjectExternalAudioResponseModel>;
export declare namespace ProjectExternalAudioResponseModel {
    interface Raw {
        external_audio_id: string;
        filename: string;
        signed_url?: string | null;
        offset_ms: number;
        duration_ms: number;
        start_time_ms: number;
        end_time_ms?: number | null;
        order: string;
        track_id: string;
        created_at_ms: number;
        updated_at_ms: number;
        volume_gain_db?: number | null;
        muted?: boolean | null;
        fade_in_ms?: number | null;
        fade_out_ms?: number | null;
        source_external_audio_id?: string | null;
        source_asset_id?: string | null;
        source_platform_asset_id?: string | null;
        pending_blocks_metadata?: PendingBlocksMetadataModel.Raw | null;
        pending_external_audios_metadata?: PendingExternalAudiosMetadataModel.Raw | null;
        speech_imported?: boolean | null;
        pending_task?: PendingClipTask.Raw | null;
        error?: string | null;
        current_snapshot_id?: string | null;
        source_context?: ProjectExternalAudioResponseModelSourceContext.Raw | null;
        analysis?: AudioAnalysis.Raw | null;
        transcription?: AssetTranscription.Raw | null;
        import_speech_progress?: number | null;
    }
}
