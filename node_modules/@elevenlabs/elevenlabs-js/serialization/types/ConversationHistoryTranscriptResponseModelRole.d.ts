import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ConversationHistoryTranscriptResponseModelRole: core.serialization.Schema<serializers.ConversationHistoryTranscriptResponseModelRole.Raw, ElevenLabs.ConversationHistoryTranscriptResponseModelRole>;
export declare namespace ConversationHistoryTranscriptResponseModelRole {
    type Raw = "user" | "agent";
}
