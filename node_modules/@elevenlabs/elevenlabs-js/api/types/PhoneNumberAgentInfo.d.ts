export interface PhoneNumberAgentInfo {
    /** The ID of the agent */
    agentId: string;
    /** The name of the agent */
    agentName: string;
    /** Environment to use for resolving environment variables on calls to this number. */
    environment?: string;
    /** Agent branch to use for calls to this number. */
    branchId?: string;
}
