import type * as ElevenLabs from "../../../../../../index";
/**
 * @example
 *     {}
 */
export interface UpdatePhoneNumberRequest {
    agentId?: string;
    label?: string;
    inboundTrunkConfig?: ElevenLabs.InboundSipTrunkConfigRequestModel;
    outboundTrunkConfig?: ElevenLabs.OutboundSipTrunkConfigRequestModel;
    livekitStack?: ElevenLabs.LivekitStackType;
    storeSipMessages?: boolean;
    /** Environment to use for resolving environment variables on calls to this number. */
    environment?: string;
    /** Agent branch to use for calls to this number. */
    branchId?: string;
}
