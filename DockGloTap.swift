import Cocoa
import ApplicationServices

let logURL = URL(fileURLWithPath: NSHomeDirectory())
              .appendingPathComponent("dev/dockglo/click_log.jsonl")

// create the log file if it doesn't exist
if !FileManager.default.fileExists(atPath: logURL.path) {
    FileManager.default.createFile(atPath: logURL.path, contents: nil)
}

var dockFrame = NSRect.zero
func refreshDockFrame() {
    for window in NSApp.windows where window.identifier?.rawValue == "Dock" {
        dockFrame = window.frame; break
    }
}
func frontBundleID() -> String {
    NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? "unknown"
}

let tap = CGEvent.tapCreate(
    tap: .cghidEventTap,
    place: .headInsertEventTap,
    options: .defaultTap,
    eventsOfInterest: CGEventMask(1 << CGEventType.leftMouseDown.rawValue),
    callback: { _, _, event, _ in
        let p = event.location
        if dockFrame.contains(p) {
            refreshDockFrame()
            let tile = Int((p.x - dockFrame.minX) / 64)                // crude width
            let rec: [String: Any] = [
                "ts": Int(Date().timeIntervalSince1970),
                "wantIdx": tile,
                "landed": frontBundleID()
            ]
            if let data = try? JSONSerialization.data(withJSONObject: rec),
               let fh = try? FileHandle(forWritingTo: logURL) {
                fh.seekToEndOfFile()
                fh.write(data)
                fh.write("\n".data(using: .utf8)!)
                try? fh.close()
            }
        }
        return Unmanaged.passRetained(event)
    }, userInfo: nil)!

CGEvent.tapEnable(tap: tap, enable: true)
let src = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)!
CFRunLoopAddSource(CFRunLoopGetCurrent(), src, .commonModes)
refreshDockFrame(); CFRunLoopRun()
