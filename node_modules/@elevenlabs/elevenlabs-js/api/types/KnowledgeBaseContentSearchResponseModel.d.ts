import type * as ElevenLabs from "../index";
export interface KnowledgeBaseContentSearchResponseModel {
    results: ElevenLabs.KnowledgeBaseContentSearchResult[];
    nextCursor?: string;
}
