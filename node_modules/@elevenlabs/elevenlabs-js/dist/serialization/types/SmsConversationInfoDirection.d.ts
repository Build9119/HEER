import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SmsConversationInfoDirection: core.serialization.Schema<serializers.SmsConversationInfoDirection.Raw, ElevenLabs.SmsConversationInfoDirection>;
export declare namespace SmsConversationInfoDirection {
    type Raw = "inbound" | "outbound";
}
