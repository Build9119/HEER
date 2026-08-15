import type * as ElevenLabs from "../index";
export interface AudioAnalysisResult {
    title: string;
    description: string;
    contentType?: string;
    overallPacing?: string;
    segments?: ElevenLabs.AudioSegment[];
    keyMoments?: ElevenLabs.AudioKeyMoment[];
}
