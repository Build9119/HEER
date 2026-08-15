import type * as ElevenLabs from "../index";
export interface AstMultiplicationOperatorNodeOutput {
    /** Left operand of the binary operator. */
    left: ElevenLabs.AstNodeOutput;
    /** Right operand of the binary operator. */
    right: ElevenLabs.AstNodeOutput;
}
