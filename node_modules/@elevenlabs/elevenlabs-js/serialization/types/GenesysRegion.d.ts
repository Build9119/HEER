import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const GenesysRegion: core.serialization.Schema<serializers.GenesysRegion.Raw, ElevenLabs.GenesysRegion>;
export declare namespace GenesysRegion {
    type Raw = "us_east_1" | "eu_west_1" | "ap_southeast_2" | "ap_northeast_1" | "eu_central_1" | "us_west_2" | "ca_central_1" | "ap_northeast_2" | "eu_west_2" | "ap_south_1" | "us_east_2" | "sa_east_1" | "me_central_1" | "ap_northeast_3" | "eu_central_2" | "mx_central_1" | "ap_southeast_1";
}
