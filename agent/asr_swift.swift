// asr_swift.swift — offline macOS speech-to-text for HEER.
//
// Uses the built-in Speech framework (on-device recognizer) to transcribe a
// pre-recorded audio file (WAV/CAF/m4a). Compiled once by agent/voice.py and
// cached. Reads the audio path from argv[1], prints JSON to stdout:
//   {"text": "..."}        on success
//   {"error": "..."}       on failure (authorization, recognizer, etc.)
//
// Build:  swiftc -O asr_swift.swift -o /tmp/heer_asr/asr_swift
// Run:    asr_swift /tmp/clip.wav

import Foundation
import Speech

// ---------------------------------------------------------------------------
// Output helpers
//
// When launched via LaunchServices (`open -W -n HeerASR.app --args <wav> <out>`)
// stdout is detached, so the JSON result is also written to the file passed as
// argv[2] (when present). That keeps a single result format for both direct
// invocation and bundle-context launch (which properly resolves the TCC
// responsible process for the Speech framework permission).
// ---------------------------------------------------------------------------

var outputFilePath: String?

func emit(_ obj: [String: String]) {
    if let data = try? JSONSerialization.data(withJSONObject: obj),
       let out = String(data: data, encoding: .utf8) {
        FileHandle.standardOutput.write(out.data(using: .utf8)!)
        if let outputFilePath {
            try? data.write(to: URL(fileURLWithPath: outputFilePath))
        }
    }
}


func fail(_ message: String) -> Never {
    emit(["error": message])
    exit(1)
}

func dbg(_ message: String) {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
}

// ---------------------------------------------------------------------------
// Authorization (one-time system prompt; file-based recognition > no mic)
// ---------------------------------------------------------------------------

dbg("[asr] requesting authorization…")
let authSema = DispatchSemaphore(value: 0)
var authorized = false

SFSpeechRecognizer.requestAuthorization { status in
    authorized = (status == .authorized)
    authSema.signal()
}
authSema.wait()
dbg("[asr] authorization done: \(authorized)")

guard authorized else {
    fail("speech recognition not authorized — enable it in System Settings > Privacy & Security > Speech Recognition")
}

guard let recognizer = SFSpeechRecognizer(), recognizer.isAvailable else {
    fail("no speech recognizer available for the current locale")
}
dbg("[asr] recognizer ready; on-device supported: \(recognizer.supportsOnDeviceRecognition)")

// ---------------------------------------------------------------------------
// Recognize
// ---------------------------------------------------------------------------

let args = CommandLine.arguments
guard args.count >= 2 else {
    fail("usage: asr_swift <audio-file> [output-json]")
}
let path = args[1]
if args.count >= 3 {
    outputFilePath = args[2]
}
guard FileManager.default.fileExists(atPath: path) else {
    fail("audio file not found")
}

let url = URL(fileURLWithPath: path)
let request = SFSpeechURLRecognitionRequest(url: url)
request.shouldReportPartialResults = false
// Note: not forcing requiresOnDeviceRecognition — it can stall recognition
// on machines where the on-device model isn't fully downloaded.

let done = DispatchSemaphore(value: 0)
var transcript = ""
var errorMessage: String?
var hadFinal = false

recognizer.recognitionTask(with: request) { result, error in
    if let error = error {
        errorMessage = error.localizedDescription
        done.signal()
        return
    }
    if let result = result {
        transcript = result.bestTranscription.formattedString
        if result.isFinal {
            hadFinal = true
            done.signal()
        }
    }
}

// give the recognizer generous time (long clips)
let waitResult = done.wait(timeout: .now() + 180)
if waitResult == .timedOut {
    fail("recognition timed out")
}

if let errorMessage = errorMessage {
    fail(errorMessage)
}
if !hadFinal {
    fail("recognition produced no result")
}

emit(["text": transcript])
