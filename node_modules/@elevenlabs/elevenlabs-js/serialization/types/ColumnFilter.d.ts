import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ColumnFilterOperation } from "./ColumnFilterOperation";
import { ColumnFilterValuesItem } from "./ColumnFilterValuesItem";
export declare const ColumnFilter: core.serialization.ObjectSchema<serializers.ColumnFilter.Raw, ElevenLabs.ColumnFilter>;
export declare namespace ColumnFilter {
    interface Raw {
        column: string;
        operation: ColumnFilterOperation.Raw;
        values: (ColumnFilterValuesItem.Raw | null | undefined)[];
    }
}
