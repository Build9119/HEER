import { SpeechToTextClient as GeneratedSpeechToText } from "../api/resources/speechToText/client/Client";
import type { SpeechToTextClient } from "../api/resources/speechToText/client/Client";
import type * as ElevenLabs from "../api";
import type * as core from "../core";
import { ScribeRealtime } from "./realtime";
export declare class SpeechToText extends GeneratedSpeechToText {
    private _realtime;
    get realtime(): ScribeRealtime;
    convert(request: ElevenLabs.BodySpeechToTextV1SpeechToTextPost & {
        webhook: true;
    }, requestOptions?: SpeechToTextClient.RequestOptions): core.HttpResponsePromise<ElevenLabs.SpeechToTextWebhookResponseModel>;
    convert(request: ElevenLabs.BodySpeechToTextV1SpeechToTextPost & {
        useMultiChannel: true;
    }, requestOptions?: SpeechToTextClient.RequestOptions): core.HttpResponsePromise<ElevenLabs.MultichannelSpeechToTextResponseModel>;
    convert(request: ElevenLabs.BodySpeechToTextV1SpeechToTextPost, requestOptions?: SpeechToTextClient.RequestOptions): core.HttpResponsePromise<ElevenLabs.SpeechToTextChunkResponseModel>;
}
