import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ApiIntegrationOAuth2AuthCodeResponseScopeSeparator: core.serialization.Schema<serializers.ApiIntegrationOAuth2AuthCodeResponseScopeSeparator.Raw, ElevenLabs.ApiIntegrationOAuth2AuthCodeResponseScopeSeparator>;
export declare namespace ApiIntegrationOAuth2AuthCodeResponseScopeSeparator {
    type Raw = " " | ",";
}
