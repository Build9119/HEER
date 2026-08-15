export declare const QualityPresetType: {
    readonly Standard: "standard";
    readonly High: "high";
    readonly Ultra: "ultra";
    readonly UltraLossless: "ultra_lossless";
};
export type QualityPresetType = (typeof QualityPresetType)[keyof typeof QualityPresetType];
