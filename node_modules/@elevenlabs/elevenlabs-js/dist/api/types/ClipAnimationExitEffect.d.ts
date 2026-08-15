export declare const ClipAnimationExitEffect: {
    readonly None: "none";
    readonly Fade: "fade";
    readonly Float: "float";
    readonly GentleFloat: "gentle_float";
    readonly ZoomIn: "zoom_in";
    readonly Drop: "drop";
    readonly SlideLeft: "slide_left";
    readonly SlideRight: "slide_right";
    readonly SlideUp: "slide_up";
    readonly SlideDown: "slide_down";
    readonly Pop: "pop";
    readonly Bounce: "bounce";
    readonly Spin: "spin";
    readonly SlideBounce: "slide_bounce";
};
export type ClipAnimationExitEffect = (typeof ClipAnimationExitEffect)[keyof typeof ClipAnimationExitEffect];
