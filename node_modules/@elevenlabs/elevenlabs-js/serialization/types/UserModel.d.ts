import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { UserTypeId } from "./UserTypeId";
export declare const UserModel: core.serialization.ObjectSchema<serializers.UserModel.Raw, ElevenLabs.UserModel>;
export declare namespace UserModel {
    interface Raw {
        name?: string | null;
        uid?: string | null;
        type_id?: UserTypeId.Raw | null;
        type?: string | null;
        email_addr?: string | null;
        full_name?: string | null;
        domain?: string | null;
    }
}
