import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { StudioClipReference } from "./StudioClipReference";
export declare const ReferenceVideo: core.serialization.ObjectSchema<serializers.ReferenceVideo.Raw, ElevenLabs.ReferenceVideo>;
export declare namespace ReferenceVideo {
    interface Raw {
        generation_id?: string | null;
        content_asset_id?: string | null;
        template_node_id?: string | null;
        studio_clip?: StudioClipReference.Raw | null;
    }
}
