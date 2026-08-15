import type * as ElevenLabs from "../index";
export interface ReferenceVideo {
    generationId?: string;
    contentAssetId?: string;
    templateNodeId?: string;
    studioClip?: ElevenLabs.StudioClipReference;
}
