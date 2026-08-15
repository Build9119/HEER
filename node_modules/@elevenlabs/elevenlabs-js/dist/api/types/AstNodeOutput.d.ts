import type * as ElevenLabs from "../index";
export type AstNodeOutput = ElevenLabs.AstNodeOutput.AddOperator | ElevenLabs.AstNodeOutput.AndOperator | ElevenLabs.AstNodeOutput.BooleanLiteral | ElevenLabs.AstNodeOutput.ConditionalOperator | ElevenLabs.AstNodeOutput.DivOperator | ElevenLabs.AstNodeOutput.DynamicVariable | ElevenLabs.AstNodeOutput.EqOperator | ElevenLabs.AstNodeOutput.GtOperator | ElevenLabs.AstNodeOutput.GteOperator | ElevenLabs.AstNodeOutput.Llm | ElevenLabs.AstNodeOutput.LtOperator | ElevenLabs.AstNodeOutput.LteOperator | ElevenLabs.AstNodeOutput.MulOperator | ElevenLabs.AstNodeOutput.NeqOperator | ElevenLabs.AstNodeOutput.NullLiteral | ElevenLabs.AstNodeOutput.NumberLiteral | ElevenLabs.AstNodeOutput.OrOperator | ElevenLabs.AstNodeOutput.StringLiteral | ElevenLabs.AstNodeOutput.SubOperator;
export declare namespace AstNodeOutput {
    interface AddOperator extends ElevenLabs.AstAdditionOperatorNodeOutput {
        type: "add_operator";
    }
    interface AndOperator extends ElevenLabs.AstAndOperatorNodeOutput {
        type: "and_operator";
    }
    interface BooleanLiteral extends ElevenLabs.AstBooleanNodeOutput {
        type: "boolean_literal";
    }
    interface ConditionalOperator extends ElevenLabs.AstConditionalOperatorNodeOutput {
        type: "conditional_operator";
    }
    interface DivOperator extends ElevenLabs.AstDivisionOperatorNodeOutput {
        type: "div_operator";
    }
    interface DynamicVariable extends ElevenLabs.AstDynamicVariableNodeOutput {
        type: "dynamic_variable";
    }
    interface EqOperator extends ElevenLabs.AstEqualsOperatorNodeOutput {
        type: "eq_operator";
    }
    interface GtOperator extends ElevenLabs.AstGreaterThanOperatorNodeOutput {
        type: "gt_operator";
    }
    interface GteOperator extends ElevenLabs.AstGreaterThanOrEqualsOperatorNodeOutput {
        type: "gte_operator";
    }
    interface Llm extends ElevenLabs.AstllmNodeOutput {
        type: "llm";
    }
    interface LtOperator extends ElevenLabs.AstLessThanOperatorNodeOutput {
        type: "lt_operator";
    }
    interface LteOperator extends ElevenLabs.AstLessThanOrEqualsOperatorNodeOutput {
        type: "lte_operator";
    }
    interface MulOperator extends ElevenLabs.AstMultiplicationOperatorNodeOutput {
        type: "mul_operator";
    }
    interface NeqOperator extends ElevenLabs.AstNotEqualsOperatorNodeOutput {
        type: "neq_operator";
    }
    interface NullLiteral extends ElevenLabs.AstNullNodeOutput {
        type: "null_literal";
    }
    interface NumberLiteral extends ElevenLabs.AstNumberNodeOutput {
        type: "number_literal";
    }
    interface OrOperator extends ElevenLabs.AstOrOperatorNodeOutput {
        type: "or_operator";
    }
    interface StringLiteral extends ElevenLabs.AstStringNodeOutput {
        type: "string_literal";
    }
    interface SubOperator extends ElevenLabs.AstSubtractionOperatorNodeOutput {
        type: "sub_operator";
    }
}
