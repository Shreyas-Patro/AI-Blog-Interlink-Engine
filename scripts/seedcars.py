#!/usr/bin/env python3
"""Creates 5 interlinked car articles in ./test_posts/

Demo pattern:
  - One pillar article ("How to Buy a Car") references short category names
  - Four category articles ("What is an SUV", "What is a Sedan", etc.)
    each have those short names as anchor_phrases
  - The category articles also cross-reference each other naturally

Expected result: 8-12 high-quality links across 5 articles.

Run: python scripts/seed.py
"""
from pathlib import Path

posts = {

    # ── PILLAR ARTICLE ──────────────────────────────────────────────────────
    "how-to-buy-a-car.md": """---
title: "How to Buy a Car"
slug: how-to-buy-a-car
url: https://yourblog.com/blogs/how-to-buy-a-car
tags: [cars, buying, guide]

---

## Start With What You Actually Need

Buying a car is one of the larger financial decisions most people make, and the right starting point is almost always your actual daily use rather than the car you find aesthetically appealing. The ideal car for a family of five living in the suburbs is very different from the ideal car for a single person commuting thirty kilometres each way in heavy city traffic. Be honest with yourself about how you will use the vehicle ninety percent of the time, not the edge cases that come up twice a year.

Start by categorising the body types that suit your life. The four dominant categories in the passenger car market are the SUV, the sedan, the hatchback, and the electric vehicle, and each serves a fundamentally different set of needs. An SUV gives you space, height, and the ability to handle rough roads. A sedan gives you a comfortable ride, better fuel efficiency, and a more car-like driving experience. A hatchback gives you flexibility, easy parking, and a low price of entry. An electric vehicle gives you running-cost savings and a fundamentally different driving feel.

Once you know the body type that fits your life, the rest of the process becomes a search rather than an exploration. You are no longer looking at every new car on the market — you are comparing the three or four best options in one category against each other. This narrowing is the single most effective thing you can do to make car buying less exhausting and more likely to result in a good decision.

## Budget Honestly, Including Running Costs

The sticker price is only a fraction of what a car actually costs you. The total cost of ownership over five years is what you should be budgeting against, and it includes fuel or charging, insurance, service and maintenance, depreciation, and the cost of financing if you are taking a loan. A cheap car with poor fuel economy and high maintenance costs can easily cost more over five years than a more expensive car with low running costs.

For most buyers, depreciation is the single largest component of total ownership cost, and it varies dramatically between body types and brands. An SUV from a premium brand typically loses thirty-five to forty-five percent of its value in the first three years. A well-regarded sedan might lose twenty-five percent in the same period. A hatchback from a reliable manufacturer often holds its value better than either. These numbers are not fixed laws — specific models vary widely — but the pattern is consistent enough to be worth thinking about.

Running an electric vehicle changes the cost equation significantly. The per-kilometre running cost is a fraction of a petrol or diesel equivalent, but the purchase price is higher, and you need to factor in the cost of home charging infrastructure if you want the full convenience. Over a five-year ownership period with typical usage, an EV often works out cheaper overall, but the break-even point depends on how many kilometres you drive per year.

## Test Drive With Real Use Cases

Most test drives are useless. The dealership hands you the keys, you drive for fifteen minutes on a familiar route, and you come back with a vague positive impression. This tells you almost nothing about whether you will still be happy with the car in two years. A good test drive replicates how you will actually use the car, and that means driving it on your actual commute, parking it in your actual garage, and checking whether your actual family fits comfortably.

If you are considering an SUV, load it with luggage and passengers in the configuration you will most often use. Check visibility from the driver's seat with the rear seats occupied. Try parking in the tightest spot you regularly deal with. SUVs look similar on paper but feel very different once you have four adults and a boot full of bags inside.

If you are considering a sedan, pay particular attention to the ride quality on the worst road surface you regularly encounter. Sedans ride differently than SUVs on bad roads, and some handle it gracefully while others become genuinely unpleasant. The cabin noise at highway speeds is another factor that dealers rarely let you experience meaningfully on a short test drive.

## Negotiate on Total Cost, Not Monthly Payment

Dealers love to frame the price conversation in terms of monthly payment because it obscures the total amount you are actually paying. A thousand rupees a month "less" on the EMI might look like a win, but it often comes from extending the loan term by two years, which means you end up paying significantly more in total interest. Always negotiate on the out-the-door price in total, never on the monthly figure.

The out-the-door price includes the vehicle itself, registration, insurance, any accessories the dealer insists on bundling, and any handling or documentation charges they try to add. Dealers make substantial margin on the accessories and add-on services they push at the end of the deal. Most of these are things you do not need, or can buy aftermarket for half the price. Learning to say no to the add-ons is one of the most valuable skills in car buying.

Walking away is the most powerful negotiating tool you have, and most buyers are too emotionally committed to the car to use it. If the dealer will not meet your price, leave. There are other dealers, there are other brands, and the car is not worth more to you than your budget says it is worth. Buyers who are willing to walk away consistently pay less than buyers who are not.
""",

    # ── CATEGORY ARTICLE 1 ──────────────────────────────────────────────────
    "what-is-an-suv.md": """---
title: "What is an SUV"
slug: what-is-an-suv
url: https://yourblog.com/blogs/what-is-an-suv
tags: [cars, suv, guide]

---

## The Rise of the SUV

The SUV — short for Sport Utility Vehicle — has become the default body type for family car buyers in most markets, and the reasons are not mysterious once you understand what it actually offers. An SUV combines the elevated seating position of a truck with the comfort of a passenger car and the practicality of a larger interior space. This combination turns out to be something a very large number of buyers want once they experience it.

The modern SUV descends from the off-road utility vehicles of the 1980s and 1990s, but today's versions are almost entirely focused on comfort and on-road use. A contemporary compact SUV shares more DNA with a hatchback than with a Land Rover Defender. The elevated ride height and the rugged styling cues remain, but the drivetrain, the suspension, and the interior are all optimised for paved roads and the kind of driving most people actually do.

This evolution is why the SUV segment has fragmented so dramatically. At the small end you have crossover SUVs barely larger than a hatchback. In the middle you have comfortable five-seat family vehicles. At the large end you have three-row vehicles that genuinely compete with minivans. Deciding which sub-segment fits your needs is almost as important as deciding you want an SUV in the first place.

## Why Buyers Choose SUVs

The most common reason buyers move to an SUV is the elevated seating position. Sitting higher makes it easier to get in and out, gives you a better view of traffic, and provides a sense of safety that is partly perceptual and partly real. The visibility advantage is genuine — you can see over the tops of smaller cars and spot hazards earlier. Ease of entry matters more than young buyers appreciate, and it becomes a significant factor as buyers age.

Space is the second major draw. An SUV of any given footprint typically offers more usable interior volume than a sedan of the same exterior size, because the taller roofline allows for more passenger and luggage space. For families with small children, car seats, prams, and sports equipment, this extra volume is the difference between a car that works for daily life and one that constantly feels cramped.

Perceived safety also drives SUV sales, though the reality is more nuanced than the perception. SUVs are generally safer for their own occupants in a collision with a smaller vehicle, but are more likely to roll over than low-slung cars in certain scenarios. Modern stability control systems have largely neutralised the rollover risk, but the underlying physics has not changed. For most buyers in most conditions, a modern SUV is genuinely safe, but the safety advantage over a well-designed sedan or hatchback is smaller than most buyers assume.

## When an SUV is the Wrong Choice

If your driving is primarily urban, solo, and involves frequent parking in tight spaces, an SUV is often the wrong choice. You are paying for space and capability you will rarely use, and dealing with the downsides of a larger, thirstier vehicle every single day. For a single person commuting to work in a city, a hatchback is almost always a better fit than a compact SUV with similar interior capacity.

Fuel economy is the other reason to think twice. Even modern SUVs with efficient engines drink more fuel than an equivalent sedan or hatchback, and over a five-year ownership period the difference in running costs is substantial. If fuel economy is a primary concern, a sedan or an electric vehicle will almost always work out cheaper to run than an SUV.

Parking is a genuine daily annoyance for SUV owners in dense urban environments. The extra width and length means many older parking spots are tight to the point of being unusable. Some multi-level parking structures have height restrictions that exclude larger SUVs entirely. These are not dealbreakers for most buyers, but they are real inconveniences that are worth thinking about honestly during the buying process.
""",

    # ── CATEGORY ARTICLE 2 ──────────────────────────────────────────────────
    "what-is-a-sedan.md": """---
title: "What is a Sedan"
slug: what-is-a-sedan
url: https://yourblog.com/blogs/what-is-a-sedan
tags: [cars, sedan, guide]

---

## The Classic Passenger Car

A sedan is the traditional three-box passenger car — a separate engine compartment, passenger cabin, and enclosed boot — that defined what "car" meant for most of the twentieth century. Despite the rise of the SUV, the sedan remains the most comfortable and refined body type for pure on-road driving, and it retains a loyal following among buyers who prioritise ride quality and driving dynamics over interior volume.

The defining characteristic of a sedan is the separation of the cargo area from the passenger cabin. This separation brings real benefits: better sound insulation because the rear passengers are acoustically isolated from the boot, better crash structure because the boot provides a crumple zone behind the rear seats, and a cleaner driving feel because the weight distribution and aerodynamics are more balanced than in a taller vehicle.

Sedans come in every size from compact to full-size luxury, but the market in most countries has polarised around two segments. Compact and mid-size sedans compete with hatchbacks and SUVs for family buyers. Full-size and luxury sedans compete for a more specific audience that values comfort, prestige, and driving refinement over the versatility offered by other body types.

## Why Buyers Choose Sedans

Ride quality is the single most common reason buyers choose a sedan over an SUV of similar price. The lower centre of gravity, the longer wheelbase, and the more compliant suspension tuning that is possible without worrying about rollover produce a ride that is consistently more comfortable at both urban and highway speeds. Buyers who have driven both back to back often find the difference striking.

Fuel economy is typically better in a sedan than in an equivalent SUV, sometimes dramatically so. The lower weight, smaller frontal area, and more favourable aerodynamics all contribute to this advantage. For buyers who drive long distances, the fuel savings over a five-year ownership period can easily exceed one lakh rupees, which is real money in any budget.

Driving enjoyment is the quieter reason many enthusiasts still prefer sedans. The low seating position, the direct steering feel, and the balanced weight distribution make a well-designed sedan more engaging to drive than a typical SUV. For buyers who actually enjoy driving rather than just getting from A to B, this matters more than any spec sheet comparison.

## When a Sedan is the Wrong Choice

If you regularly carry tall items, bulky sports equipment, or more than three passengers with luggage, a sedan will feel cramped in ways that show up repeatedly in daily use. The boot of a compact sedan typically holds three medium suitcases; an equivalent SUV might hold five. For families who use their car for weekend trips with the whole family loaded in, the sedan's cargo limitations become irritating quickly.

Rough roads are the other clear case against a sedan. The low ground clearance that helps handling on smooth pavement becomes a liability on broken surfaces, steep ramps, and roads with deep potholes. Buyers who live in areas with genuinely poor road surfaces consistently find that the sedan is not the right body type for their daily reality, and a compact SUV or a rugged hatchback serves them better.

For buyers making a long list of cars to consider, a sedan is worth test driving even if your initial assumption was that you wanted an SUV. Many buyers who thought they wanted an SUV end up choosing a sedan once they actually drive both back to back, and vice versa. The goal of a good buying process is to challenge your initial assumptions rather than just confirm them.
""",

    # ── CATEGORY ARTICLE 3 ──────────────────────────────────────────────────
    "what-is-a-hatchback.md": """---
title: "What is a Hatchback"
slug: what-is-a-hatchback
url: https://yourblog.com/blogs/what-is-a-hatchback
tags: [cars, hatchback, guide]

---

## The Most Practical Body Type

A hatchback is a car with a rear door that opens upwards and includes the rear window, giving direct access to the cargo area from the back. This simple structural difference from a sedan produces a dramatically different car. The cargo area flows continuously into the passenger cabin, the rear seats typically fold down to extend it, and the overall length of the car is shorter for the same amount of usable interior space.

The hatchback has historically been the dominant body type in European and Asian markets where urban space is tight, fuel is expensive, and families prize practicality over prestige. In markets where SUVs have come to dominate, the hatchback retains a strong position at the entry level and among buyers who understand that it often delivers more real-world usefulness than its larger and more expensive alternatives.

Modern hatchbacks range from pure city cars barely longer than three metres to premium hot hatches that can outperform sports sedans in real-world conditions. The sub-segments are worth understanding because they serve very different buyers. A small city hatchback is the right car for an urban single person. A larger family hatchback competes directly with compact sedans and small SUVs. A hot hatch is an enthusiast's car that happens to look practical.

## Why Buyers Choose Hatchbacks

The single biggest advantage is the combination of small exterior size with flexible interior use. A hatchback that is genuinely easy to park in tight city spots can still carry a surprising amount of cargo when you fold the rear seats down. This flexibility means one car can handle both weekday commuting and weekend runs to the furniture store, which is a harder compromise for a sedan to make.

Running costs are consistently lower than equivalent sedans or SUVs. The smaller engine sizes typical in this segment produce better fuel economy, the lower weight reduces tyre wear, and insurance costs are often lower because hatchbacks tend to be involved in less severe collisions than larger vehicles. Over a five-year ownership period, the total cost savings versus an SUV can be substantial — often more than the difference in purchase price.

Ease of use in urban environments is an underrated benefit. The visibility out of a compact hatchback is typically excellent because the car is small enough that you can see its corners easily. Parallel parking is genuinely easier. Navigating through tight lanes and congested market streets is less stressful. For buyers whose driving is primarily urban, these daily experiences matter more than the theoretical advantages of a larger car.

## When a Hatchback is the Wrong Choice

For families with three or more children, a hatchback of any size will eventually feel constraining. The rear seat width is typically inadequate for three child seats, and the cargo area behind the rear seats is smaller than a sedan's boot or an SUV's loading space. At some point, family size forces buyers out of the hatchback segment regardless of how much they prefer the driving experience.

Highway cruising over long distances is another area where larger vehicles typically have an advantage. A compact hatchback can be noisy at highway speeds, less stable in strong crosswinds, and less comfortable over six-hour driving days than a sedan or SUV. For buyers who regularly drive long distances on open roads, the hatchback's urban advantages become less relevant and its highway limitations more significant.

If you are cross-shopping across body types, do not dismiss the hatchback without actually driving one. Many buyers who assume they need a larger car discover that a well-designed hatchback does almost everything they need while costing significantly less to run. The right body type is whichever one fits your actual usage, not whichever one signals the most status.
""",

    # ── CATEGORY ARTICLE 4 ──────────────────────────────────────────────────
    "what-is-an-electric-vehicle.md": """---
title: "What is an Electric Vehicle"
slug: what-is-an-electric-vehicle
url: https://yourblog.com/blogs/what-is-an-electric-vehicle
tags: [cars, ev, electric]

---

## How an Electric Vehicle Actually Works

An electric vehicle, or EV, is a car powered by an electric motor drawing energy from a battery pack, rather than by an internal combustion engine burning petrol or diesel. The core technology is simpler than a conventional car — fewer moving parts, no gearbox in most cases, no exhaust system, no fuel system — but the battery chemistry and the charging infrastructure are more demanding than most buyers initially appreciate.

The battery is the single most important component in any electric vehicle. Modern EVs use lithium-ion battery packs with capacities measured in kilowatt-hours. A typical compact EV has a battery between thirty and fifty kilowatt-hours, giving it a real-world range of two hundred to four hundred kilometres between charges. A larger or more premium EV may have a battery of seventy-five to one hundred kilowatt-hours and a range exceeding five hundred kilometres. The battery is also the most expensive single component, typically accounting for a third or more of the total vehicle cost.

Charging an EV happens in two fundamentally different ways. Home charging through a domestic wall-mounted charger is slow but convenient — you plug in overnight and wake up with a full battery. DC fast charging at a public station is much faster, delivering eighty percent charge in thirty to forty-five minutes on modern chargers, but requires you to find and use public infrastructure. Most EV owners do the vast majority of their charging at home, with public fast charging reserved for long trips.

## Why Buyers Choose Electric Vehicles

Running cost savings are the most concrete reason to buy an EV, and the numbers are genuinely striking. The per-kilometre cost of running an EV on home electricity is typically one-fifth to one-tenth of the cost of running an equivalent petrol car. Over a five-year ownership period, this can mean two to three lakh rupees in fuel savings for a typical family driver. Service costs are also significantly lower because there are fewer wear items and no routine oil changes.

The driving feel of an electric vehicle is distinctive enough that many buyers who try one find it hard to go back. Instant torque from standstill, smooth and silent acceleration, and the absence of gear shifts produce a driving experience that is genuinely more relaxed than a petrol equivalent. In dense urban traffic, where you are accelerating and decelerating constantly, the difference is particularly noticeable.

Environmental considerations drive a meaningful portion of EV purchases, though the reality is more nuanced than simple advocacy suggests. An EV powered by electricity from a coal-dominated grid is not meaningfully cleaner than a modern petrol car over its full life cycle. As grids shift toward renewable generation, the environmental advantage grows, but buyers should be honest about the current realities rather than assuming any EV is automatically clean.

## When an Electric Vehicle is the Wrong Choice

If you cannot charge at home, an EV is significantly harder to live with than a petrol car. The entire cost and convenience proposition of EV ownership depends on having reliable, cheap home charging. Buyers living in apartments without dedicated parking, or in locations where installing a home charger is not practical, should think very carefully before committing to an EV. Relying entirely on public charging is possible but expensive and less convenient than the advertising suggests.

Long-distance driving remains more complicated in an EV than in a petrol car. Planning routes around fast charging stations, waiting thirty to forty-five minutes at charge points, and accepting that extreme cold or highway speeds reduce real-world range are all part of the reality. For buyers who make frequent long trips, these limitations matter. The situation is improving rapidly as charging infrastructure expands, but in most markets in 2026, it is not yet as convenient as refuelling a petrol car at an existing fuel station.

Purchase price is still meaningfully higher than an equivalent petrol car, though the gap is narrowing. For buyers whose driving volumes are low, the running cost savings may not recover the price premium within a reasonable ownership period. For buyers who drive more than fifteen thousand kilometres a year, the EV typically works out cheaper over five years. Running the numbers honestly for your specific usage pattern is essential rather than assuming the EV is automatically a better economic choice.
""",
}

dest = Path("test_posts")
dest.mkdir(exist_ok=True)

# Remove any existing .md files to keep a clean test set
for old in dest.glob("*.md"):
    old.unlink()
    print(f"Removed old: {old}")

for filename, content in posts.items():
    (dest / filename).write_text(content, encoding="utf-8")
    print(f"Created: {dest / filename}")

print(f"\n✓ {len(posts)} test articles created in ./test_posts/")
print("\nNext steps:")
print("  python scripts/reset_data.py")
print("  python -m link_engine.cli run ./test_posts")
print("  python scripts/debug_phrases.py")
print("  python scripts/debug_matches.py")