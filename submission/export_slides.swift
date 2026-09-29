import CoreGraphics
import CoreText
import Foundation

let width: CGFloat = 1600
let height: CGFloat = 900
let output = URL(fileURLWithPath: CommandLine.arguments.dropFirst().first ?? "submission/ai-innovation-slides.pdf")
let pageBounds = CGRect(x: 0, y: 0, width: width, height: height)
guard let context = CGContext(output as CFURL, mediaBox: nil, nil) else {
    fatalError("Could not create PDF at \(output.path)")
}

let ink = CGColor(red: 0.984, green: 0.973, blue: 1, alpha: 1)
let muted = CGColor(red: 0.796, green: 0.749, blue: 0.855, alpha: 1)
let mint = CGColor(red: 0.569, green: 0.961, blue: 0.835, alpha: 1)
let lavender = CGColor(red: 0.788, green: 0.682, blue: 1, alpha: 1)
let amber = CGColor(red: 0.965, green: 0.788, blue: 0.471, alpha: 1)
let line = CGColor(red: 0.91, green: 0.847, blue: 1, alpha: 0.25)
let panel = CGColor(red: 0.16, green: 0.10, blue: 0.24, alpha: 1)

func rect(_ x: CGFloat, _ top: CGFloat, _ w: CGFloat, _ h: CGFloat) -> CGRect {
    CGRect(x: x, y: height - top - h, width: w, height: h)
}

func fill(_ x: CGFloat, _ top: CGFloat, _ w: CGFloat, _ h: CGFloat, _ color: CGColor) {
    context.setFillColor(color)
    context.fill(rect(x, top, w, h))
}

func stroke(_ x: CGFloat, _ top: CGFloat, _ w: CGFloat, _ h: CGFloat, _ color: CGColor, _ lineWidth: CGFloat = 1) {
    context.setStrokeColor(color)
    context.setLineWidth(lineWidth)
    context.stroke(rect(x, top, w, h))
}

func text(_ value: String, _ x: CGFloat, _ top: CGFloat, _ size: CGFloat, _ color: CGColor, _ maxWidth: CGFloat, fontName: String = "Helvetica") {
    let font = CTFontCreateWithName(fontName as CFString, size, nil)
    let attributes: [NSAttributedString.Key: Any] = [
        NSAttributedString.Key(kCTFontAttributeName as String): font,
        NSAttributedString.Key(kCTForegroundColorAttributeName as String): color,
    ]
    let attributed = NSAttributedString(string: value, attributes: attributes)
    let framesetter = CTFramesetterCreateWithAttributedString(attributed as CFAttributedString)
    let path = CGPath(rect: CGRect(x: x, y: 35, width: maxWidth, height: height - top - 35), transform: nil)
    let frame = CTFramesetterCreateFrame(framesetter, CFRange(location: 0, length: attributed.length), path, nil)
    CTFrameDraw(frame, context)
}

func background(_ number: Int) {
    context.beginPDFPage(nil)
    fill(0, 0, width, height, CGColor(red: 0.09, green: 0.06, blue: 0.18, alpha: 1))
    context.setStrokeColor(CGColor(red: 0.94, green: 0.88, blue: 1, alpha: 0.045))
    context.setLineWidth(1)
    stride(from: CGFloat(0), through: width, by: 48).forEach { x in
        context.move(to: CGPoint(x: x, y: 0))
        context.addLine(to: CGPoint(x: x, y: height))
    }
    stride(from: CGFloat(0), through: height, by: 48).forEach { y in
        context.move(to: CGPoint(x: 0, y: y))
        context.addLine(to: CGPoint(x: width, y: y))
    }
    context.strokePath()
    stroke(96, 790, 1408, 1, line)
    text("AI INNOVATION  /  BILINGUAL VOICE SUPPORT", 96, 817, 15, muted, 900)
    text(String(format: "%02d / 05", number), 1370, 817, 15, muted, 140)
}

func tile(_ x: CGFloat, _ top: CGFloat, _ title: String, _ detail: String, accent: CGColor = mint) {
    fill(x, top, 660, 142, panel)
    stroke(x, top, 660, 142, line)
    fill(x, top, 4, 142, accent)
    text(title, x + 24, top + 22, 23, accent, 610, fontName: "Helvetica-Bold")
    text(detail, x + 24, top + 59, 18, muted, 610)
}

func flow(_ x: CGFloat, _ top: CGFloat, _ label: String, _ title: String, _ detail: String, accent: CGColor) {
    fill(x, top, 335, 230, panel)
    stroke(x, top, 335, 230, line)
    fill(x, top, 335, 4, accent)
    text(label, x + 20, top + 23, 14, muted, 295)
    text(title, x + 20, top + 59, 23, accent, 295, fontName: "Helvetica-Bold")
    text(detail, x + 20, top + 105, 17, muted, 295)
}

background(1)
text("ASSEMBLYAI VOICE AGENT HACKATHON  /  SEPTEMBER 2026", 100, 105, 18, mint, 1000)
text("Support, in your\nlanguage.", 96, 260, 92, ink, 930, fontName: "Helvetica-Bold")
text("AI Innovation — a bilingual voice-support assistant for Vietnamese- and English-speaking customers.", 102, 520, 27, muted, 880)
text("VIETNAMESE  ↔  ENGLISH     ·     VOICE-FIRST     ·     HUMAN-AWARE", 102, 645, 17, mint, 980)
context.setStrokeColor(lavender)
context.setLineWidth(2)
for radius in stride(from: CGFloat(90), through: 240, by: 50) {
    context.strokeEllipse(in: rect(1170 + (240 - radius), 260 + (240 - radius), radius * 2, radius * 2))
}
context.endPDFPage()

background(2)
text("01  /  THE PROBLEM", 100, 95, 17, mint, 800)
text("Getting help shouldn't depend\non your language.", 96, 140, 57, ink, 1100, fontName: "Helvetica-Bold")
tile(100, 340, "Language friction", "Customers may struggle to explain an issue or follow support steps in a second language.")
tile(820, 340, "Slow first response", "Simple questions can turn into long waits before a customer knows what to try next.", accent: lavender)
tile(100, 510, "Trust matters", "Support should be clear about what it can do—and what requires a person.", accent: amber)
tile(820, 510, "Designed for a handoff", "Safe initial guidance and a concise issue summary for human support.", accent: lavender)
context.endPDFPage()

background(3)
text("02  /  THE EXPERIENCE", 100, 95, 17, mint, 800)
text("One conversation. Two languages.\nHuman control.", 96, 140, 57, ink, 1200, fontName: "Helvetica-Bold")
flow(100, 350, "01  ·  SPEAK", "Natural voice", "Describe an issue in Vietnamese or English.", accent: lavender)
flow(455, 350, "02  ·  SEE", "Live transcript", "Follow partial and final speech recognition.", accent: mint)
flow(810, 350, "03  ·  HEAR", "Spoken guidance", "Short response sentences are voiced as they arrive.", accent: amber)
flow(1165, 350, "04  ·  CONTROL", "Interrupt or hand off", "Barge in anytime; get a clear human-support next step.", accent: CGColor(red: 1, green: 0.55, blue: 0.61, alpha: 1))
text("Demo: ask in Vietnamese, switch to English, interrupt a reply, then request account-specific help.", 102, 630, 20, muted, 1250)
context.endPDFPage()

background(4)
text("03  /  BUILT ON ASSEMBLYAI", 100, 95, 17, mint, 800)
text("Real-time speech in.\nOrchestrated support out.", 96, 140, 57, ink, 1200, fontName: "Helvetica-Bold")
flow(100, 350, "INPUT", "Browser mic", "Mono PCM16 audio at 24 kHz over WebSocket.", accent: lavender)
flow(455, 350, "SPEECH", "AssemblyAI", "Streaming Speech-to-Text for Vietnamese / English.", accent: mint)
flow(810, 350, "ORCHESTRATION", "FastAPI + Gemini", "Conversation context, language preference, streamed reply.", accent: amber)
flow(1165, 350, "VOICE", "Edge TTS", "Sentence-sized audio returned to the browser.", accent: CGColor(red: 1, green: 0.55, blue: 0.61, alpha: 1))
text("The application owns turn handling, language preference, response generation, and speech output.", 102, 630, 20, muted, 1250)
context.endPDFPage()

background(5)
text("04  /  RESPONSIBLE SUPPORT", 100, 95, 17, mint, 800)
text("Helpful, without pretending\nto be the helpdesk.", 96, 140, 57, ink, 1250, fontName: "Helvetica-Bold")
tile(100, 370, "What AI Innovation does", "Offers concise, general troubleshooting; speaks the customer's language; prepares a short summary for official support.", accent: mint)
tile(820, 370, "What AI Innovation does not do", "Cannot access accounts, check orders, create tickets, issue refunds, or state company policies.", accent: amber)
text("Next: connect an approved company knowledge base and a secure human-support workflow.", 102, 600, 21, muted, 1250)
text("No password or payment credentials requested.", 102, 660, 18, mint, 1250)
context.endPDFPage()

context.closePDF()
print("Wrote \(output.path)")
