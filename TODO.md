# TODO — sortilege-vtt-l5r5e

Open work, newest concerns first. `PLAN.md` holds what landed and why; this file holds what is
known and not yet done.

## Advancement (the player's Advancement page) — make it a proper advancement screen

The first version (PLAN I16) buys ring and skill ranks at the book's costs (Table 2–2, core
p. 97, read from the corpus), adds a technique by name at 3 XP or a stepped cost, and on Save
archives the character as a version and makes the advanced one current. It is a ledger with
steppers, not yet an advancement screen. To improve:

- **School rank and curriculum.** Show the character's school and current rank, and its
  curriculum for that rank. Mark each purchase in or out of curriculum, count XP toward the next
  rank — in full in curriculum, half (rounded up) out of it and for every ring, per the corpus's
  `out_of_curriculum_half_xp_rounded_up` — and show the rank-up when it comes (the school
  ability's new value, a Dragon tattoo, the mastery ability at rank 6).
- **Restrictions, enforced.** Skills cap at 5 (done). Rings: the corpus line reads *"Cannot
  increase a ring to a value greater than lowest ring + Void Ring. Maximum 5."* — check it against
  the book's page before enforcing it; only the cap of 5 is enforced now. Techniques: the categories
  the school may learn, prerequisites, and the curriculum's privileged access (`=`), per the
  corpus's `technique_restrictions` and `restrictions_and_prerequisites`.
- **A real technique picker.** Today it is a type-ahead over every technique in every book. It
  should offer what this character may learn — by category, rank and curriculum — with each
  technique's text on tap (as the Play tab's cards do) and its own XP cost where it lists one
  ("3 XP, or other listed value"), not a stepper the player sets.
- **A review before Save.** What changes, before → after, and what follows from it: Endurance,
  Composure, Focus, Vigilance and the Void point maximum when a ring moves; the skill a technique's
  check uses.
- **The version's name.** Saved as *Before advancement*; let the player name it (*After Session
  Seven*), defaulting to that.
- **Layout.** A long skill name (*Composition*, *Martial Arts [Melee]*) wraps and pushes its
  stepper out of line; fix the row grid. Collapse the skill groups, and keep Earned / Spent /
  Available in view while scrolling (a bar at the bottom).
- **Owner's calls, not yet made:**
  - Who awards XP: today the player may raise *Earned* on the page. Should an award be the GM's
    (an op the GM sends, the player only spends)?
  - Should the GM approve an advancement before it becomes current, or only see it (it is logged
    and archived now)?
  - Advantages, disadvantages and titles gained in play — on this page, or elsewhere?
