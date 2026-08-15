import type * as ElevenLabs from "../index";
export interface ColumnFilter {
    column: string;
    operation: ElevenLabs.ColumnFilterOperation;
    values: (ElevenLabs.ColumnFilterValuesItem | undefined)[];
}
