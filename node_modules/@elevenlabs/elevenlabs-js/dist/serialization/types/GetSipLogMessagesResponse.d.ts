import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { SipLogMessage } from "./SipLogMessage";
export declare const GetSipLogMessagesResponse: core.serialization.ObjectSchema<serializers.GetSipLogMessagesResponse.Raw, ElevenLabs.GetSipLogMessagesResponse>;
export declare namespace GetSipLogMessagesResponse {
    interface Raw {
        sip_messages: SipLogMessage.Raw[];
        next_cursor?: string | null;
        has_more?: boolean | null;
    }
}
