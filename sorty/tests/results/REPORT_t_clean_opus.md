# Sorty scenario test report

Run: 2026-11-21 15:37  |  model: `claude-opus-5-5` (effort low)  |  station: 3bin  |  images: Blender renders in `tests/images`  |  estimated API cost of this run: $0.03

## Result

**Sorty got 1 of 1 scenarios right.**

Sorty's thinking time averaged 7.8 s per item. It needed nothing from the person on 0 of 1 items, and 1.0 requests per item on average.

## Every scenario

| Scenario | What Sorty did | Final answer | Result |
|---|---|---|---|
| Pizza box, clean inside | asked to open show inside; ran contamination check | Blue bin, on your left. Clean pizza boxes recycle; greasy ones go to compost. Thank you! | PASS |

## How to read this

- A scenario passes only if the bin is right, any needed instruction (such as pouring out liquid) is given, and Sorty behaved sensibly: asked when no camera could know, looked again when a camera could, and did not bother the person when the answer was already visible.
- The one-look camera is graded on the bin and instruction only.
- The pictures are Blender renders, not photos from a real bin camera. Real-camera behaviour still has to be checked on the device.
