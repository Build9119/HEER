import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { SessionStartedPayloadConfig } from "./SessionStartedPayloadConfig";
export declare const SessionStartedPayload: core.serialization.ObjectSchema<serializers.SessionStartedPayload.Raw, ElevenLabs.SessionStartedPayload>;
export declare namespace SessionStartedPayload {
    interface Raw {
        message_type: "session_started";
        session_id: string;
        config: SessionStartedPayloadConfig.Raw;
    }
}
