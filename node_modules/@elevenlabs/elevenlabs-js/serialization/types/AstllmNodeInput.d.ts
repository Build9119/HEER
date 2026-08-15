import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AstllmNodeInputPrompt } from "./AstllmNodeInputPrompt";
import { AstllmNodeInputValueSchema } from "./AstllmNodeInputValueSchema";
export declare const AstllmNodeInput: core.serialization.Schema<serializers.AstllmNodeInput.Raw, ElevenLabs.AstllmNodeInput>;
export declare namespace AstllmNodeInput {
    type Raw = AstllmNodeInputValueSchema.Raw | AstllmNodeInputPrompt.Raw;
}
