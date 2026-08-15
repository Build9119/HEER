import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { StudioClipReferenceClipType } from "./StudioClipReferenceClipType";
export declare const StudioClipReference: core.serialization.ObjectSchema<serializers.StudioClipReference.Raw, ElevenLabs.StudioClipReference>;
export declare namespace StudioClipReference {
    interface Raw {
        project_id: string;
        chapter_id: string;
        clip_type: StudioClipReferenceClipType.Raw;
        clip_id: string;
        block_id?: string | null;
        preview_url?: string | null;
    }
}
