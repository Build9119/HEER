import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TextToDialogueWebsocketFinal: core.serialization.ObjectSchema<serializers.TextToDialogueWebsocketFinal.Raw, ElevenLabs.TextToDialogueWebsocketFinal>;
export declare namespace TextToDialogueWebsocketFinal {
    interface Raw {
        is_final: true;
    }
}
