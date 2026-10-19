import Foundation
import Vision
import AppKit

// Usage: swift ocr.swift <imagePath> [outputPath]
let args = CommandLine.arguments
guard args.count >= 2 else {
    print("usage: swift ocr.swift <image> [out]")
    exit(1)
}
let imagePath = args[1]
let outPath = args.count >= 3 ? args[2] : nil

guard let img = NSImage(contentsOfFile: imagePath) else {
    print("ERR cannot load image \(imagePath)")
    exit(1)
}
var rect = NSRect(origin: .zero, size: img.size)
guard let cg = img.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
    print("ERR cannot make cgImage")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en-US"]
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do {
    try handler.perform([request])
} catch {
    print("ERR perform: \(error)")
    exit(1)
}

var lines: [(y: CGFloat, text: String)] = []
if let results = request.results {
    for obs in results {
        guard let cand = obs.topCandidates(1).first else { continue }
        let bb = obs.boundingBox
        // Vision y is bottom-up; convert to top-down for reading order
        lines.append((y: 1.0 - bb.origin.y - bb.height, text: cand.string))
    }
}
// sort by y then x for reading order
lines.sort { a, b in
    if abs(a.y - b.y) > 0.01 { return a.y < b.y }
    return true
}

var full = lines.map { $0.text }.joined(separator: "\n")
if let outPath = outPath {
    try full.write(toFile: outPath, atomically: true, encoding: .utf8)
    print("WROTE \(outPath) (\(full.count) chars)")
} else {
    print(full)
}