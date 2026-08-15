import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
import { ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput } from "./ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput";
import { ConversationHistoryTranscriptOtherToolsResultCommonModel } from "./ConversationHistoryTranscriptOtherToolsResultCommonModel";
import { ConversationHistoryTranscriptSystemToolResultCommonModelOutput } from "./ConversationHistoryTranscriptSystemToolResultCommonModelOutput";
export declare const ConversationHistoryTranscriptResponseModelToolResultsItem: core.serialization.Schema<serializers.ConversationHistoryTranscriptResponseModelToolResultsItem.Raw, ElevenLabs.ConversationHistoryTranscriptResponseModelToolResultsItem>;
export declare namespace ConversationHistoryTranscriptResponseModelToolResultsItem {
    type Raw = ConversationHistoryTranscriptOtherToolsResultCommonModel.Raw | ConversationHistoryTranscriptSystemToolResultCommonModelOutput.Raw | ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput.Raw | serializers.ConversationHistoryTranscriptWorkflowToolsResultCommonModelOutput.Raw;
}
