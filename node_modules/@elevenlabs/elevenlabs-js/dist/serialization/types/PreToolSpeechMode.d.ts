import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const PreToolSpeechMode: core.serialization.Schema<serializers.PreToolSpeechMode.Raw, ElevenLabs.PreToolSpeechMode>;
export declare namespace PreToolSpeechMode {
    type Raw = "auto" | "force" | "off";
}
