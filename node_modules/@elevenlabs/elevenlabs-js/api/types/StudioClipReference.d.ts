import type * as ElevenLabs from "../index";
export interface StudioClipReference {
    projectId: string;
    chapterId: string;
    clipType: ElevenLabs.StudioClipReferenceClipType;
    clipId: string;
    blockId?: string;
    previewUrl?: string;
}
