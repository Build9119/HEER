import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import * as serializers from "../index";
import { ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelInput } from "./ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelInput";
import { ConversationHistoryTranscriptOtherToolsResultCommonModel } from "./ConversationHistoryTranscriptOtherToolsResultCommonModel";
import { ConversationHistoryTranscriptSystemToolResultCommonModelInput } from "./ConversationHistoryTranscriptSystemToolResultCommonModelInput";
export declare const WorkflowToolNestedToolsStepModelInputResultsItem: core.serialization.Schema<serializers.WorkflowToolNestedToolsStepModelInputResultsItem.Raw, ElevenLabs.WorkflowToolNestedToolsStepModelInputResultsItem>;
export declare namespace WorkflowToolNestedToolsStepModelInputResultsItem {
    type Raw = ConversationHistoryTranscriptOtherToolsResultCommonModel.Raw | ConversationHistoryTranscriptSystemToolResultCommonModelInput.Raw | ConversationHistoryTranscriptApiIntegrationWebhookToolsResultCommonModelInput.Raw | serializers.ConversationHistoryTranscriptWorkflowToolsResultCommonModelInput.Raw;
}
