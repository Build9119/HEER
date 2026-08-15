export declare const EnvironmentVariablesListRequestType: {
    readonly String: "string";
    readonly Secret: "secret";
    readonly AuthConnection: "auth_connection";
};
export type EnvironmentVariablesListRequestType = (typeof EnvironmentVariablesListRequestType)[keyof typeof EnvironmentVariablesListRequestType];
