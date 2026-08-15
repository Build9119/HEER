import type * as ElevenLabs from "../../../../../../../../../../index";
/**
 * @example
 *     {
 *         embeddingModel: "e5_mistral_7b_instruct"
 *     }
 */
export interface ChunkGetRequest {
    /** The embedding model used to retrieve the chunk. */
    embeddingModel?: ElevenLabs.EmbeddingModelEnum;
}
