import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
export declare const ColumnFilterOperation: core.serialization.Schema<serializers.ColumnFilterOperation.Raw, ElevenLabs.ColumnFilterOperation>;
export declare namespace ColumnFilterOperation {
    type Raw = "in" | "not_in" | "le" | "ge" | "lt" | "gt" | "eq" | "neq";
}
