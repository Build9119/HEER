import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ConversationHistoryRedactionConfig } from "./ConversationHistoryRedactionConfig";
export declare const PrivacyConfigOutput: core.serialization.ObjectSchema<serializers.PrivacyConfigOutput.Raw, ElevenLabs.PrivacyConfigOutput>;
export declare namespace PrivacyConfigOutput {
    interface Raw {
        record_voice?: boolean | null;
        retention_days?: number | null;
        delete_transcript_and_pii?: boolean | null;
        delete_audio?: boolean | null;
        apply_to_existing_conversations?: boolean | null;
        zero_retention_mode?: boolean | null;
        conversation_history_redaction?: ConversationHistoryRedactionConfig.Raw | null;
    }
}
