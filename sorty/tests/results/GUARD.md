# Instant alert test report

Run: 2026-11-21 16:46  |  fast model: `claude-haiku-5-5`  |  picture size: 512 px  |  pictures: Blender renders in `tests/images`  |  estimated API cost of this run: $0.008

## Result

| What was shown | Result |
|---|---|
| Load-wreckers (battery, phone, vape, plastic bag, bag of trash) | alert raised on **10 of 10** |
| Ordinary items (bottles, cans, boxes, cups, food and so on) | false alarm on **0 of 52** |
| Time for one fast look | typically **1.0 s**, slowest 2.8 s |

The fast look ran on its own here, several pictures at a time. In the product it runs beside the careful model, and only an alert it is sure about is shown; when it stays silent the careful model answers as usual.

## Every picture

| Picture | Should alert as | Fast model said | It saw | Time | Result |
|---|---|---|---|---|---|
| banana_peel.jpg | - | (silent) | banana peel | 1.1 s | silent, correct |
| banana_peel.jpg | - | (silent) | banana peel | 1.7 s | silent, correct |
| battery_aa.jpg | battery | battery | two AA batteries | 1.0 s | caught |
| battery_aa.jpg | battery | battery | two AA batteries | 1.1 s | caught |
| blurry_dark.jpg | - | (silent) | red drink can | 1.0 s | silent, correct |
| blurry_dark.jpg | - | (silent) | red drink can | 1.0 s | silent, correct |
| cardboard_box_clean.jpg | - | (silent) | empty cardboard box | 0.9 s | silent, correct |
| cardboard_box_clean.jpg | - | (silent) | empty cardboard box | 1.9 s | silent, correct |
| carton_empty.jpg | - | (silent) | orange juice carton | 0.9 s | silent, correct |
| carton_empty.jpg | - | (silent) | orange juice carton | 0.9 s | silent, correct |
| chip_bag.jpg | - | (silent) | chip bag | 1.2 s | silent, correct |
| chip_bag.jpg | - | (silent) | chip bag | 1.2 s | silent, correct |
| clamshell_closed.jpg | - | (silent) | white foam takeout container | 1.2 s | silent, correct |
| clamshell_closed.jpg | - | (silent) | white foam takeout container | 1.0 s | silent, correct |
| clamshell_open_food.jpg | - | (silent) | takeout food tray | 1.0 s | silent, correct |
| clamshell_open_food.jpg | - | (silent) | takeout food tray | 1.0 s | silent, correct |
| clear_bottle_empty.jpg | - | (silent) | plastic water bottle | 1.1 s | silent, correct |
| clear_bottle_empty.jpg | - | (silent) | water bottle | 1.7 s | silent, correct |
| clear_bottle_half_cola.jpg | - | (silent) | cola plastic bottle | 1.0 s | silent, correct |
| clear_bottle_half_cola.jpg | - | (silent) | cola bottle | 1.9 s | silent, correct |
| coffee_cup_lid.jpg | - | (silent) | paper coffee cup | 1.0 s | silent, correct |
| coffee_cup_lid.jpg | - | (silent) | disposable coffee cup | 1.5 s | silent, correct |
| cold_cup_bottom_compostable.jpg | - | (silent) | clear plastic cup | 0.9 s | silent, correct |
| cold_cup_bottom_compostable.jpg | - | (silent) | clear plastic cup | 1.1 s | silent, correct |
| cold_cup_bottom_pet.jpg | - | (silent) | clear plastic bottle | 1.2 s | silent, correct |
| cold_cup_bottom_pet.jpg | - | (silent) | clear plastic bottle | 0.9 s | silent, correct |
| cold_cup_side.jpg | - | (silent) | clear plastic cup | 1.1 s | silent, correct |
| cold_cup_side.jpg | - | (silent) | clear plastic cup | 1.0 s | silent, correct |
| empty_scene.jpg | - | (silent) | nothing visible | 0.9 s | silent, correct |
| empty_scene.jpg | - | (silent) | nothing visible | 0.9 s | silent, correct |
| glass_bottle_empty.jpg | - | (silent) | green glass bottle | 0.9 s | silent, correct |
| glass_bottle_empty.jpg | - | (silent) | green glass bottle | 1.7 s | silent, correct |
| greasy_napkin.jpg | - | (silent) | crumpled food wrappers | 1.2 s | silent, correct |
| greasy_napkin.jpg | - | (silent) | crumpled food wrappers | 1.0 s | silent, correct |
| opaque_bottle.jpg | - | (silent) | shampoo bottle | 1.5 s | silent, correct |
| opaque_bottle.jpg | - | (silent) | shampoo bottle | 1.0 s | silent, correct |
| pizza_box_closed.jpg | - | (silent) | pizza box | 1.0 s | silent, correct |
| pizza_box_closed.jpg | - | (silent) | pizza box | 0.9 s | silent, correct |
| pizza_box_open_clean.jpg | - | (silent) | empty pizza box | 1.1 s | silent, correct |
| pizza_box_open_clean.jpg | - | (silent) | empty pizza box | 1.2 s | silent, correct |
| pizza_box_open_greasy.jpg | - | (silent) | greasy pizza box | 1.0 s | silent, correct |
| pizza_box_open_greasy.jpg | - | (silent) | greasy pizza box | 1.5 s | silent, correct |
| pizza_box_open_leftovers.jpg | - | (silent) | pizza slices in box | 1.1 s | silent, correct |
| pizza_box_open_leftovers.jpg | - | (silent) | pizza slices in box | 1.8 s | silent, correct |
| pizza_box_open_moldy.jpg | - | (silent) | moldy pizza in box | 0.9 s | silent, correct |
| pizza_box_open_moldy.jpg | - | (silent) | open pizza box with moldy pizza | 1.0 s | silent, correct |
| plastic_bag.jpg | plastic_bag | plastic_bag | white plastic shopping bag | 1.5 s | caught |
| plastic_bag.jpg | plastic_bag | plastic_bag | white plastic shopping bag | 1.3 s | caught |
| plastic_fork.jpg | - | (silent) | white plastic fork and knife | 1.0 s | silent, correct |
| plastic_fork.jpg | - | (silent) | plastic fork and knife | 1.0 s | silent, correct |
| smartphone.jpg | electronics | electronics | smartphone | 1.0 s | caught |
| smartphone.jpg | electronics | electronics | smartphone | 1.1 s | caught |
| soda_can.jpg | - | (silent) | cola can | 1.3 s | silent, correct |
| soda_can.jpg | - | (silent) | cola can | 0.9 s | silent, correct |
| spray_can.jpg | - | (silent) | spray paint can | 1.2 s | silent, correct |
| spray_can.jpg | - | (silent) | spray paint can | 1.0 s | silent, correct |
| tied_bag.jpg | bagged_trash | bagged_trash | tied plastic trash bag | 0.9 s | caught |
| tied_bag.jpg | bagged_trash | bagged_trash | tied plastic bag | 1.1 s | caught |
| two_items_peel_bottle.jpg | - | (silent) | banana peel | 1.1 s | silent, correct |
| two_items_peel_bottle.jpg | - | (silent) | banana peel | 0.9 s | silent, correct |
| vape.jpg | vape | vape | disposable vape pen | 2.8 s | caught |
| vape.jpg | vape | vape | disposable vape pen | 2.3 s | caught |

## How to read this

- The pictures are Blender renders, not photos from a real bin camera, and each load-wrecker has only one picture.
- A missed alert is not a wrong answer: the careful model still sends the item to the right place, a few seconds later.
- A false alarm would be a wrong answer, which is why the fast model is told to stay silent unless it is sure.
