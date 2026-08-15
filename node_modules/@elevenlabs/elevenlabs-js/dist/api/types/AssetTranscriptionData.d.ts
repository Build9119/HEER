export interface AssetTranscriptionData {
    languageCode: string;
    text: string;
    words: string[];
    wordStartTimesMs: number[];
    wordEndTimesMs: number[];
    wordSpeakerIds: (string | undefined)[];
}
