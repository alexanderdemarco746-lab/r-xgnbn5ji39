# Sorty scenario test report

Run: 2026-11-21 15:38  |  model: `claude-sonnet-5-5` (effort low)  |  station: 3bin  |  images: Blender renders in `tests/images`  |  estimated API cost of this run: $0.04

## Result

**Sorty got 3 of 3 scenarios right.**

Sorty's thinking time averaged 7.1 s per item. It needed nothing from the person on 0 of 3 items, and 1.0 requests per item on average.

## Every scenario

| Scenario | What Sorty did | Final answer | Result |
|---|---|---|---|
| Pizza box, greasy inside | asked to open show inside; ran contamination check | Green bin, in the middle. Greasy or cheesy cardboard goes in compost, box and all. Thank you! | PASS |
| Pizza box, clean inside | asked to open show inside; ran contamination check | Blue bin, on your left. Clean, dry cardboard pizza boxes can be recycled. Thank you! | PASS |
| Soda can, half full | asked "Is the can empty?" | First, pour out the rest of the cola. Then: blue bin, on your left. Liquids never go in bins; empty aluminum cans are recycled. Thank you! | PASS |

## How to read this

- A scenario passes only if the bin is right, any needed instruction (such as pouring out liquid) is given, and Sorty behaved sensibly: asked when no camera could know, looked again when a camera could, and did not bother the person when the answer was already visible.
- The one-look camera is graded on the bin and instruction only.
- The pictures are Blender renders, not photos from a real bin camera. Real-camera behaviour still has to be checked on the device.
