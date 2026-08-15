import type { Server as HttpServer } from "node:http";
import WebSocket from "ws";
import type { BaseClientOptions, NormalizedClientOptions } from "../../BaseClient";
import type * as ElevenLabs from "../../api/types";
import { type SpeechEngineCallbacks } from "./types";
import { SpeechEngineSession } from "./SpeechEngineSession";
import { SpeechEngineAttachment } from "./SpeechEngineAttachment";
/**
 * Represents a speech engine instance. Returned by `elevenlabs.speechEngine.get()`.
 *
 * Use `engine.attach(httpServer, path, callbacks)` to integrate with an existing
 * HTTP server, or drop down to `engine.verifyRequest()` and `engine.createSession()`
 * for full control.
 *
 * @example
 * ```typescript
 * const engine = await elevenlabs.speechEngine.get("seng_123");
 *
 * engine.attach(httpServer, "/api/speech-engine/ws", {
 *     async onTranscript(transcript, signal, session) {
 *         session.sendResponse(await llm.generate(transcript, { signal }));
 *     },
 * });
 * ```
 */
export declare class SpeechEngineResource {
    readonly engineId: string;
    /**
     * Full configuration returned by the API. Populated when the resource is
     * returned from `create()`, `get()`, or `update()`.
     *
     * `undefined` when using the `attach()` shortcut directly, since no API
     * call is made in that case.
     */
    readonly config: Omit<ElevenLabs.SpeechEngineResponse, "speechEngineId"> | undefined;
    /** @internal */
    readonly _options: NormalizedClientOptions<BaseClientOptions>;
    /** @internal */
    constructor(engineId: string, options: NormalizedClientOptions<BaseClientOptions>, response?: ElevenLabs.SpeechEngineResponse);
    /**
     * Attach to an existing HTTP server and begin accepting Speech Engine
     * connections at the given path.
     *
     * Handles WebSocket upgrades, path routing, and request verification
     * automatically. Returns a `SpeechEngineAttachment` whose `.close()` stops
     * accepting connections without affecting the HTTP server.
     *
     * @example
     * ```typescript
     * engine.attach(httpServer, "/api/speech-engine/ws", {
     *     async onTranscript(transcript, signal, session) {
     *         const stream = await openai.responses.create({ model: "gpt-4o", input: transcript, stream: true }, { signal });
     *         session.sendResponse(stream);
     *     },
     * });
     * ```
     */
    attach(httpServer: HttpServer, path: string, handler: SpeechEngineCallbacks): SpeechEngineAttachment;
    /**
     * Verify that an incoming HTTP upgrade request is a legitimate connection
     * from the ElevenLabs Speech Engine API.
     *
     * Checks the `X-Elevenlabs-Speech-Engine-Authorization` header for a valid
     * JWT signed with the SHA-256 hash of the API key.
     *
     * Only needed when managing the WebSocket upgrade yourself. When using
     * `engine.attach()`, verification is handled automatically.
     */
    verifyRequest(req: {
        headers: Record<string, string | string[] | undefined>;
    }): Promise<boolean>;
    /** @internal Returns `null` when the request is valid, or a human-readable reason when rejected. */
    private getVerificationFailure;
    /**
     * Wrap an accepted WebSocket in a `SpeechEngineSession`.
     *
     * Only needed when managing the WebSocket upgrade yourself. When using
     * `engine.attach()`, sessions are created automatically.
     */
    createSession(ws: WebSocket, options?: {
        debug?: boolean;
    }): SpeechEngineSession;
    /** @internal */
    private wireHandler;
}
/** @internal — exported for testing only */
export declare function verifySpeechEngineJwt(value: string, apiKey: string): Record<string, unknown>;
