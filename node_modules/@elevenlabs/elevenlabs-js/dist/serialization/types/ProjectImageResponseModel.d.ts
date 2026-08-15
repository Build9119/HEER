import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { CanvasPlacement } from "./CanvasPlacement";
import { ClipAnimation } from "./ClipAnimation";
import { ImageAnalysis } from "./ImageAnalysis";
import { PendingClipTask } from "./PendingClipTask";
export declare const ProjectImageResponseModel: core.serialization.ObjectSchema<serializers.ProjectImageResponseModel.Raw, ElevenLabs.ProjectImageResponseModel>;
export declare namespace ProjectImageResponseModel {
    interface Raw {
        image_id: string;
        filename: string;
        signed_url?: string | null;
        thumbnail_signed_url?: string | null;
        source?: "upload" | null;
        file_size_bytes: number;
        width: number;
        height: number;
        track_id?: string | null;
        offset_ms: number;
        duration_ms: number;
        order: string;
        canvas_placement: CanvasPlacement.Raw;
        animation?: ClipAnimation.Raw | null;
        opacity?: number | null;
        created_at_ms: number;
        updated_at_ms: number;
        current_snapshot_id?: string | null;
        source_asset_id?: string | null;
        source_platform_asset_id?: string | null;
        error?: string | null;
        pending_task?: PendingClipTask.Raw | null;
        analysis?: ImageAnalysis.Raw | null;
    }
}
