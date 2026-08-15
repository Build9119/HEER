import type * as ElevenLabs from "../index";
export interface VideoAnalysisResult {
    title: string;
    description: string;
    contentType?: string;
    overallPacing?: string;
    subjects?: ElevenLabs.VideoSubject[];
    segments?: ElevenLabs.VideoSegment[];
    keyMoments?: ElevenLabs.VideoKeyMoment[];
}
