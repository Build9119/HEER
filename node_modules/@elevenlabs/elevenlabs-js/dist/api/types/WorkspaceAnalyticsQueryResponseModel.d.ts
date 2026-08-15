import type * as ElevenLabs from "../index";
export interface WorkspaceAnalyticsQueryResponseModel {
    columns: string[];
    columnTypes: ElevenLabs.WorkspaceAnalyticsQueryResponseModelColumnTypesItem[];
    rows: (ElevenLabs.WorkspaceAnalyticsQueryResponseModelRowsItemItem | undefined)[][];
    columnUnits: (ElevenLabs.ColumnUnit | undefined)[];
}
