import Cocoa
import ApplicationServices
let logURL = URL(fileURLWithPath: NSHomeDirectory())
              .appendingPathComponent("dev/dockglo/click_log.jsonl")
FileManager.default.createFile(atPath: logURL.path, contents: nil)

func dockRect() -> CGRect {
    let info = CGWindowListCopyWindowInfo([.excludeDesktopElements, .optionOnScreenOnly], 0) as? [[String: Any]] ?? []
    for w in info where (w["kCGWindowOwnerName"] as? String) == "Dock" {
        if let b = w["kCGWindowBounds"] as? [String: CGFloat] {
            return CGRect(x: b["X"]!, y: b["Y"]!, width: b["Width"]!, height: b["Height"]!)
        }
    }
    return .zero
}

var dockFrame = dockRect()
func frontID() -> String { NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? "unknown" }

let tap = CGEvent.tapCreate(tap: .cghidEventTap, place: .headInsertEventTap,
    options: .defaultTap,
    eventsOfInterest: CGEventMask(1 << CGEventType.leftMouseDown.rawValue),
    callback: { _,_,e,_ in
        dockFrame = dockRect()
        let p = e.location
        if dockFrame.contains(p) {
            let tile = Int((p.x - dockFrame.minX)/64)
            let rec = ["ts": Int(Date().timeIntervalSince1970),
                       "wantIdx": tile,
                       "landed": frontID()] as [String : Any]
            if let d = try? JSONSerialization.data(withJSONObject: rec),
               let h = try? FileHandle(forWritingTo: logURL) {
                h.seekToEndOfFile(); h.write(d); h.write("\n".data(using:.utf8)!); try? h.close()
            }
        }
        return Unmanaged.passRetained(e)
    }, userInfo: nil)!

CGEvent.tapEnable(tap: tap, enable: true)
let src = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)!
CFRunLoopAddSource(CFRunLoopGetCurrent(), src, .commonModes)
CFRunLoopRun()
