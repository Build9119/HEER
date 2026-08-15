import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TextToDialogueWebsocketError: core.serialization.ObjectSchema<serializers.TextToDialogueWebsocketError.Raw, ElevenLabs.TextToDialogueWebsocketError>;
export declare namespace TextToDialogueWebsocketError {
    interface Raw {
        message: string;
        error: string;
        code: number;
        param?: string | null;
    }
}
