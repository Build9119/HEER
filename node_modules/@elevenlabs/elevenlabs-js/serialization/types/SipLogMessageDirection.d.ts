import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SipLogMessageDirection: core.serialization.Schema<serializers.SipLogMessageDirection.Raw, ElevenLabs.SipLogMessageDirection>;
export declare namespace SipLogMessageDirection {
    type Raw = "in" | "out";
}
