import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { KnowledgeBaseContentSearchResult } from "./KnowledgeBaseContentSearchResult";
export declare const KnowledgeBaseContentSearchResponseModel: core.serialization.ObjectSchema<serializers.KnowledgeBaseContentSearchResponseModel.Raw, ElevenLabs.KnowledgeBaseContentSearchResponseModel>;
export declare namespace KnowledgeBaseContentSearchResponseModel {
    interface Raw {
        results: KnowledgeBaseContentSearchResult.Raw[];
        next_cursor?: string | null;
    }
}
