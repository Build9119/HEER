import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
import { ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput } from "./ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput";
import { ConversationHistoryTranscriptOtherToolsResultCommonModel } from "./ConversationHistoryTranscriptOtherToolsResultCommonModel";
import { ConversationHistoryTranscriptSystemToolResultCommonModelOutput } from "./ConversationHistoryTranscriptSystemToolResultCommonModelOutput";
export declare const ConversationHistoryTranscriptCommonModelOutputToolResultsItem: core.serialization.Schema<serializers.ConversationHistoryTranscriptCommonModelOutputToolResultsItem.Raw, ElevenLabs.ConversationHistoryTranscriptCommonModelOutputToolResultsItem>;
export declare namespace ConversationHistoryTranscriptCommonModelOutputToolResultsItem {
    type Raw = ConversationHistoryTranscriptOtherToolsResultCommonModel.Raw | ConversationHistoryTranscriptSystemToolResultCommonModelOutput.Raw | ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput.Raw | serializers.ConversationHistoryTranscriptWorkflowToolsResultCommonModelOutput.Raw;
}
