# Sorty scenario test report

Run: 2026-11-21 15:02  |  model: `claude-sonnet-5-5` (effort low)  |  station: 3bin  |  images: Blender renders in `tests/images`  |  estimated API cost of this run: $0.05

## Result

**Sorty got 2 of 2 scenarios right.**

Sorty's thinking time averaged 8.4 s per item. It needed nothing from the person on 0 of 2 items, and 1.0 requests per item on average.

## Every scenario

| Scenario | What Sorty did | Final answer | Result |
|---|---|---|---|
| Pizza box, greasy inside | asked to open show inside; ran contamination check | Green bin, in the middle. Greasy or cheesy pizza boxes go to compost, whole box. Thank you! | PASS |
| Soda can, half full | asked "Is the can completely empty?" | First, pour out the cola first. Then: blue bin, on your left. Aluminum cans are recyclable once the liquid is poured out. Thank you! | PASS |

## How to read this

- A scenario passes only if the bin is right, any needed instruction (such as pouring out liquid) is given, and Sorty behaved sensibly: asked when no camera could know, looked again when a camera could, and did not bother the person when the answer was already visible.
- The one-look camera is graded on the bin and instruction only.
- The pictures are Blender renders, not photos from a real bin camera. Real-camera behaviour still has to be checked on the device.
