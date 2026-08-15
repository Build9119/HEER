import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const VisitedAgentRef: core.serialization.ObjectSchema<serializers.VisitedAgentRef.Raw, ElevenLabs.VisitedAgentRef>;
export declare namespace VisitedAgentRef {
    interface Raw {
        agent_id: string;
        branch_id?: string | null;
    }
}
