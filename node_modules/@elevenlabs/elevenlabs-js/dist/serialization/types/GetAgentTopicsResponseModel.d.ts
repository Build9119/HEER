import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { AgentTopicResponseModel } from "./AgentTopicResponseModel";
export declare const GetAgentTopicsResponseModel: core.serialization.ObjectSchema<serializers.GetAgentTopicsResponseModel.Raw, ElevenLabs.GetAgentTopicsResponseModel>;
export declare namespace GetAgentTopicsResponseModel {
    interface Raw {
        topics: AgentTopicResponseModel.Raw[];
        window_start_unix_secs: number;
        window_end_unix_secs: number;
    }
}
