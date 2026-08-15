import type * as ElevenLabs from "../index";
export interface TestFromConversationMetadataInput {
    conversationId: string;
    agentId: string;
    branchId?: string;
    workflowNodeId?: string;
    originalAgentReply?: ElevenLabs.ConversationHistoryTranscriptCommonModelInput[];
}
