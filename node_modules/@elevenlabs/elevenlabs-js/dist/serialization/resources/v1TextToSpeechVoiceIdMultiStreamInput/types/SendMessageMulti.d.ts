import type * as ElevenLabs from "../../../../api/index";
import * as core from "../../../../core";
import type * as serializers from "../../../index";
import { CloseContext } from "../../../types/CloseContext";
import { CloseSocket } from "../../../types/CloseSocket";
import { FlushContext } from "../../../types/FlushContext";
import { InitialiseContext } from "../../../types/InitialiseContext";
import { InitializeConnectionMulti } from "../../../types/InitializeConnectionMulti";
import { KeepContextAlive } from "../../../types/KeepContextAlive";
import { SendTextMulti } from "../../../types/SendTextMulti";
export declare const SendMessageMulti: core.serialization.Schema<serializers.SendMessageMulti.Raw, ElevenLabs.SendMessageMulti>;
export declare namespace SendMessageMulti {
    type Raw = InitializeConnectionMulti.Raw | InitialiseContext.Raw | SendTextMulti.Raw | FlushContext.Raw | CloseContext.Raw | CloseSocket.Raw | KeepContextAlive.Raw;
}
