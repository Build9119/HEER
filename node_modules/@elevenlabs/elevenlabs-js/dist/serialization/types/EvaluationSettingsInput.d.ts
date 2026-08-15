import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { PromptEvaluationCriteria } from "./PromptEvaluationCriteria";
export declare const EvaluationSettingsInput: core.serialization.ObjectSchema<serializers.EvaluationSettingsInput.Raw, ElevenLabs.EvaluationSettingsInput>;
export declare namespace EvaluationSettingsInput {
    interface Raw {
        criteria?: PromptEvaluationCriteria.Raw[] | null;
    }
}
