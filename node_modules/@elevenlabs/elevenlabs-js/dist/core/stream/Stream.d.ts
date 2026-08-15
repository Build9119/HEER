export declare namespace Stream {
    interface Args {
        /**
         * The HTTP response stream to read from.
         */
        stream: ReadableStream;
        /**
         * The event shape to use for parsing the stream data.
         */
        eventShape: JsonEvent | SseEvent;
        /**
         * An abort signal to stop the stream.
         */
        signal?: AbortSignal;
        /**
         * Whether transparent mid-stream reconnection is enabled on resumable
         * SSE endpoints. Defaults to true. Has no effect on non-resumable endpoints.
         */
        reconnectionEnabled?: boolean;
        /**
         * Maximum number of consecutive failed reconnect attempts on resumable SSE
         * endpoints before giving up. The counter resets to zero each time a
         * reconnected stream successfully yields at least one event (i.e. makes
         * progress). Has no effect on non-resumable endpoints.
         */
        maxReconnectionAttempts?: number;
        /**
         * A function that re-issues the HTTP request with the Last-Event-ID header
         * and returns the new response body stream. Required for reconnection to work.
         */
        reconnect?: (lastEventId: string) => Promise<ReadableStream>;
    }
    interface JsonEvent {
        type: "json";
        messageTerminator: string;
    }
    interface SseEvent {
        type: "sse";
        streamTerminator?: string;
        eventDiscriminator?: string;
        resumable?: boolean;
    }
}
export interface ServerSentEvent<T> {
    data: T;
    id?: string;
    retry?: number;
    event?: string;
}
export declare class Stream<T> implements AsyncIterable<T> {
    private stream;
    private parse;
    /**
     * The prefix to use for each message. For example,
     * for SSE, the prefix is "data: ".
     */
    private prefix;
    private messageTerminator;
    private streamTerminator;
    private eventDiscriminator;
    private resumable;
    private reconnectionEnabled;
    private maxReconnectionAttempts;
    private reconnect;
    private controller;
    private decoder;
    private externalSignal;
    private onExternalAbort;
    constructor({ stream, parse, eventShape, signal, reconnectionEnabled, maxReconnectionAttempts, reconnect, }: Stream.Args & {
        parse: (val: unknown) => Promise<T>;
    });
    private iterMessages;
    private iterDataMessages;
    private iterSseEvents;
    /**
     * Parses and returns a single SSE event, or returns null if the event is a stream terminator.
     */
    private dispatchSseEvent;
    /**
     * Determines whether a reconnection attempt should be made.
     */
    private shouldReconnect;
    /**
     * Delays before reconnecting, using a server-sent retry directive if provided
     * (clamped to MAX_RECONNECT_DELAY_MS), otherwise falling back to
     * DEFAULT_RECONNECT_DELAY_MS. The delay is abortable: if the stream's abort
     * signal fires during the wait, the promise resolves immediately.
     */
    private delayReconnect;
    private createEmptyStream;
    private removeAbortListener;
    withMetadata(): AsyncIterable<ServerSentEvent<T>>;
    private injectDiscriminator;
    [Symbol.asyncIterator](): AsyncIterator<T, void, unknown>;
    private decodeChunk;
}
/**
 * Browser polyfill for ReadableStream
 */
export declare function readableStreamAsyncIterable<T>(stream: any): AsyncIterableIterator<T>;
