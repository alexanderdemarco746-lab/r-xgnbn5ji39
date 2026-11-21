# Sorty scenario test report

Run: 2026-11-21 15:34  |  model: `claude-haiku-5-5` (effort low)  |  station: 3bin  |  images: Blender renders in `tests/images`  |  estimated API cost of this run: $0.00

## Result

**Sorty got 1 of 2 scenarios right.**

Sorty's thinking time averaged 3.6 s per item. It needed nothing from the person on 1 of 2 items, and 0.5 requests per item on average.

## Every scenario

| Scenario | What Sorty did | Final answer | Result |
|---|---|---|---|
| Pizza box, greasy inside | asked to open show inside | Green bin, in the middle. Greasy or cheesy pizza boxes go to compost, even the whole box. Thank you! | PASS |
| Soda can, half full | answered at once | First, pour out any drink. Then: blue bin, on your left. Empty aluminum cans go in recycling, but any liquid must be poured out first. Thank you! | FAIL: should have asked the person (no camera can see this) |

## How to read this

- A scenario passes only if the bin is right, any needed instruction (such as pouring out liquid) is given, and Sorty behaved sensibly: asked when no camera could know, looked again when a camera could, and did not bother the person when the answer was already visible.
- The one-look camera is graded on the bin and instruction only.
- The pictures are Blender renders, not photos from a real bin camera. Real-camera behaviour still has to be checked on the device.
