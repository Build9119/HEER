/**
 * Defines asset positioning and transformation on canvas.
 */
export interface CanvasPlacement {
    xRelative?: number;
    yRelative?: number;
    scaleX?: number;
    scaleY?: number;
    pivotX?: number;
    pivotY?: number;
    skewX?: number;
    skewY?: number;
    cropTop?: number;
    cropRight?: number;
    cropBottom?: number;
    cropLeft?: number;
    flipX?: boolean;
    flipY?: boolean;
}
