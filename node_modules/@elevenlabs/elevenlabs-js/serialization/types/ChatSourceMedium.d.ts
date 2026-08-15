import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ChatSourceMedium: core.serialization.Schema<serializers.ChatSourceMedium.Raw, ElevenLabs.ChatSourceMedium>;
export declare namespace ChatSourceMedium {
    type Raw = "audio" | "text" | "image" | "file";
}
