export interface VideoSegment {
    startMs: number;
    endMs: number;
    description: string;
    subjects?: string[];
    shotType?: string;
    cameraMovement?: string;
    transitionIn?: string;
    hasSpeech?: boolean;
    hasMusic?: boolean;
    pacing?: string;
}
