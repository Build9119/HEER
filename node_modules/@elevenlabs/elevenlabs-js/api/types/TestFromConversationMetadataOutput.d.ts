import type * as ElevenLabs from "../index";
export interface TestFromConversationMetadataOutput {
    conversationId: string;
    agentId: string;
    branchId?: string;
    workflowNodeId?: string;
    originalAgentReply?: ElevenLabs.ConversationHistoryTranscriptCommonModelOutput[];
}
