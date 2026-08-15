import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CreateLocationParams: core.serialization.ObjectSchema<serializers.CreateLocationParams.Raw, ElevenLabs.CreateLocationParams>;
export declare namespace CreateLocationParams {
    interface Raw {
        smb_tool_type?: "create_location" | null;
    }
}
