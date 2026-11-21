# Sorty scenario test report

Run: 2026-11-21 16:50  |  model: `claude-opus-5-5` (effort low)  |  station: 3bin  |  images: Blender renders in `tests/images`  |  estimated API cost of this run: $0.91

## Result

**Sorty got 35 of 36 scenarios right.**

Sorty's thinking time averaged 4.9 s per item. It needed nothing from the person on 14 of 36 items, and 0.7 requests per item on average.

## Every scenario

| Scenario | What Sorty did | Final answer | Result |
|---|---|---|---|
| Pizza box, greasy inside | asked to open show inside; ran contamination check | Green bin, in the middle. Greasy pizza boxes go in compost, crumbs too. Thank you! | PASS |
| Pizza box, clean inside | asked to open show inside; ran contamination check | Blue bin, on your left. Clean, dry pizza boxes go in recycling. Thank you! | PASS |
| Pizza box with leftover slices | asked to open show inside; ran contamination check | Green bin, in the middle. Greasy boxes and leftover food both go to compost. Thank you! | PASS |
| Pizza box, moldy leftovers inside | asked to open show inside; ran contamination check | Green bin, in the middle. Greasy or moldy boxes and old pizza all compost. Thank you! | PASS |
| Foam takeout box with food inside | asked to show bottom; asked "Is the box marked compostable?" | First, scrape any food into compost. Then: black bin, on your right. Foam can't be recycled or composted, so landfill. Thank you! | PASS |
| Clear cup, marked compostable underneath | asked to show bottom; ran label check | Green bin, in the middle. Cups marked compostable go in the green bin. Thank you! | PASS |
| Clear cup, marked 1 PETE underneath | asked to show bottom; ran label check | Blue bin, on your left. Empty cups marked 1 PETE go in recycling. Thank you! | PASS |
| Soda can, empty | asked "Is there any drink left inside?" | Blue bin, on your left. Empty metal cans go in the blue recycling bin. Thank you! | PASS |
| Soda can, half full | asked "Is there any drink left inside?" | First, pour the drink down a sink. Then: blue bin, on your left. Empty cans recycle, but drinks never go in bins. Thank you! | PASS |
| Paper coffee cup with lid, some coffee left | asked "Is there still coffee inside?"; asked to show bottom | Pour out the coffee. Coffee cup and lid: black bin, on your right. Slide off the sleeve. Cardboard sleeve: blue bin, on your left. Thank you! | FAIL: sent something to 'recycle' (correct: landfill) |
| Spray paint can, still has paint | asked "Is the spray can completely empty?" | Not in these bins. Please use the hazardous waste drop-off. Spray cans with paint left can catch fire. Thank you! | PASS |
| Spray paint can, completely empty | asked "Is the spray can completely empty?" | Blue bin, on your left. Fully empty spray cans are metal, so they recycle. Thank you! | PASS |
| Opaque bottle, person does not know | asked to show bottom | Black bin, on your right. Unmarked plastic goes to landfill; empty bottles marked 1, 2, 5 recycle. Thank you! | PASS |
| Tied bag of mixed trash | answered at once | Black bin, on your right. Tied bags of mixed trash go in landfill. Thank you! | PASS |
| Clear bottle, visibly empty | answered at once | Blue bin, on your left. Empty plastic bottles go in recycling, cap on. Thank you! | PASS |
| Clear bottle, half full of cola | answered at once | First, pour out the cola. Then: blue bin, on your left. Empty bottles get recycled, and you can leave the cap on. Thank you! | PASS |
| Banana peel | answered at once | Green bin, in the middle. Fruit peels and food scraps go in compost. Thank you! | PASS |
| Clean shipping box | answered at once | Blue bin, on your left. Clean, dry cardboard boxes go in recycling. Thank you! | PASS |
| Empty chip bag | answered at once | Black bin, on your right. Shiny chip bags aren't foil, so they can't be recycled. Thank you! | PASS |
| Used greasy napkins | answered at once | Green bin, in the middle. Used napkins with food on them go in compost. Thank you! | PASS |
| Plastic fork and knife | asked to flip over | Black bin, on your right. Plastic utensils go to landfill unless marked compostable. Thank you! | PASS |
| Empty glass bottle | answered at once | Blue bin, on your left. Empty glass bottles go in the blue recycling bin. Thank you! | PASS |
| AA batteries | answered at once | Not in these bins. Please use the battery drop-off. Batteries can start fires, so never bin them. Thank you! | PASS |
| Old smartphone | answered at once | Not in these bins. Please use the battery and e-waste drop-off. Phones have batteries that can start fires in bins. Thank you! | PASS |
| Banana peel and empty bottle together | answered at once | Pour out any water left. Water bottle: blue bin, on your left. Banana peel: green bin, in the middle. Thank you! | PASS |
| Nothing presented | answered at once | [no_item] Hold your item up to the camera. | PASS |
| Dark blurry frame, then a clear one | asked to hold still; asked "Is there still drink inside?" | Blue bin, on your left. Empty metal cans go in the blue recycling bin. Thank you! | PASS |
| Soda can, person walks off without answering | asked "Is there any drink left inside?" | First, pour out any drink. Then: blue bin, on your left. Empty cans go in recycling, drinks go down the drain. Thank you! | PASS |
| Pizza box, person refuses to open it | asked to open show inside | Green bin, in the middle. Pizza boxes are always fine in compost, greasy or clean. Thank you! | PASS |
| Clear cup, person does not show the bottom | asked to show bottom | Black bin, on your right. Clear cups without a visible mark go to landfill. Thank you! | PASS |
| Soda can, Spanish speaker | asked "¿La lata está vacía?" | Contenedor azul, a tu izquierda. Las latas vacías de metal se reciclan. ¡Gracias! | PASS |
| Soda can, distracted answer | asked "Is there any drink left inside?" | First, pour out any leftover drink. Then: blue bin, on your left. Empty cans go in the blue recycle bin. Thank you! | PASS |
| Soda can, person tries to override the rules | asked "Is there any drink left inside?" | First, pour out any leftover drink. Then: blue bin, on your left. Empty metal cans go in the blue recycling bin. Thank you! | PASS |
| Disposable vape | answered at once | Not in these bins. Please use the battery or e-waste drop-off. Vapes have batteries inside that can start bin fires. Thank you! | PASS |
| Empty plastic shopping bag | answered at once | Black bin, on your right. Plastic bags jam recycling machines, so they go in landfill. Thank you! | PASS |
| Juice carton, empty | asked "Is there any juice left inside?" | Blue bin, on your left. Empty juice and milk cartons go in recycling. Thank you! | PASS |

## How to read this

- A scenario passes only if the bin is right, any needed instruction (such as pouring out liquid) is given, and Sorty behaved sensibly: asked when no camera could know, looked again when a camera could, and did not bother the person when the answer was already visible.
- The one-look camera is graded on the bin and instruction only.
- The pictures are Blender renders, not photos from a real bin camera. Real-camera behaviour still has to be checked on the device.
