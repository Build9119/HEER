import type * as ElevenLabs from "../index";
export interface KnowledgeBaseDocumentChunksResponseModel {
    chunks: ElevenLabs.KnowledgeBaseDocumentChunkResponseModel[];
    nextCursor?: string;
}
