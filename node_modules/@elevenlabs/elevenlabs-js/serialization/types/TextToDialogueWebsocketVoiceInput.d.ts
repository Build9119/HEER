import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TextToDialogueWebsocketVoiceInput: core.serialization.ObjectSchema<serializers.TextToDialogueWebsocketVoiceInput.Raw, ElevenLabs.TextToDialogueWebsocketVoiceInput>;
export declare namespace TextToDialogueWebsocketVoiceInput {
    interface Raw {
        text: string;
        voice_id: string;
        new_turn?: boolean | null;
    }
}
