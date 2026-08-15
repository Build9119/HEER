import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
import { ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput } from "./ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput";
import { ConversationHistoryTranscriptOtherToolsResultCommonModel } from "./ConversationHistoryTranscriptOtherToolsResultCommonModel";
import { ConversationHistoryTranscriptSystemToolResultCommonModelOutput } from "./ConversationHistoryTranscriptSystemToolResultCommonModelOutput";
export declare const WorkflowToolNestedToolsStepModelOutputResultsItem: core.serialization.Schema<serializers.WorkflowToolNestedToolsStepModelOutputResultsItem.Raw, ElevenLabs.WorkflowToolNestedToolsStepModelOutputResultsItem>;
export declare namespace WorkflowToolNestedToolsStepModelOutputResultsItem {
    type Raw = ConversationHistoryTranscriptOtherToolsResultCommonModel.Raw | ConversationHistoryTranscriptSystemToolResultCommonModelOutput.Raw | ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelOutput.Raw | serializers.ConversationHistoryTranscriptWorkflowToolsResultCommonModelOutput.Raw;
}
