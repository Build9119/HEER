import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ConversationHistoryTranscriptFileInputResponseModel: core.serialization.ObjectSchema<serializers.ConversationHistoryTranscriptFileInputResponseModel.Raw, ElevenLabs.ConversationHistoryTranscriptFileInputResponseModel>;
export declare namespace ConversationHistoryTranscriptFileInputResponseModel {
    interface Raw {
        file_id: string;
        original_filename: string;
        mime_type: string;
        file_url: string;
    }
}
