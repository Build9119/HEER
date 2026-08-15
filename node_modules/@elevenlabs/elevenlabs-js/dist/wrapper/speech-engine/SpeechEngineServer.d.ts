import WebSocket from "ws";
import { type SpeechEngineCallbacks } from "./types";
import { SpeechEngineSession } from "./SpeechEngineSession";
export interface SpeechEngineServerOptions extends SpeechEngineCallbacks {
    /**
     * Port to listen on. Defaults to 3001.
     */
    port?: number;
    /**
     * Your ElevenLabs API key. Used to verify that incoming WebSocket
     * connections originate from the ElevenLabs API.
     *
     * When omitted, the server will reject all connections and throw
     * an error on start. Pass `{ apiKey: "..." }` or set the
     * `ELEVENLABS_API_KEY` environment variable.
     */
    apiKey?: string;
    /**
     * The ID of the speech engine this server handles connections for.
     * Populated automatically when created via `engine.listen()`.
     */
    engineId?: string;
}
/**
 * Standalone WebSocket server that produces `SpeechEngineSession` instances for
 * each incoming connection from the ElevenLabs Speech Engine API.
 *
 * Every incoming connection is verified against the ElevenLabs API using the
 * configured API key before being accepted.
 *
 * For integration with an existing HTTP server (e.g. Express, Next.js), use
 * `engine.attach()` instead.
 */
export declare class SpeechEngineServer {
    private wss;
    private httpServer;
    private options;
    constructor(options: SpeechEngineServerOptions);
    /**
     * Create a `SpeechEngineSession` from an existing WebSocket. Use this
     * when you manage your own WebSocket server and want to wrap individual
     * connections.
     */
    handleConnection(ws: WebSocket): SpeechEngineSession;
    /**
     * Start the standalone WebSocket server on the configured port.
     */
    start(): void;
    private wireHandler;
    /**
     * Stop the WebSocket server and close all active connections.
     */
    stop(): Promise<void>;
}
