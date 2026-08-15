export interface AudioSegment {
    startMs: number;
    endMs: number;
    description: string;
    segmentType?: string;
    hasSpeech?: boolean;
    hasMusic?: boolean;
    pacing?: string;
}
