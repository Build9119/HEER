import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const UnitTestWorkflowNodeTransitionEvaluationNodeId: core.serialization.ObjectSchema<serializers.UnitTestWorkflowNodeTransitionEvaluationNodeId.Raw, ElevenLabs.UnitTestWorkflowNodeTransitionEvaluationNodeId>;
export declare namespace UnitTestWorkflowNodeTransitionEvaluationNodeId {
    interface Raw {
        type?: "node_id" | null;
        agent_id: string;
        target_node_id: string;
    }
}
