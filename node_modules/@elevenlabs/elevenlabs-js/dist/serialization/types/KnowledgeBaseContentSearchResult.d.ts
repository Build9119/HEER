import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { KnowledgeBaseContentSearchResultDocument } from "./KnowledgeBaseContentSearchResultDocument";
import { SearchHighlightSegment } from "./SearchHighlightSegment";
export declare const KnowledgeBaseContentSearchResult: core.serialization.ObjectSchema<serializers.KnowledgeBaseContentSearchResult.Raw, ElevenLabs.KnowledgeBaseContentSearchResult>;
export declare namespace KnowledgeBaseContentSearchResult {
    interface Raw {
        document: KnowledgeBaseContentSearchResultDocument.Raw;
        search_snippet?: SearchHighlightSegment.Raw[] | null;
        score: number;
    }
}
