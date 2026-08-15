import type * as ElevenLabs from "../index";
export interface GetKnowledgeBaseDependentAgentsResponseModel {
    agents: ElevenLabs.GetKnowledgeBaseDependentAgentsResponseModelAgentsItem[];
    branches?: ElevenLabs.DependentBranchInfo[];
    nextCursor?: string;
    hasMore: boolean;
}
