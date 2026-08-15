import type * as ElevenLabs from "../index";
export interface UnitTestRunResponseModel {
    testRunId: string;
    testInfo?: ElevenLabs.UnitTestRunResponseModelTestInfo;
    testInvocationId: string;
    agentId: string;
    branchId?: string;
    workflowNodeId?: string;
    status: ElevenLabs.TestRunStatus;
    agentResponses?: ElevenLabs.ConversationHistoryTranscriptCommonModelOutput[];
    testId: string;
    testName?: string;
    conditionResult?: ElevenLabs.TestConditionResultCommonModel;
    lastUpdatedAtUnix?: number;
    metadata?: ElevenLabs.TestRunMetadata;
    rootFolderId?: string;
    rootFolderName?: string;
    environment?: string;
}
