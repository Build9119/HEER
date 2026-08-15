import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { KnowledgeBaseDocumentChunkResponseModel } from "./KnowledgeBaseDocumentChunkResponseModel";
export declare const KnowledgeBaseDocumentChunksResponseModel: core.serialization.ObjectSchema<serializers.KnowledgeBaseDocumentChunksResponseModel.Raw, ElevenLabs.KnowledgeBaseDocumentChunksResponseModel>;
export declare namespace KnowledgeBaseDocumentChunksResponseModel {
    interface Raw {
        chunks: KnowledgeBaseDocumentChunkResponseModel.Raw[];
        next_cursor?: string | null;
    }
}
