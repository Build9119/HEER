export interface RetryTriggerAction {
    /** Custom feedback to inject into the agent when retrying after guardrail trigger. */
    feedback?: string;
}
