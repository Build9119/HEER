import type * as ElevenLabs from "../index";
export interface KnowledgeBaseContentSearchResult {
    document: ElevenLabs.KnowledgeBaseContentSearchResultDocument;
    searchSnippet?: ElevenLabs.SearchHighlightSegment[];
    score: number;
}
