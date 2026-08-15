import type * as ElevenLabs from "../../api/index";
import * as core from "../../core";
import type * as serializers from "../index";
import { ColumnUnit } from "./ColumnUnit";
import { WorkspaceAnalyticsQueryResponseModelColumnTypesItem } from "./WorkspaceAnalyticsQueryResponseModelColumnTypesItem";
import { WorkspaceAnalyticsQueryResponseModelRowsItemItem } from "./WorkspaceAnalyticsQueryResponseModelRowsItemItem";
export declare const WorkspaceAnalyticsQueryResponseModel: core.serialization.ObjectSchema<serializers.WorkspaceAnalyticsQueryResponseModel.Raw, ElevenLabs.WorkspaceAnalyticsQueryResponseModel>;
export declare namespace WorkspaceAnalyticsQueryResponseModel {
    interface Raw {
        columns: string[];
        column_types: WorkspaceAnalyticsQueryResponseModelColumnTypesItem.Raw[];
        rows: (WorkspaceAnalyticsQueryResponseModelRowsItemItem.Raw | null | undefined)[][];
        column_units: (ColumnUnit.Raw | null | undefined)[];
    }
}
