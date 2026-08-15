import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const CloseSocket: core.serialization.ObjectSchema<serializers.CloseSocket.Raw, ElevenLabs.CloseSocket>;
export declare namespace CloseSocket {
    interface Raw {
        close_socket?: boolean | null;
    }
}
