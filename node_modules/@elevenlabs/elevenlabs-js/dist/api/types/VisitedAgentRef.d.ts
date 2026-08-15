/**
 * An agent (and optional branch) that participated in the call, in first-seen transcript order.
 */
export interface VisitedAgentRef {
    agentId: string;
    branchId?: string;
}
