/**
 * Returned by `engine.attach()`. Call `.close()` to stop accepting connections
 * without affecting the HTTP server.
 */
export declare class SpeechEngineAttachment {
    private wss;
    private httpServer;
    private upgradeListener;
    /** @internal */
    constructor(wss: {
        close(cb?: (err?: Error) => void): void;
    }, httpServer?: {
        removeListener(event: string, listener: (...args: unknown[]) => void): void;
    }, upgradeListener?: (...args: unknown[]) => void);
    /**
     * Stop accepting new connections, remove the upgrade listener from the HTTP
     * server, and close the underlying WebSocket server.
     * Does not affect the HTTP server the attachment was created from.
     */
    close(): Promise<void>;
}
