export declare const ChatSourceMedium: {
    readonly Audio: "audio";
    readonly Text: "text";
    readonly Image: "image";
    readonly File: "file";
};
export type ChatSourceMedium = (typeof ChatSourceMedium)[keyof typeof ChatSourceMedium];
