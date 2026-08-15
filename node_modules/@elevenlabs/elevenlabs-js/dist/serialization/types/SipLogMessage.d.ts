import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { SipLogMessageDirection } from "./SipLogMessageDirection";
export declare const SipLogMessage: core.serialization.ObjectSchema<serializers.SipLogMessage.Raw, ElevenLabs.SipLogMessage>;
export declare namespace SipLogMessage {
    interface Raw {
        call_id: string;
        phone_numbers: string[];
        local_address: string;
        remote_address: string;
        transport: string;
        raw_message: string;
        error_message: string;
        direction: SipLogMessageDirection.Raw;
        created_at_unix_micro: number;
    }
}
