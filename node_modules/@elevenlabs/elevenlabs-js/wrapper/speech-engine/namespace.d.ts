/**
 * Speech Engine namespace — provides event constants and classes for handling
 * incoming WebSocket connections from the ElevenLabs Speech Engine API.
 *
 * @example
 * ```typescript
 * import { SpeechEngine } from "@elevenlabs/elevenlabs-js";
 *
 * const session = new SpeechEngine.Session(ws);
 * session.on(SpeechEngine.USER_TRANSCRIPT, async (transcript, signal) => { ... });
 * ```
 */
/** Fired when the session is initialized with a conversation ID. */
export declare const INIT: "init";
/** Fired when the Speech Engine API sends a user transcript. */
export declare const USER_TRANSCRIPT: "user_transcript";
/** Fired when the user disconnects the call. */
export declare const CLOSE: "close";
/** Fired when an error occurs (protocol or WebSocket level). */
export declare const ERROR: "error";
/** Fired when the underlying WebSocket connection drops. */
export declare const DISCONNECTED: "disconnected";
export { SpeechEngineSession as Session } from "./SpeechEngineSession";
export { SpeechEngineServer as Server, type SpeechEngineServerOptions as ServerOptions } from "./SpeechEngineServer";
export { SpeechEngineAttachment as Attachment } from "./SpeechEngineAttachment";
export { SpeechEngineResource as Resource } from "./SpeechEngineResource";
export { SpeechEngineClientWrapper as Client } from "./SpeechEngineClientWrapper";
