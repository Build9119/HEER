import type { MusicClient as GeneratedMusic } from "../api/resources/music/client/Client";
import { ElevenLabsClient as FernClient } from "../Client";
import type * as core from "../core";
import { SpeechEngineClientWrapper } from "./speech-engine";
import { SpeechToText } from "./speechToText";
import { WebhooksClient } from "./webhooks";
export declare namespace ElevenLabsClient {
    interface Options extends FernClient.Options {
        /**
         * Your ElevenLabs API Key. Defaults to the environment
         * variable ELEVENLABS_API_KEY.
         */
        apiKey?: core.Supplier<string>;
    }
}
export declare class ElevenLabsClient extends FernClient {
    private _customWebhooks;
    private _customMusic;
    private _customSpeechToText;
    private _customSpeechEngine;
    constructor(options?: ElevenLabsClient.Options);
    get webhooks(): WebhooksClient;
    get music(): GeneratedMusic;
    get speechToText(): SpeechToText;
    get speechEngine(): SpeechEngineClientWrapper;
}
