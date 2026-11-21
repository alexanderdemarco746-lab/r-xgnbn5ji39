# Sorty scenario test report

Run: 2026-11-21 15:36  |  model: `claude-opus-5-5` (effort low)  |  station: 3bin  |  images: Blender renders in `tests/images`  |  estimated API cost of this run: $0.00

## Result

**Sorty got 0 of 2 scenarios right.**

Sorty's thinking time averaged 23.4 s per item. It needed nothing from the person on 2 of 2 items, and 0.0 requests per item on average.

## Every scenario

| Scenario | What Sorty did | Final answer | Result |
|---|---|---|---|
| Pizza box, greasy inside | answered at once | [error] I can't tell right now. Please check the labels on the bins. | FAIL: ended with 'error' (rate limited by the API), expected 'verdict' |
| Soda can, half full | answered at once | [error] I can't tell right now. Please check the labels on the bins. | FAIL: ended with 'error' (rate limited by the API), expected 'verdict' |

## How to read this

- A scenario passes only if the bin is right, any needed instruction (such as pouring out liquid) is given, and Sorty behaved sensibly: asked when no camera could know, looked again when a camera could, and did not bother the person when the answer was already visible.
- The one-look camera is graded on the bin and instruction only.
- The pictures are Blender renders, not photos from a real bin camera. Real-camera behaviour still has to be checked on the device.
