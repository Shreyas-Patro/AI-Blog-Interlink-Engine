#!/usr/bin/env python3
"""Creates 3 interlinked test markdown articles in ./test_posts/

These articles are designed to exercise the link engine:
  - Each has title-derived long-tail phrases
  - Each has frontmatter anchor_phrases for additional coverage
  - Each references the other two's topics in natural prose
  - Expected result: 4-6 high-confidence inter-article links

Run: python scripts/seed.py
"""
from pathlib import Path

posts = {
    "kitchen-renovation-cost.md": """---
title: "How Much Does a Kitchen Renovation Cost in 2026"
slug: kitchen-renovation-cost
url: https://yourblog.com/blogs/kitchen-renovation-cost
tags: [renovation, kitchen, budget]
anchor_phrases:
  - "how much does a kitchen renovation cost"
  - "kitchen renovation cost"
  - "budget a kitchen renovation"
---

## What You Actually Pay For in a Kitchen Renovation

A full kitchen renovation in 2026 typically costs between fifteen and sixty thousand dollars, depending on the size of the space, the quality of materials, and how much structural work is involved. The enormous range catches many homeowners off guard, and it is the single biggest source of frustration when people start getting quotes from contractors. Understanding where the money actually goes is the first step toward setting a realistic budget.

Cabinetry is consistently the largest line item, typically accounting for thirty to forty percent of the total cost. Semi-custom cabinets from a mid-tier manufacturer run around six to twelve thousand dollars for an average-sized kitchen, while fully custom cabinetry can easily exceed twenty thousand. The jump from stock to custom is significant, and most homeowners end up somewhere in the middle with semi-custom options that allow for some personalisation without the premium of bespoke work.

Countertops are the second major expense. Quartz has overtaken granite as the default premium choice because it offers better stain resistance and requires no sealing. A kitchen with forty square feet of counter space will run between three and six thousand dollars in quartz, more if you choose exotic slabs or waterfall edges. Butcher block and laminate remain viable budget options but affect resale value in ways that are worth thinking about before you commit.

## The Hidden Costs Nobody Warns You About

Beyond the obvious line items — cabinets, counters, appliances, flooring — there is a whole category of expenses that homeowners consistently underestimate. Electrical work almost always costs more than the initial estimate, especially in older homes where the wiring needs to be brought up to current code. Moving a single outlet or adding a circuit for a new appliance can easily add fifteen hundred dollars to your bill.

Plumbing relocation is another source of budget blowouts. If your renovation plans involve moving the sink or adding a pot filler above the stove, you are not just paying for the new fixtures — you are paying for the labour to re-route supply lines and drains through walls and floors. In homes with slab foundations, this can mean breaking concrete, which adds serious time and cost.

The quality of your contractor matters more than almost anything else on this list. A good contractor will spot problems early, manage subcontractors effectively, and keep the project on schedule. How to choose a renovation contractor is something we cover in detail elsewhere, but the short version is: check references, verify insurance, and never pay more than ten percent upfront. The cheapest bid is rarely the best value once you account for the cost of fixing mistakes.

## How to Budget a Kitchen Renovation Realistically

The classic advice is to add twenty percent contingency to whatever number you start with, and in our experience this is still roughly correct. Kitchens are full of unknowns that only reveal themselves once demolition begins — water damage behind cabinets, ancient wiring in the walls, floors that are not level. The contingency is not a luxury, it is a realistic estimate of what a mid-sized renovation actually costs when real problems surface.

Think about your renovation in three tiers. A cosmetic refresh — paint, new hardware, perhaps a new countertop — can be done for under ten thousand dollars and deliver a surprising amount of visual impact. A mid-range renovation that replaces cabinets, counters, and appliances while keeping the existing layout typically lands between twenty and thirty-five thousand. A full gut renovation with layout changes, new lighting design, and premium finishes starts at forty and climbs from there.

Lighting is one of the most under-budgeted elements in kitchen renovations. Most homeowners allocate a few hundred dollars for fixtures and are shocked when the electrician's bill doubles that figure. The best modern kitchen lighting design combines ambient, task, and accent sources — and designing kitchen lighting properly requires thinking through how you actually use the space, not just where the old fixtures happened to be.

## When Renovating Makes Financial Sense

Kitchen renovations are among the highest-return home improvements you can make, but the financial logic depends entirely on your situation. If you are planning to sell within two years, a moderate mid-range renovation typically recovers seventy to eighty percent of its cost in increased sale price. A full luxury renovation recovers less, proportionally, because buyers rarely pay a premium for the top-tier finishes that cost the most. The sweet spot for resale is a clean, well-executed mid-range renovation with broad appeal.

If you are renovating for yourself and plan to stay in the home for five or more years, the calculation changes. The return on a kitchen renovation is no longer primarily financial — it is about the quality of life you extract from using the space every day. A well-designed kitchen that you enjoy cooking in is genuinely one of the better investments you can make in your own happiness, and the financial return becomes a secondary consideration.
""",

    "choose-renovation-contractor.md": """---
title: "How to Choose a Renovation Contractor"
slug: choose-renovation-contractor
url: https://yourblog.com/blogs/choose-renovation-contractor
tags: [renovation, contractors, hiring]
anchor_phrases:
  - "how to choose a renovation contractor"
  - "choose a renovation contractor"
  - "choosing the right contractor"
  - "vetting a contractor"
---

## Why the Contractor Matters More Than the Design

Homeowners tend to obsess over design choices — the cabinet finish, the countertop material, the tile pattern — and treat contractor selection as an afterthought. This is exactly backwards. The best design in the world will be ruined by a careless contractor, and a modest renovation executed by a skilled team can look extraordinary. How to choose a renovation contractor is genuinely the most consequential decision you will make on a project, and it deserves more thought than most people give it.

The problem is that most homeowners do not know how to evaluate a contractor meaningfully. They get three bids, pick the one in the middle, check a couple of references, and hope for the best. This approach works perhaps sixty percent of the time. The other forty percent ends in delays, cost overruns, shoddy workmanship, or in the worst cases, outright abandonment of the project with a partial payment already pocketed. The downside of a bad contractor is severe enough that it is worth investing real effort in vetting a contractor properly before signing anything.

A good contractor has three qualities that are visible if you know where to look. They communicate clearly and consistently, even about bad news. They have a portfolio of recent work they can show you in person, not just photographs. And their subcontractor relationships are stable — the same plumber, the same electrician, the same tiler showing up on job after job. Each of these signals something important about how the business is actually run.

## Red Flags That Should End the Conversation

Certain behaviours should immediately disqualify a contractor regardless of how low their bid is. The most important is an unwillingness to provide proof of insurance. A legitimate contractor carries general liability insurance and workers compensation coverage, and they will provide certificates from their insurer directly to you or your insurance agent. A contractor who hesitates, delays, or provides photocopies instead of direct insurer verification is either uninsured or lying. Walk away.

Demands for large upfront payments are another unambiguous red flag. Industry standard is ten percent down at signing, with progress payments tied to specific milestones — demolition complete, rough-in complete, substantial completion. A contractor asking for thirty or fifty percent upfront is either cashflow-strapped or planning to take your money and disappear. Either way, it is not your problem to solve by paying them.

Verbal agreements on material changes should never happen. Once the contract is signed, every change needs to be in writing with a clear price before any work proceeds. Contractors who casually say "do not worry about it, we will sort it at the end" are setting you up for a painful conversation three months later when they present a change order for fifteen thousand dollars of work you did not realise you were authorising. Getting everything in writing is boring and tedious and absolutely essential.

## The Reference Check That Actually Works

Most reference checks are worthless because homeowners ask the wrong questions. Asking "were you happy with the work" produces a predictable yes from whichever clients the contractor chose to list as references. The useful questions are specific and uncomfortable. Did the project come in on budget — and if not, by how much? How were problems handled when they came up? Did they clean up at the end of every day? Would you hire them again for a larger project, or only something smaller?

Visit the reference in person if you can. Seeing the finished work, asking follow-up questions in the moment, and getting a sense of how the homeowner actually feels about the experience reveals things that a phone call cannot. It is a big ask of a stranger, but most people who had a good experience are surprisingly willing to show off the work. A contractor who is unwilling to provide references you can visit in person is telling you something.

Online reviews are noisy but useful in aggregate. Look for patterns across ten or more reviews rather than fixating on any single glowing or scathing one. Pay particular attention to how the contractor responds to negative reviews. A professional response that acknowledges the issue and explains what was done to address it is a good sign. A defensive or combative response is an extremely bad sign that tells you exactly how they will behave if your project goes sideways.

## Scoping the Bid Correctly

The biggest source of budget disputes on residential renovations is vague scopes of work. Bids should specify exactly what is included and exactly what is excluded, line by line. If a bid says "kitchen renovation" as a single line item, you do not have a scope — you have a wish. How much does a kitchen renovation cost is a question that cannot be answered without a detailed scope, and the same contractor can legitimately quote you three wildly different prices depending on what is actually in that scope.

Insist on a bid that breaks down costs into at least ten categories: demolition, framing and structural work, electrical rough-in, plumbing rough-in, insulation and drywall, flooring, cabinets, countertops, appliances, paint and trim, lighting design and installation, and final cleanup. Each category should have its own line item with both labour and materials broken out separately. This level of detail is standard practice among professional contractors and anyone who resists providing it is signalling that they prefer to keep their pricing opaque.

The lowest bid is almost never the right choice. Contractors who dramatically underbid are either inexperienced, desperate, or planning to recover their margin through change orders once you are committed to the project. A bid that is twenty-five percent below the next closest is not a bargain — it is a warning sign. The right choice is usually the mid-range bid from a contractor whose communication, references, and work quality you have personally verified.
""",

    "kitchen-lighting-design.md": """---
title: "Designing Kitchen Lighting That Actually Works"
slug: kitchen-lighting-design
url: https://yourblog.com/blogs/kitchen-lighting-design
tags: [kitchen, lighting, design]
anchor_phrases:
  - "designing kitchen lighting"
  - "kitchen lighting design"
  - "modern kitchen lighting design"
  - "plan kitchen lighting"
---

## Why Most Kitchens Are Badly Lit

Walk into the average residential kitchen and you will find a single central fixture in the middle of the ceiling, perhaps a row of recessed cans on a switch with no dimmer, and under-cabinet lighting that either does not exist or was added as an afterthought. This is not lighting design — it is the absence of lighting design. The result is a kitchen that is too dark where you are actually working, too bright where you are not, and completely inflexible for different times of day or different activities.

Good kitchen lighting design starts from how the space is actually used. Cooking, entertaining, cleaning up after dinner, and just walking through the kitchen in the middle of the night all require different lighting conditions. A properly designed kitchen has separate circuits for different zones, dimmers on every circuit, and fixtures chosen for their function rather than just their appearance. This sounds expensive and complicated, but most of the complication is in the planning — the actual installation is not meaningfully harder than bad lighting.

The reason so many renovated kitchens end up with mediocre lighting is that lighting design is typically left until late in the project, when the budget is already stretched and decisions have to be made quickly. Lighting is also one of the few areas where a good electrician cannot save a bad plan. If the circuits are not where they need to be before the drywall goes up, adding them later means cutting open finished walls. The time to plan kitchen lighting is before demolition, not after.

## The Three Layers Every Kitchen Needs

Professional lighting designers talk about three layers of illumination: ambient, task, and accent. A well-lit kitchen has all three, controlled independently, with the ability to use them in combination or separately depending on what you are doing. Skipping any of the three produces a kitchen that is functional at best and frustrating at worst.

Ambient lighting is the overall wash of light that makes the space usable. In a kitchen this is typically achieved through recessed ceiling fixtures on a dimmer, spaced evenly across the ceiling rather than clustered in the centre. The quantity depends on ceiling height and the reflectivity of your surfaces. A rough rule is one four-inch recessed LED fixture per twenty-five square feet of floor space, but this is a starting point for discussion with your electrician, not a final specification.

Task lighting is what actually lets you see what you are doing on the counter. This means under-cabinet LED strips at every stretch of counter, hung close to the front edge of the upper cabinet rather than buried at the back where shadows form. It also means dedicated lighting over the cooktop and the sink — the two places where people spend the most time working with their hands. Undercounter lighting is one of the most noticeable upgrades in a renovation and is absurdly cheap relative to its impact.

Accent lighting is the layer most people skip, and it is what makes a kitchen feel designed rather than just lit. Pendant lights over an island or peninsula serve an ambient function but also create a visual focal point. Toe-kick lighting at the base of cabinets turns on with motion and provides gentle illumination for night-time passage. Interior cabinet lighting makes your glassware and dishware visible through glass-fronted doors. None of these are strictly necessary, but together they transform a kitchen from a utility space into a room you want to spend time in.

## Working With Your Contractor on Lighting

Lighting is an area where the quality of your contractor shows up immediately. A mediocre contractor will install whatever the electrician thinks is easiest. A good contractor will pull you into the planning conversation, walk through your daily use of the kitchen with you, and coordinate the electrician and the cabinet installer to make sure the rough-in matches the cabinet layout exactly. How to choose a renovation contractor is a separate topic, but the lighting plan is one of the best tests of whether your contractor is actually engaged with the design or just executing a checklist.

Budget for lighting as a distinct line item in your renovation. Most homeowners underbudget dramatically for this because they see the cost of fixtures and forget the cost of the electrical work behind them. Recessed cans, under-cabinet LEDs, pendants, and the associated dimmer switches add up surprisingly fast — five to eight thousand dollars is typical for a well-designed kitchen lighting plan in a mid-range renovation. When you are thinking about how much does a kitchen renovation cost overall, this is a meaningful component that deserves its own consideration rather than being absorbed into a vague electrical allowance.

Dimmers on every circuit are not optional. A kitchen without dimmers is stuck at either "too bright for dinner" or "too dark for cooking," with no middle ground. Modern LED-compatible dimmers are inexpensive and reliable, and retrofitting them after the fact is straightforward if they were not included originally. But planning them in from the start costs almost nothing extra and is one of the easiest ways to dramatically improve the daily experience of the space.

## Fixtures That Age Well

Lighting fixtures date a kitchen faster than almost any other element. The ornate wrought-iron pendants that were ubiquitous fifteen years ago now look immediately dated, and the blown-glass globes that replaced them are heading in the same direction. The safest choice for longevity is simple geometry, matte finishes, and restrained scale. Drama in lighting is almost always a mistake in a kitchen that you plan to keep for a decade or more.

The correlated colour temperature of your bulbs matters more than most homeowners realise. Warm white, around 2700 to 3000 Kelvin, is appropriate for residential kitchens and produces light that flatters both food and people. The cooler 4000K and 5000K bulbs you see in commercial kitchens make food look sterile and make skin tones look unhealthy. Specify the colour temperature explicitly in your lighting plan — do not leave it to whoever buys the bulbs.

Quality of light also depends on the colour rendering index of the bulbs, which measures how accurately they reproduce the true colour of objects. Cheap LEDs often have a CRI of 80 or below, which makes tomatoes look washed out and the subtle colours of your countertop look flat. Bulbs with a CRI of 90 or higher cost slightly more but produce noticeably richer and more natural light. In a kitchen, where you are looking at food and cooking surfaces constantly, the difference is genuinely worth the few extra dollars per fixture.
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