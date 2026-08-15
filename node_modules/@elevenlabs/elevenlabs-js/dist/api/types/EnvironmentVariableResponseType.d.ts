export declare const EnvironmentVariableResponseType: {
    readonly String: "string";
    readonly Secret: "secret";
    readonly AuthConnection: "auth_connection";
};
export type EnvironmentVariableResponseType = (typeof EnvironmentVariableResponseType)[keyof typeof EnvironmentVariableResponseType];
