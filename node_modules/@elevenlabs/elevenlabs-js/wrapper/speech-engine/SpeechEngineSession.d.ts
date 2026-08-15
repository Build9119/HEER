import { type SpeechEngineEventMap, type SpeechEngineEventName, type WebSocketLike } from "./types";
/**
 * Wraps a WebSocket connection from the ElevenLabs Speech Engine API into a
 * typed, event-driven session.
 *
 * The ElevenLabs API connects to the developer's server via WebSocket. Each
 * connection represents one conversation. The session emits events for
 * transcripts and lifecycle changes, and provides methods to send LLM
 * responses back. When a new transcript arrives, the previous transcript's
 * abort signal is fired automatically, cancelling any in-flight LLM call.
 *
 * @example
 * ```typescript
 * import { SpeechEngine } from "@elevenlabs/elevenlabs-js";
 *
 * wss.on("connection", (ws) => {
 *     const session = new SpeechEngine.Session(ws);
 *
 *     session.on(SpeechEngine.USER_TRANSCRIPT, async (transcript, { signal }) => {
 *         const response = await llm.generate(transcript, { signal });
 *         session.sendResponse(response);
 *     });
 * });
 * ```
 */
export declare class SpeechEngineSession {
    private ws;
    private emitter;
    private currentAbortController;
    private currentEventId;
    private inTranscriptHandler;
    private _conversationId;
    private closed;
    private log;
    constructor(ws: WebSocketLike, options?: {
        debug?: boolean;
    });
    on<E extends SpeechEngineEventName>(event: E, listener: (...args: SpeechEngineEventMap[E]) => void): this;
    off<E extends SpeechEngineEventName>(event: E, listener: (...args: SpeechEngineEventMap[E]) => void): this;
    once<E extends SpeechEngineEventName>(event: E, listener: (...args: SpeechEngineEventMap[E]) => void): this;
    /**
     * Send an LLM response back to the Speech Engine API for TTS synthesis.
     *
     * Accepts a complete string, an `AsyncIterable<string>` for streaming
     * token-by-token responses, or an LLM stream that yields event objects
     * (e.g. an OpenAI Responses API stream). Event objects are automatically
     * parsed to extract text deltas.
     */
    sendResponse(response: string | AsyncIterable<unknown>): Promise<void>;
    /**
     * Close the session and the underlying WebSocket connection.
     */
    close(): void;
    /**
     * The conversation ID assigned by the Speech Engine API, available after
     * the `init` event.
     */
    get conversationId(): string | undefined;
    /**
     * Whether the session is still open.
     */
    get isOpen(): boolean;
    private setupWebSocket;
    private handleMessage;
    private streamResponse;
    /**
     * Extract text content from a stream chunk. Handles plain strings and
     * common LLM stream event formats:
     *
     * - OpenAI Responses API (`response.output_text.delta`)
     * - OpenAI Chat Completions API (`choices[0].delta.content`)
     * - Anthropic Messages API (`content_block_delta` with `text_delta`)
     * - Google Gemini API (`candidates[0].content.parts[0].text`)
     */
    private extractText;
    private sendAgentResponse;
    private send;
    private abortCurrent;
}
