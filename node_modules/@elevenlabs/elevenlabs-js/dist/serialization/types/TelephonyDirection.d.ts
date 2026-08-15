import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const TelephonyDirection: core.serialization.Schema<serializers.TelephonyDirection.Raw, ElevenLabs.TelephonyDirection>;
export declare namespace TelephonyDirection {
    type Raw = "inbound" | "outbound";
}
