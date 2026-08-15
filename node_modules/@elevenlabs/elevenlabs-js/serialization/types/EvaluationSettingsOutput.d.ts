import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { PromptEvaluationCriteria } from "./PromptEvaluationCriteria";
export declare const EvaluationSettingsOutput: core.serialization.ObjectSchema<serializers.EvaluationSettingsOutput.Raw, ElevenLabs.EvaluationSettingsOutput>;
export declare namespace EvaluationSettingsOutput {
    interface Raw {
        criteria?: PromptEvaluationCriteria.Raw[] | null;
    }
}
