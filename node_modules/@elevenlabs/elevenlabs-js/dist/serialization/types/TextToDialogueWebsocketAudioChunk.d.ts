import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { DialogueTextAlignment } from "./DialogueTextAlignment";
export declare const TextToDialogueWebsocketAudioChunk: core.serialization.ObjectSchema<serializers.TextToDialogueWebsocketAudioChunk.Raw, ElevenLabs.TextToDialogueWebsocketAudioChunk>;
export declare namespace TextToDialogueWebsocketAudioChunk {
    interface Raw {
        audio?: string | null;
        alignment?: DialogueTextAlignment.Raw | null;
        normalized_alignment?: DialogueTextAlignment.Raw | null;
    }
}
