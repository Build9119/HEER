/**
 * @example
 *     {}
 */
export interface BodyUpdateDocumentV1ConvaiKnowledgeBaseDocumentationIdPatch {
    /** A custom, human-readable name for the document. */
    name?: string;
    /** Updated content for the document. Only supported for text documents, URL documents with auto-sync disabled, and file documents. */
    content?: string;
}
