# Sorty scenario test report

Run: 2026-11-21 16:30  |  model: `claude-opus-5-5` (effort low)  |  station: 3bin  |  images: Blender renders in `tests/images`  |  estimated API cost of this run: $1.14

## Result

**Sorty got 32 of 33 scenarios right.**

Same model, same rules, same pictures. The only difference is whether it may look again and ask:

| Method | Correct bin and instruction | On the items whose answer is hidden |
|---|---|---|
| One-look camera (answers from the first picture) | 28 of 33 | 9 of 14 |
| Sorty (looks again, asks, runs specialist checks) | 32 of 33 | 13 of 14 |

Sorty's thinking time averaged 5.0 s per item. It needed nothing from the person on 12 of 33 items, and 0.7 requests per item on average.

## Every scenario

| Scenario | What Sorty did | Final answer | Result | One-look camera |
|---|---|---|---|---|
| Pizza box, greasy inside | asked to open show inside; ran contamination check | Green bin, in the middle. Greasy pizza boxes and crumbs go in compost. Thank you! | PASS | ok: Green bin, in the middle. Pizza boxes, greasy or clean, can always go in compost. Thank you! |
| Pizza box, clean inside | asked to open show inside; ran contamination check | Blue bin, on your left. Clean, dry pizza boxes can be recycled. Thank you! | PASS | WRONG: Green bin, in the middle. Pizza boxes, greasy or not, can go in compost. Thank you! |
| Pizza box with leftover slices | asked to open show inside; ran contamination check | Green bin, in the middle. Greasy boxes and leftover food both go in compost. Thank you! | PASS | ok: Green bin, in the middle. Greasy pizza boxes compost, and clean ones compost fine too. Thank you! |
| Pizza box, moldy leftovers inside | asked to open show inside; ran contamination check | Green bin, in the middle. Greasy or moldy boxes and old food both compost. Thank you! | PASS | ok: Green bin, in the middle. Pizza boxes, greasy or clean, can always go in compost. Thank you! |
| Foam takeout box with food inside | asked to open show inside; ran label check | Scrape food into green bin. Leftover food: green bin, in the middle. Takeout box: black bin, on your right. Thank you! | PASS | ok: First, scrape any food into compost. Then: black bin, on your right. Unmarked white takeout boxes may be foam, so landfill. Thank you! |
| Clear cup, marked compostable underneath | asked to show bottom; ran label check | Green bin, in the middle. Cups marked compostable go in the green bin. Thank you! | PASS | WRONG: Black bin, on your right. Clear cups without a mark go in landfill. Thank you! |
| Clear cup, marked 1 PETE underneath | asked to show bottom; ran label check | Blue bin, on your left. Empty cups marked 1 PETE go in recycling. Thank you! | PASS | WRONG: Black bin, on your right. Unmarked clear cups go to landfill; check bottoms for marks. Thank you! |
| Soda can, empty | asked "Is there any drink left inside?" | Blue bin, on your left. Empty metal cans go in the blue recycling bin. Thank you! | PASS | ok: First, pour out any leftover soda. Then: blue bin, on your left. Empty metal cans go in the blue recycling bin. Thank you! |
| Soda can, half full | asked "Is there any drink left inside?" | First, pour the drink down a drain. Then: blue bin, on your left. Empty cans recycle, but drinks never go in bins. Thank you! | PASS | ok: First, pour out any leftover drink. Then: blue bin, on your left. Empty metal cans go in the blue recycling bin. Thank you! |
| Paper coffee cup with lid, some coffee left | asked "Is there still coffee inside?"; asked to show bottom | Pour out the coffee. Coffee cup and lid: black bin, on your right. Slide off the sleeve. Cardboard sleeve: blue bin, on your left. Thank you! | FAIL: sent something to 'recycle' (correct: landfill) | WRONG: Pour out any leftover coffee. Coffee cup and lid: black bin, on your right. Slide the sleeve off. Cardboard sleeve: blue bin, on your left. Thank you! |
| Spray paint can, still has paint | asked "Is the can completely empty, no spray?" | Not in these bins. Please use the hazardous waste drop-off. Spray cans with paint left can catch fire or burst. Thank you! | PASS | ok: Not in these bins. Please use the hazardous waste drop-off. Spray paint cans can catch fire, so they need special drop-off. Thank you! |
| Spray paint can, completely empty | asked "Is the can completely empty, no spray left?" | Blue bin, on your left. Fully empty spray cans are metal, so recycle them. Thank you! | PASS | WRONG: Not in these bins. Please use the hazardous waste drop-off. Paint and spray cans under pressure can catch fire. Thank you! |
| Opaque bottle, person does not know | asked to show bottom | Black bin, on your right. Without a 1, 2 or 5 mark, plastic goes to landfill. Thank you! | PASS | ok: First, squeeze out any leftover shampoo. Then: black bin, on your right. Only bottles marked 1, 2 or 5 go in recycling. Thank you! |
| Tied bag of mixed trash | answered at once | Black bin, on your right. Tied bags of mixed trash always go to landfill. Thank you! | PASS | ok: Black bin, on your right. Tied bags of mixed trash go in landfill. Thank you! |
| Clear bottle, visibly empty | answered at once | Blue bin, on your left. Empty plastic bottles go in recycling, cap on. Thank you! | PASS | ok: Blue bin, on your left. Empty plastic bottles go in recycling, cap on. Thank you! |
| Clear bottle, half full of cola | answered at once | First, pour the cola down a drain. Then: blue bin, on your left. Empty plastic bottles go in recycling, cap on. Thank you! | PASS | ok: First, pour out the cola. Then: blue bin, on your left. Empty bottles recycle; drinks go down the drain. Thank you! |
| Banana peel | answered at once | Green bin, in the middle. Fruit peels and food scraps go in compost. Thank you! | PASS | ok: Green bin, in the middle. Fruit peels and food scraps go in compost. Thank you! |
| Clean shipping box | answered at once | Blue bin, on your left. Clean, dry cardboard boxes go in recycling. Thank you! | PASS | ok: Blue bin, on your left. Clean, dry cardboard goes in recycling, label and all. Thank you! |
| Empty chip bag | answered at once | Black bin, on your right. Shiny chip bags aren't foil, so they can't be recycled. Thank you! | PASS | ok: Black bin, on your right. Shiny chip bags aren't foil, so they go to landfill. Thank you! |
| Used greasy napkins | answered at once | Green bin, in the middle. Used napkins with food on them go in compost. Thank you! | PASS | ok: Green bin, in the middle. Napkins with food on them go in compost. Thank you! |
| Plastic fork and knife | asked to flip over | Black bin, on your right. Utensils go in landfill unless marked compostable. Thank you! | PASS | ok: Black bin, on your right. Plastic utensils go in landfill unless marked compostable. Thank you! |
| Empty glass bottle | answered at once | Blue bin, on your left. Empty glass bottles go in the blue recycling bin. Thank you! | PASS | ok: Blue bin, on your left. Empty glass bottles go in the blue recycling bin. Thank you! |
| AA batteries | answered at once | Not in these bins. Please use the battery drop-off. Batteries can start fires, so never bin them. Thank you! | PASS | ok: Not in these bins. Please use the battery drop-off. Batteries can start fires, so never bin them. Thank you! |
| Old smartphone | answered at once | Not in these bins. Please use the battery and e-waste drop-off. Phone batteries can start fires, so never bin them. Thank you! | PASS | ok: Not in these bins. Please use the battery and e-waste drop-off. Phones have batteries that can start fires. Thank you! |
| Banana peel and empty bottle together | answered at once | Banana peel: green bin, in the middle. Pour out any leftover water. Plastic water bottle: blue bin, on your left. Thank you! | PASS | ok: Banana peel: green bin, in the middle. Pour out any water. Plastic water bottle: blue bin, on your left. Thank you! |
| Nothing presented | answered at once | [no_item] Hold your item up to the camera. | PASS | ok: [no_item] Hold your item up to the camera. |
| Dark blurry frame, then a clear one | asked to hold still; asked "Is there any soda left inside?" | Blue bin, on your left. Empty metal cans go in the blue bin. Thank you! | PASS | ok: First, pour out any drink. Then: blue bin, on your left. Empty metal cans go in the blue recycle bin. Thank you! |
| Soda can, person walks off without answering | asked "Is there any drink left inside?" | First, pour out any drink left. Then: blue bin, on your left. Empty cans recycle; drinks go down the drain. Thank you! | PASS | ok: First, pour out any leftover drink. Then: blue bin, on your left. Empty metal cans go in the blue recycling bin. Thank you! |
| Pizza box, person refuses to open it | asked to open show inside | Green bin, in the middle. Pizza boxes can always go in compost, greasy or clean. Thank you! | PASS | ok: Green bin, in the middle. Pizza boxes, greasy or not, can always go in compost. Thank you! |
| Clear cup, person does not show the bottom | asked to show bottom | Black bin, on your right. Clear cups need a 1 or compostable mark underneath. Thank you! | PASS | ok: Black bin, on your right. Clear cups without a visible mark go in landfill. Thank you! |
| Soda can, Spanish speaker | asked "¿La lata está vacía?" | Contenedor azul, a tu izquierda. Las latas vacías de aluminio se reciclan. ¡Gracias! | PASS | ok: Primero, vacía lo que quede de bebida. Luego: contenedor azul, a tu izquierda. Las latas vacías van al reciclaje azul. ¡Gracias! |
| Soda can, distracted answer | asked "Is there any drink left inside?" | First, pour out any drink. Then: blue bin, on your left. Empty metal cans go in the blue recycling bin. Thank you! | PASS | ok: First, pour out any leftover drink. Then: blue bin, on your left. Empty metal cans go in the blue recycling bin. Thank you! |
| Soda can, person tries to override the rules | asked "Is there any drink left inside?" | First, pour out any drink. Then: blue bin, on your left. Empty metal cans go in the blue recycle bin. Thank you! | PASS | ok: First, pour out any leftover drink. Then: blue bin, on your left. Empty metal cans go in the blue recycling bin. Thank you! |

## How to read this

- A scenario passes only if the bin is right, any needed instruction (such as pouring out liquid) is given, and Sorty behaved sensibly: asked when no camera could know, looked again when a camera could, and did not bother the person when the answer was already visible.
- The one-look camera is graded on the bin and instruction only.
- The pictures are Blender renders, not photos from a real bin camera. Real-camera behaviour still has to be checked on the device.
