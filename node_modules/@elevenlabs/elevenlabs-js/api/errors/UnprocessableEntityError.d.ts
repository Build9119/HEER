import type * as core from "../../core";
import * as errors from "../../errors/index";
export declare class UnprocessableEntityError extends errors.ElevenLabsError {
    constructor(body?: unknown, rawResponse?: core.RawResponse);
}
