import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ListAuthConnectionsResponseAuthConnectionsItem } from "./ListAuthConnectionsResponseAuthConnectionsItem";
export declare const ListAuthConnectionsResponse: core.serialization.ObjectSchema<serializers.ListAuthConnectionsResponse.Raw, ElevenLabs.ListAuthConnectionsResponse>;
export declare namespace ListAuthConnectionsResponse {
    interface Raw {
        auth_connections: ListAuthConnectionsResponseAuthConnectionsItem.Raw[];
    }
}
