import type * as ElevenLabs from "../index";
export interface GetAgentTopicsResponseModel {
    topics: ElevenLabs.AgentTopicResponseModel[];
    windowStartUnixSecs: number;
    windowEndUnixSecs: number;
}
