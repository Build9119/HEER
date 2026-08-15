import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const SessionStartedPayloadConfigCommitStrategy: core.serialization.Schema<serializers.SessionStartedPayloadConfigCommitStrategy.Raw, ElevenLabs.SessionStartedPayloadConfigCommitStrategy>;
export declare namespace SessionStartedPayloadConfigCommitStrategy {
    type Raw = "manual" | "vad";
}
