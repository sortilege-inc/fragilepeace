# Correcting the chronicle against the session recordings

Started 2026-09-12. Ground truth is `archive/transcriptions/`, not the Archivist
export: the Archivist compressed and in places inverted what happened, and the
voice rewrite then polished the inversion.

Gates for every session, run from this folder:

```bash
python3 scripts/build_site.py && python3 scripts/factguard.py \
  && python3 scripts/voicecheck.py && python3 scripts/verify_site.py
```

`acceptcheck.py` is part of the run:

```bash
python3 scripts/acceptcheck.py
```

Every deliberate removal goes in the accept table with a reason. Since
2026-09-14 that table is **`sources/factguard-accept.json` in the site repo**,
not a literal in `factguard.py`, so the reasons have git history. This log lives
at the site repo root beside `REWRITE.md`.

## Progress

| Sessions | State |
|---|---|
| 1 | No recording. Untouched. |
| 2, 3, 4, 5 | Done — commit `0dd17ce` |
| 6 | Done — commit `567f94d` |
| 7 | Done — commit `279274f` |
| 8 | Done — commit `2003862` |
| 9, 10 | Done |
| 11 | Done — commit `ef3895a` |
| 12 | Done — commit `be56900` |
| 13 | Done — commit `ddcdfbe` |
| 14 | Done — commit `c142205` |
| 15 | Done — commit `fc1215d` |
| 16 | Done — commit `6c9f0b5` |
| 17 | Done — commit `622a0d1`, PARTIAL RECORDING (last 20 min only) |
| 18 | Done — commit `bb09ef5` |
| 19 | Done — commit `33f9f59` |
| 20 | Done — commit `85a5222` |
| 21 | Done — commit `23615c3` |
| 22 | Done — commit `036628c` |
| 23 | Done — commit `04fbfdd` |
| 24 | Done — commit `20d2021` |
| 25 | Done — commit `dd636b5` |
| 26 | Done — commit `caad563` |
| 27 | Done — commits `5a983a4`, `854c8bc` |
| 28 | Done — commit `ffedd42` |
| 29 | Done — commit `64e5a63` |
| 30 | Done — commit `0e09d06` |
| 31 | Done — commit `125ca3e` |
| 32 | Done — commit `f289c8a` |
| 33 | Done — commit `7fa1096` |
| 34 | Done — commit `d40895d` |
| 35 | Done — commit `5bed223` |
| 36 | Done — commit `50ec033` |
| 37 | Done — **every session with a recording is now corrected** |
| 41 → 55 | Hand-authored from these same sources; lower priority |

**No recording exists for sessions 1, 3, 38, 39 and 40.** 3 was corrected from
session 4's opening recap; 38–40 have nothing.

## Resolved

- **Kitsu Yue** (owner, 2026-09-13, reversing the 2026-08-12 call). One person,
  filed by the export under three names. `Katsuki Yui` and `Kitsu Yui` now
  correct to `Kitsu Yue` in `archivist.CORRECTIONS`, the pinned alias in
  `ALIASES` flipped to match, and the two export pages merged into one
  `kitsu-yue.html` carrying s8 → s26. The export backed the call: 106 "Kitsu
  Yue" against 36 "Kitsu Yui" and 14 "Katsuki Yui" — the old rule had been
  rewriting the majority spelling into the minority one.

- **Two factguard defects, fixed 2026-09-13.** (1) `f_names` derived its
  "ordinary English" vocabulary from each text separately, so a rewrite that
  happened to use a word in lower case had its sentence-initial capital
  discounted while the original's was counted — reporting a loss for a word
  sitting in both texts. `compare()` now passes the union of both vocabularies.
  (2) `f_quotes` fingerprints each italic run, so merging two adjacent runs into
  one changed the fingerprints without losing a word; a fingerprint whose words
  all survive inside a longer new run is now absorbed. Splitting a run still
  reports, deliberately. Four accepted entries that existed only because of (1)
  and (2) were removed. Regression-tested: reworded quotes, deleted quotes and
  dropped names all still fail.

### Session 11 — what the record had wrong

The Archivist had collapsed three characters into one. **Bayushi Monban** was
given Ikoma Akuyaku's approach to the Unicorn camp *and* Matsu Morozane's
challenge, cat and clash. The pre-pass rewrite had already split Monban back
out; what it had not caught was that the underlying account was also inverted
and over-read:

- **The challenge ran the other way.** A Unicorn officer rode out, danced on his
  saddle, and called *Morozane* the cowardly dog. The record had Morozane
  issuing it.
- **Akuyaku never reached the camp.** The battle goes in at noon. He moved one
  range band, hugging the ridge and a paddy lip, and was still crossing when the
  session ended. The record had him inside the camp, in the dark, unseen —
  and had the Setsuna section build an argument on top of that.
- **The firebombs were a Lightning Raid** — the same fire-ring shūji Morozane
  had used a round earlier, turned around. The record read it as "a prepared
  position spending prepared weapons." Kitsu Somalia asked at the table whether
  the man was a shugenja at all and the GM did not answer; the corrected record
  leaves the question open, because it is open.
- **Round one and round two were merged.** Somalia's three panic was Morozane's
  Lightning Raid; the Touchstone of Courage was round two, and was a response to
  the fire on the other flank, not a consolidation of ground he had taken.
- **Nobody won anything.** The clash is unfinished, the strategic objective went
  unmet, and neither centre engaged. Which is the load-bearing fact for the
  mines case: the Lion fought at least one day of the Snow Plain blind.

`sources/entities/Unicorn Officer.md` is now a local page and the export entry
is in `SUPERSEDED_BY_LOCAL` — the export identified the challenger as General
Shinjo Kamo, which is an identification a later account supplies and the field
did not.

### Session 12 — what the record had wrong

- **Matsumura Zane is not a person.** The transcription mishears "Matsu
  Morozane" and the Archivist built a **second PC page** out of it — 41 mentions
  against 310. The recording settles it in the general's own mouth. Merged in
  `archivist.CORRECTIONS`; PC count 10 → 9.
- **The record skipped the day's result.** Morozane *lost* the clash — first
  move bought with bid strife, both scimitars through his guard, a blade at his
  throat and an offer of quarter he refused — and with it the **Unicorn**
  completed "test their mettle" and the Lion did not. He escaped capture only
  because both armies broke ranks to drag their commanders clear. None of this
  was in the record, which opened with the Unicorn withdrawal.
- **The mines claim was invented.** The record asserted the Old Diamond Mines
  sit on the forested hill Akuyaku climbed, that the battle was fought below
  them, that neither army knew, and that the Scorpion did — and built the entire
  Setsuna section on it, down to what Shoshuro Aishi can and cannot say in
  court. **The mines are not mentioned once in the s10, s11 or s12 recordings.**
  That geography is first established in s13 and after. Removed.
- **A whole scene was missing:** Toronoko's Righteous Example breaking the
  pincer, Somalia's Wall of Fire down the Unicorn line, the parley readings of
  Shinjo Kamo, and Morozane forfeiting ten honour and ten glory to enrage the
  Unicorn general's horse and then whinny at the man.

### Session 13 — what the record had wrong

- **Akuyaku's injury is permanent and the record softened it.** He kept the
  feet; he took **permanent nerve damage**. He can feel his toes and they do not
  move, and a knife along the sole gets nothing. His speed is gone and the medic
  said he may not be fit for the field and certainly not as a scout — which is
  the only thing he is for. The record had "he got some feeling into it" and a
  confinement order.
- **Toronoko's treatment failed.** Her sage-and-cayenne paste was a medicine
  *fire* check at TN3 and it missed. What saved the foot was four people:
  Somalia's Path to Inner Peace for the pain, Toronoko's triage direction
  dropping the medics' TN by two, Kayamayako calling for gentle fire rather than
  destructive, and Somalia holding Extinguish over the flame while they turned
  the foot above it. The record credited Kayamayako with the rewarming; she is
  not a shugenja and says so.
- **The Frozen River count was a mechanics misread.** "One of them died in it and
  four more went into the water" — the four is **panic**, not men. One casualty,
  four panic, and a couple pulled out who froze and were left.
- **Toronoko's first volley did nothing.** The arrows clattered off the
  fortification and the Unicorn jeered; she needed more than seven damage to get
  through it. The volley pinned the enemy leader and that is all. The attrition
  and panic came on her *second* action, Righteous Example at range.
- **Somalia commanded samurai archers**, not ashigaru — she left her shugenja
  behind for speed. Morozane took the mountain-born ashigaru spearmen. And her
  sword charge was worth two casualties, not "real damage".
- **The record understated the beating.** Three Unicorn cohorts plus a fourth
  commander's fire attack cut Morozane's unit in half. His Touchstone of Courage
  **failed**; he spent opportunities to shed two panic and walked to the front
  himself. The Lightning Raid landed only because he is Famously Lucky and the
  dice had to be thrown twice.
- **Kagekatsu's grievance is a family one**, and new: *"You will pay for the
  shame that our family suffered at your hands. Your comeuppance is coming."*

**The two findings that matter for the case.** First, the mines: the Lion were
*not* ignorant that there were old workings in that country — their maps said so
and the old mine paths are why the route was thought crossable. What was not on
the army's topographical information was the particular disused path Morozane
found and the workings at the end of it, with the snow walked and then covered
and at least one adit entered. The distinction is the whole point, and the
pre-pass s12 had flattened it into "neither army knew".

Second, **the ambush was betrayed**. Morozane proposed the mountain flank out
loud in a council held the morning after an intruder was caught at Sakura's tent
and got away without showing a face; the Unicorn were waiting in the trees at the
bottom of that mountain with matched numbers. The GM says it outright at the
table. s15's "somebody who knew the flanking plan before it was run" starts here.

### Session 14 — what the record had wrong

- **Morozane declined a challenge and hid it.** The officer who beat him in the
  clash rode out and demanded he finish it. He did not accept — declining costs
  seven glory — and instead set his lion on the man's unfamiliar horse while
  behaving as though he had not heard a word. *"I am sorry, I cannot hear you
  over the sound of my lion mauling your face."* The GM noted he may need a
  Skulduggery check if anyone asks. The record had him "playing stupid until the
  officer was close enough", which reads as a tactic rather than a dodge.
- **The record killed Utaku Mangiano twice, by two different hands.** It had
  Kagekatsu's flank putting him on the ground *and* Kitsu Yue finishing him in a
  duel. It was Yue, in a single exchange, after the man strifed out — and he was
  knocked down, not killed.
- **The duel was aimed at Somalia, not Morozane**, by a bushi who did not know he
  was challenging a shugenja.
- **Kitsu Yue asked in two voices.** *"Is it her past self talking or her future
  self?" — "You hear both."* Somalia heard the woman at her elbow and the
  descendant behind her eyes at once. The record had none of this, and it is the
  session's most important line for the s9 Kitsu Taigen thread.
- **Morozane's fall was his own challenge, accepted and lost.** The shugenja rode
  out with a blazing sword in each hand — *"Do you dare fight the kami's
  chosen?"* — Morozane went for a heart-piercing strike, missed, was compromised,
  and took a finishing blow. Somalia's Extinguish failed; a Hail Mary Path to
  Inner Peace needed four successes and gave five. Then she could clear only one
  of burning and bleeding, and took the fire.
- **The three dead leaders were the counter-flank's**, not the Unicorn army's.
  The record read it as the whole enemy command.
- **The avalanche.** The GM took the idea from Toronoko's player, and at the
  table it was discussed as something the water kami might be petitioned for by a
  Kitsu standing on unsettled snow full of explosions. No roll was made. The
  record now says the idea was in the air and declines to settle whether the kami
  were asked or simply obliged.

Also added: a `Unicorn Officer` ledger bullet, so his page now runs s11 → s12 →
s14 as one thread instead of stopping at the clash.

### Session 15 — what the record had wrong

- **A fabricated quote.** *"I will stake my horse against your honour"* is a line
  Matsu Morozane never says. The Archivist misheard the table: he is on **foot**,
  and what he does is *"stake the horse as it comes at me and have the horse rear
  up"* — he puts his yari into the charging animal. The record then built "went
  off his horse onto a stake" on the same mishearing. Both gone.
- **The village and the hill were swapped.** The record sent "Kagekatsu to the
  village, Morozane and the rest to hold the Central Hill", then narrated
  Morozane fighting at the rice paddies — internally contradictory. Morozane went
  to the **village**; Somalia held the **hill**.
- **The Lion lost the village outright.** The record ends mid-battle. The enemy
  sprang from every corner, took eighteen attrition off the Lion in one blow,
  seized victory, and Morozane deliberately *failed* his Touchstone of Courage to
  take the opportunities and buy an orderly withdrawal. No village, massive
  casualties, and Kagekatsu left on the field with a severity-12 critical injury.
- **Toronoko killed one of the Five Pillars, by name.** Shinjo Gansari — a duel
  she won with a Flowing Water Strike and then a finishing blow at twice
  deadliness. The record had "a Unicorn field leader". He now has a page. (s16
  already carries the Five Pillars kill; s15 is where it happened.)
- **The dead scouts are Morozane's own detachment from s13** — the men he cut out
  of his strength to look at the workings. The record did not connect them.
- Somalia fought the hill as a shugenja, handing her cohort to Kitsu Yue: Fires
  From Within into two outriders at once, then a Wall of Fire splitting the line
  for three rounds. None of that was in the record.

**The causal chain the record missed entirely.** Two Akodo nearly came to blows
that morning; Matsu Sakura sent **Akodo Toronoko** to the far side of the camp to
cool off; and the war council then approved the village raid with nobody of equal
weight in the room to argue against Kagekatsu. The GM says it outright: *"in the
absence of Toronoko to provide a counterpoint to Kagekatsu, it seems he's
convinced the general."* Kitsu Yue argued against splitting the army and was
shouted down. A family feud decided the battle.

### Session 16 — what the record had wrong

- **Kitsu Yue called the ancestors, not Kitsu Somalia, and she did not mean to.**
  The record had Somalia calling them and being told to "take up what was hers".
  What the recording has is Yue praying *"to live to a good death"* while
  surrounded by Unicorn spears — and armoured Lion ancestors crossing the field
  and cutting into everything in their path, Yue unable to hold them or herself,
  a spear putting her down. Afterwards, at the shrine, terrified: *"I prayed to
  the ancestors to live to a good death. I didn't pray that they would come and
  fight to the death. What happened?"* Somalia is the one who explains it to her,
  and the ancestors say *"we have never been called like this before… something
  about her."* The whole army starts whispering she is a foreign sorcerer.
- **The Lion had already lost the Central Hill**, in the night, along with a
  cavalry strike onto Sakura's own position. None of that was in the record.
- **Ikoma Hideri cracked the talisman problem** — she noticed the calm on the
  Unicorn troops and remembered Iuchi Gero wearing talismans at the parley. That
  observation set the day's objective. The record credited nobody. Third time the
  historian supplies the load-bearing fact.
- **Iuchi Gero is she/her and one of the Five Pillars.** The record used they/them
  and did not know her rank.
- **Morozane killed her on the ground.** He was offered the choice — let her rise
  and fight honourably, or finish her where she lay — and took the second, for
  **ten honour**, which puts him at twenty. Two days after pretending not to hear
  a challenge. The record had none of it.
- **He failed to retake Crystal Pass.** The record said he "peeled off toward the
  pass" and stopped there. The Unicorn were dug in with their spears turned
  around, and the session ends with the supply line cut and one day of food.
- Also missing: Kagekatsu is **Toronoko's cousin**, with a blade through one lung;
  Hisoka read the Unicorn line of march and called the Crystal Pass move; Morozane
  proposed a feigned collapse out of *Akodo's Leadership* and Hisoka refused it;
  and Sakura's own tally — three of the five great commanders killed or crippled.

Continuity fix back into s15: **Takun Norio was one of the Five Pillars.** Sakura
counts his head in the morning tally, which s15 could not know and s16 settles.

### Session 17 — a partial recording, and a misgendering

**`2025-07-21 Fragile Peace.mp3.docx` is only 21 minutes long.** It starts with
the banner already being reached for. The night after Crystal Pass was lost, the
commune with the bound spirit that s16 promised for "next time", and most of the
day's fighting are simply absent — and the Archivist's own s17 recap is derived
from the same 21 minutes, almost sentence for sentence, so there is no second
source. The file now opens with a `!note` saying so, and the Setsuna section ends
on what she does not have rather than papering over it.

- **Kitsu Somalia is she/her, and s17 was the last file calling her "he".** Every
  other corrected session has her right; s17 had inherited the export's male
  default. The recording settles it twice — *"after she came surfing in on a snow
  wave"* and the GM's closing *"Miss Somalia is the only one who knows who the
  actual spy is."*
- **Morozane did not ride in on the lion.** He came off his *own* horse. The lion
  menaced Kamo's mount, his soldiers ringed it with spear points and lobbed
  something log-sized at the rider, and he took the reins and hauled. A command
  check in water stance at difficulty 3, with skilled assistance from his troops.
- **"The cold ground broke the general's fall"** was invented. The GM has Kamo
  *"hitting the snow like a heavy sack of potatoes and with a fair amount of
  grumbling."*
- **The fire arrows were the Unicorn's opening salvo**, just before dawn — the GM
  calls it "a very nasty reveille" — not a later attack that "went nowhere".
- Taking the banner **was the general's explicit order and the strategic
  objective**, and it came close to routing the Unicorn outright: their panic was
  already past what their discipline could hold.
- The old Setsuna section asked who held the hill "in 1123-minus-two-hundred".
  The year is right; the arithmetic contradicts every other statement in the
  corpus, which puts the battle three *hundred* years back.

### Session 18 — what the record had wrong

The flashback ends and the party reads the archive. The old record got the
conclusion backwards.

- **The accounts are genuine.** The record implied a revision; the recording has
  the GM state the opposite — the copies are high-fidelity, Sakura in her own
  sharp crisp diction, Morozane in his blunt one, nothing added, *"everything
  you're reading is consistent with what you experienced, except that they are
  consistently omitting examples of how the Scorpion were interfering."* Nobody
  edited the history of the Snow Plain. Everyone who could have written the
  Scorpion down separately decided not to, because *"we would have won if we had
  not been sabotaged"* reads as whining from a clan that lives on its histories.
- **Kitsu Somalia is not "missing" from the archive.** She left a great deal —
  and wrote a career's worth of scholarship on the ancestor-summoning technique
  *without ever naming its source*. The clan credits her as the first to
  demonstrate it and as a founder of the school. The party ask it out loud: *"Why
  would Somalia be credited with it if Yue found it first?"* This is the
  foundation of the s21 "restore the honour of Kitsu Yue" thread.
- **Matsu Sakura omits Ikoma Hideri and Kitsu Yue** — not "the medic", as the
  record had it. Her whole account of the battle is one line about the winter.
- **Toronoko's record defends Ikoma Akuyaku to her dying day** against the charge
  that he caused the supply disaster. He was the historical suspect, she was his
  only defender, and she is the only person in the archive who mentions him at
  all. None of that was in the record.
- **The hand changes.** The record said her "writing changes markedly". The
  finding is sharper: everything before the Snow Plain is in her own hand, and
  the battle and everything after are in someone else's.
- **Kitsu Yue's poem has three lines** and the record had swallowed the middle one
  under an ellipsis — *"The sting is in the words the children learn"*, which is
  the line the table spent ten minutes on and which Kazumi goes hunting through
  the Lion poetry cross-index for.
- **The treaty.** Midori finds it; Kitsuko Ayoko hands it to her. A certified copy
  of the Imperial original at Otosan Uchi, carrying four chops — Miya Mimoka,
  Matsu Sakura, Shinjo Kamo and **Shoshuro Amane**, who had no standing to witness
  it. Entirely absent from the record.
- **Monban knows where Ikoma Hideri's lost history is** and means to ride for the
  Snow Plain to fetch it, and spends the session trying to buy time from the
  Scorpion agent inside the castle. The map defeats him: the Snow Plain is as far
  as Otosan Uchi, without the clan roads and with a war in between.
- **Setsuna's outburst.** The record had her "say something that landed as an
  insult". She told Kitsuko Ayoko to her face that she is not samurai and not of
  the right families — and discovered in the saying of it that she believes it.
  That is the session's finding about her, and it is now the close of her section.

One new `archivist.CORRECTIONS` entry: **Miyamimoka → Miya Mimoka**, the Imperial
herald whose chop is first on the treaty. Same missing-space defect as
"Shinjukamu"; seven occurrences, all one page.

### Session 19 — what the record had wrong

- **The confession is bigger than the record said.** Monban holds a page of
  Ikoma Akuyaku's journals to a candle and a second text comes up out of the
  paper — invisible ink, an old cipher, clean careful calligraphy unlike his
  public hand, on nearly every page, duplicating everything he ever sent the
  Scorpion across decades. And among dozens of writings, an unaltered account of
  the Snow Plain in which he takes responsibility for **the poisoning, the leaked
  intelligence, and delivering Ikoma Hideri's lost histories to the Scorpion.**
- **The conclusion inverts.** Without those three agents the Lion would have
  finished the battle before the Imperial heralds arrived, and it was the heralds
  who made it a Unicorn victory. If the Scorpion bargain was to secure that
  victory, they secured it — so **the Scorpion claim may simply be true.** The
  record had the evidence cutting only against them.
- **The whole party is one family.** The genealogy gives Toturi, Sakuon and
  Akihito as descendants of Akodo Toronoko; Toronoko and Akuyaku's second son
  married into the Scorpion (Monban, Kazumi) and their third into the Crane
  (Kazumi's Kakita line); and Setsuna is an indirect descendant of Matsu
  Morozane. The record had one clause about "dynastic lines".
- **Toronoko was blinded**, and Akuyaku wrote her records for her — which is the
  answer to s18's "different hand".
- **The hostile exchange was not with Akodo Atsushi.** It was the War College
  quartermaster, unnamed on the recording. And *"I don't think I've ever heard of
  a Scorpion keeping a diary"* is **Monban's own aside**, not the instructor's
  refusal. What the quartermaster actually says is better, and is now quoted.
- **Setsuna's tea with Shosuro Imako was worse than the record admitted.** Not "my
  recommendation would favour the Scorpion". She offered **not to draw a doubtful
  Scorpion chop to Kitsuki Kaage's attention**, and asked for her name to be
  carried to **Bayushi Kachiko**, Imako's patron and Imperial Advisor. That is a
  magistrate trading suppression of evidence for a patron's notice.
- **Monban went to the sparring ground** because his own ancestor turned out to be
  a Scorpion who fooled a whole clan for a lifetime — shouting about treachery and
  dishonoured ancestors — not "rather than keep arguing".
- Also recovered: the army is the **Blood of the Lioness**; Ikoma Ichigo is Ikoma
  Hideri's **descendant** and says so; Kitsu Takeko is Akodo Sakuon's cousin and
  Akihito is his son.

One `archivist.CORRECTIONS` entry: **Okoto Sakuon → Akodo Sakuon.** There is no
Okoto family; it is the transcription's Akodo. Takeko says "my cousin, Akodo
Sakuon" on this recording, and the export itself writes the correct form twice
against twenty of the mangled one. The old `ALIASES` entry pinned it the wrong way
round, making the error the page title — the same defect the owner ruled on for
Kitsu Yue. Also fixed three occurrences in the hand-authored
`character/harunobu.html`, which is committed HTML and not generated.

### Session 20 — what the record had wrong

- **Two forgeries, two Scorpion, two members of the party who did not tell each
  other.** The record had Monban taking "Soshi Yamako's other proposal". Yamako is
  *Kazumi's* forger, met at the Path of Splinters. The Unicorn–Scorpion agreement
  is negotiated by **Monban with Shosuro Imako**, and that scene was missing —
  the handwriting sample (his chop alone will not do), the argument over who the
  forged deed should benefit, *"risk is part of the game, do you want to play or
  not"*, and her two asides about why *the least of the Bayushi* should inherit a
  diamond mine.
- **Imako's best line was absent.** *"If my lady the Imperial Advisor had need of
  these mines, she would put a word in the Emperor's ear and there would be no
  dispute. Why do you think she is allowing others to resolve it?"*
- **The Kitsu Archives debate was a real argument about law** and the record had
  one sentence of it. Monban: a performed bargain must be paid. Setsuna: nobody
  has seen the agreement, Imperial law is porous, and she can cite the training
  case where their own class was handed one set of facts and told to rule it both
  ways. *"The law is what the Emperor says it is at the time."*
- **The Lion–Crane treaty is far worse than "favouring Lion territorial
  ambitions".** The Lion give up old claims and take **two-thirds of the Asari
  Plains**, bringing their border up against Suma. It was negotiated at the *Crane
  embassy* by a Lion boy sent to lose who won outright. The mediator rules against
  the Crane as a habit — and Setsuna is nine-tenths certain he was appointed to it
  by the **Imperial Advisor**, which is Bayushi Kachiko, to whom she asked her own
  name be carried one day earlier.
- **The Scorpion have not agreed to anything.** The record had Kazumi bringing
  back "the Scorpion's own price, the same clause from the other side". They
  answered that they were open to it and asked what else she had. Setsuna says out
  loud that she still needs an affirmative.
- Also restored: Kazumi recites the Snow Plain to Yamako through Toronoko's eyes,
  and she offers to write in Toronoko's hand with her *other* hand — the hard part
  being the deliberate sloppiness, "as though writing blindfold" — and suggests
  the forged confession would be more believable if it included suspicion of the
  husband. And Monban's shrine scene: an offering to Ikoma Akuyaku, the priest on
  why non-Lion ancestors are harder to reach, and the feast for Shosuro Amane.

One `archivist.CORRECTIONS` entry: **Shosuro Amaro → Shosuro Amane.** The export's
own Amaro page describes her as "an ancestor of the Scorpion Clan, renowned for
her role as an advisor to the Unicorn Clan" — Amane entire. 37 to 5.

### Session 21 — what the record had wrong

- **The Imperial-possession proposal is Kakita Kazumi's, not Shiba Midori's.**
  Midori reports the courtyard conversation: she, Kazumi and Kitsuko Ayoko talked,
  the three converged on restoring Kitsu Yue's honour, and *Kazumi* was the one
  taken with declaring the mines an Imperial possession. The record credited
  Midori, and the Setsuna section put it in bold.
- **The treaty is silent on who won.** Ichigo: the Emperor awarded the Snow Plain
  to the Unicorn and its income to the Lion for a term, and said nothing whatever
  about the battle — it acknowledged only that a dispute existed. That is the
  factual footing the whole Imperial route stands on and it was missing.
- **The Emperor quote was inverted.** *"If the Emperor wanted the diamond mines,
  he could have just taken them"* is **Monban's rebuttal against** the Imperial
  route — nobody has taken them, so dressing the award as the Empire's will is
  something the party is doing, not something the Empire asked for. The record
  had it as Monban arguing *for* Imperial control.
- **Monban lied to her and she let him.** *"I hear you had a visitor today." —
  "Nothing to concern yourself with. A misunderstanding."* She accepted it with a
  warning attached. That was a decision, not an oversight, and the record skipped
  it entirely.
- **The Scorpion had already said yes.** Setsuna's terms were accepted at the tea
  ceremony and she did not register it — the GM says so twice, and that the
  Scorpion in question is subtle enough never to have been caught at anything. She
  spent two days negotiating against a door that was already open. This also
  settles the s19/s20 open question about the missing affirmative.
- **The note quotes Monban's own words.** *"What is earned is owed, what is owed
  is paid"* is his line, said to Setsuna's face in the argument, and it comes back
  that night on top of the delivery: *"Your words. Remember them well. Earn that
  piece of paper."*
- Also restored: the Soshi's full threat (the traitor's grove, the docket, his
  word as a Bayushi, and that *he* will present it and account for how he came by
  it); Ichigo's limit on his own testimony (*"I am happy to testify to what is. I
  do not want to speculate on what is not"*); and that Ayoko was the one assigned
  to pull the Snow Plain documents for the magistrates before they arrived.

### Session 22 — what the record had wrong

- **Setsuna's case is a statute, not a plea.** The record had "both clans
  relinquish their claims". What she actually found and cited is an **Imperial
  edict on dormant strategic resources** — contested claim, ground unused above a
  century, the Emperor may take it, no special circumstance needed — and she has
  an eyewitness to the century in her own ancestor, who crossed that hill and
  found the workings already abandoned. None of it was in the record.
- **The party's testimony survives the spiritual bar, and that was argued.**
  Shosuro Aishi probed for it before the session — *"You wouldn't be happening to
  try to court spiritual help?"* — because the Kitsuki themselves barred spiritual
  witnesses. Kaage ruled the shared memory inadmissible but the magistrates' own
  sworn accounts admissible: *"that would not fall under the exclusion of
  spiritual entities. You are staking your own honour on the accounts."*
- **The forgery confrontation was in chambers, to all three, with Setsuna
  summoned only to watch.** Not a private aside to Monban. And Kaage's words are
  much worse than the record's summary: either they knew and presented lies to his
  court, or they failed to detect them, *"which would speak to a lack of
  competence in individuals I trained… I am saving you the embarrassment."*
- **Midori's answer was to tell him the truth** — *"Kaage-sensei, it will shock
  you that the truth is even stranger than that"* — and then withdraw her own
  evidence. Kazumi staked five honour on his instead. The record had her winning a
  concession and then withdrawing testimony; it was evidence, and the contrast
  with Kazumi is the point.
- **Kaage taught Monban to find invisible ink.** *"A Scorpion — or somebody I
  trained how to detect invisible ink."*
- **Ide Tsubame's case was absent.** Every party conceded the land by its own
  chop; the Lion produce rights were a term-limited gift that expired; the
  Scorpion showed no interest for three centuries. She is arguing her first case
  of this kind against an advocate with three or four such wins behind her.
- Also: the mines are **derelict**, and nobody can say why the Scorpion want them;
  Kaage arrived expecting one magistrate and found four; and Kitsuko Ayoko walked
  in with unvetted evidence of her own, on behalf of the ancestor whose work
  Midori's ancestor was credited with.

### Ide Subane → Ide Tsubame — a spelling call I made, reversible

The export writes **Subane 149 times against 4 correct**, but every transcription
says **Tsubame**, 8 times out of 8, including from the guest player who voices her
on this recording — and Tsubame is a word (a swallow) where Subane is not. Same
dropped-consonant defect as "Okoto" for "Akodo". One `CORRECTIONS` line plus a
source sweep; say the word and I will put it back.

### The Emperor's export page is corrupt — left alone deliberately

His page is titled **"Emperor Hantei Hantei Hantei Hantei"** (5 occurrences,
against 28 "Emperor Hantei Hantei" and 3 bare "Emperor Hantei"), which is the
transcription stuttering. I tried to collapse it and **reverted**: the export file
itself is malformed in a way a rename makes worse. Its body opens

    [[[[Emperor Hantei Hantei]] Hantei Hantei]] Hantei Hantei Hantei Hantei…

— nested brackets around a run of repeated words. Any regex that rewrites the long
form fires *inside* those nested links and multiplies them, and verify_site caught
it. This needs the export entry repaired, not a correction rule. The ALIASES now
carry a comment saying so.

### A third factguard defect, found and fixed

`f_quotes` truncates its fingerprint key to 120 characters so the report stays
readable. The absorption check added on 2026-09-13 was reading those **clipped**
keys, which meant it answered "no" for exactly the case absorption exists to
allow: a short quote expanded into a longer one, where the added words push the
original's last word past the cut. Fixed by giving `compare()` the untruncated
word sets through a new `quote_word_sets()` helper.

Regression-tested: an expanded quote is absorbed; a **reworded** quote still
fails; a **deleted** quote still fails.

### Kitsu Yui → Kitsu Yue moved to ACCEPT_ALL

The sources are being brought over to the owner's spelling file by file as the
pass reaches them, so the rename now has one `ACCEPT_ALL` entry instead of a
per-file one in every session.

### Soshi Aisha / Shosuro Imako / Soshi Imako — probably one woman, not merged

The s21 recording never names her; she is "the Soshi". The export carries `Soshi
Aisha` (62 mentions — a coquettish courtier who veils her face with a fan and
serves the Imperial Advisor), `Shosuro Imako` and `Soshi Imako`, and the fan, the
coquetry and the Kachiko connection describe the same woman Setsuna took tea with
in s19 and Monban bargained with in s20. Not merging until s22–s26 are in hand.

### Shosuro, not Shoshuro — owner's ruling 2026-09-13

The family is **Shosuro**. Ten source files had been writing "Shoshuro";
`archivist.CORRECTIONS` was already normalising it at read time, so no rendered
page ever said otherwise, and this is the sources catching up. Swept, and covered
by a single `factguard.ACCEPT_ALL` entry rather than ten per-file ones.

### Akodo Sakuon and "Akodo Osakuan" are probably one man — not merged yet

`sources/entities/Akodo Osakuan.md` (written from s49) says Osakuan is **Akodo
Toturi's right hand and Akodo Akihito's father**. This recording says **Akodo
Sakuon** is one of Toturi's principal generals and Akihito's father, and Takeko
calls him cousin. Same role, same relation to Toturi, same son. I have not merged
them because s49 is thirty sessions away and I have not heard that recording —
but I expect to, and the evidence is already one-sided. Flagging rather than
acting.

### Shiguro Chinmoku is she/her — RESOLVED

Owner's ruling, 2026-09-13: **the lion is female.** This matches Jordan's own
usage on the recordings — *"my pet lion who likes some horse flanks. She's at my
side"* (2025-06-30), *"my cat did very well… she got embroiled after the duel"*
(2025-06-02). The export's "his loyalty and ferocity" never reaches a page (an NPC
entry renders its session ledger, not the Archivist prose) but it had leaked into
the s11 rewrite. Fixed there, noted in `archivist.CORRECTIONS`, and her s11 ledger
bullet now says lioness so the site carries it.

### Ikoma Hideri is she/her — corrected out of pass order

The recordings say so four separate times, across four sessions: *"her muddy
scholar's robe"* and *"Madam Historian"* (2025-06-09); *"**Her** one failure was
that the Battle of the Snow Plains went completely unrecorded"* and *"I'm pretty
sure **she** put something in there"* (2025-08-25); *"my ancestor, Ikoma Haideri,
**her** record of the battle went missing. And Ikoma Haideri **herself** perished
shortly thereafter"* (2025-09-01); *"**Her** honor should also be restored"*
(2025-09-15).

The corpus had "the man", "his lost chronicle", "assassinated before he finished
it". That came from the export. Fixed in `s18` and `s25` now rather than waiting
for those sessions to come up in the pass — it is a live misgendering on a public
page and the evidence is not in dispute. factguard reports both files clean.

**Also found, not yet acted on:** Akodo Kayamayako is **she/her** on the
2025-06-09 recording (*"She informs you that she found a suspicious person…"*);
`s19` currently uses they/them. Not wrong, just less specific — fix it when s19
comes up.

### Shoshuro Amane's pronouns — open

The GM uses **they/them** for Amane consistently and never he or she: *"the
Scorpion speaks, introducing themselves as Shoshuro Amane. **They** have been
brought along to negotiate peace"* (s12), *"**They** are simply a witness"* and
*"here **they** are in the official record"* (s18). A player says "her chop" once
in s18; the export says "she". The corpus uses she/her throughout. Left as-is for
now because flipping it touches a dozen sessions and the evidence is weaker than
Hideri's — but it is worth a ruling.

## Session 23 — what the record had wrong

Recording `2025-09-29 Fragile Peace.mp3.docx`, 1278 normalised lines. The `-alt`
variant is byte-identical after normalisation — a punctuation difference in the
speaker tags, nothing more.

**Transcript quality caveat.** This file is materially worse than s10–s22. The GM
was running his Thursday *Expanse* game in the same call ("*My Thursday Expanse
game that I run last week got moved to tonight, and so I was running that*"), and
the two games are interleaved down to the sentence inside single speaker turns.
Roughly one line in fifteen is Expanse. The L5R content is coherent and internally
consistent and corroborates known facts, so it is usable — but attributions were
taken only where clearly attested, and anything ambiguous was left out rather than
guessed. Ambiguities parked below.

- **The forgery tell was wrong.** The record had Setsuna hearing "her own
  yojimbo's voice in the phrasing." The recording has two different tells, neither
  of which is Monban's speech rhythm: the document is *too wordy for Shinjo Kamo
  as he is described to be* and *too perfect* — "it says exactly what this person
  wants" — and the bequest clause names no recipient, leaving the mines to *the
  lowest of the Bayushi*. That phrase is a present-day spoken epithet for Monban
  that "nobody has ever written down," appearing in a 300-year-old instrument. It
  reads "like a prophecy," which is not how a deed reads.

- **She was not the only one who saw it.** Kaage "raised an eyebrow because he
  also knows what that means in the modern world," and Ide Tsubame said it out
  loud in open court. The record framed the insight as Setsuna's alone.

- **Two treaties were conflated.** The record had the secret treaty "carrying
  Shosuro Amane's chop." The secret treaty is in **Shinjo Kamo's own hand, sealed
  with his chop**. Amane's chop and signature are on the **official** treaty (White
  Shores Lake) **as a witness, not a participant** — a fact that helps the Scorpion.

- **Monban lied about provenance and that is the crux.** He told the court he found
  the treaty among Shinjo Kamo's letters held by the Lion military library, hidden
  in the shelves, and that he had returned all the others. The GM called it "that
  brazen lie" and rolled it against an unknown difficulty. Kaage demanded the
  library's own records of which of Kamo's letters it ever held and dispatched an
  assistant. The record had Kaage sending for records to *verify the treaty*, which
  understates it — he is checking whether the shelf ever held the thing.

- **Tsubame won the withholding; Kaage did not do it unprompted.** She objected on
  procedure before the treaty could be entered ("Your Honour, we have procedures
  for a reason"), barely made the check, and was compromised by it. Kaage then
  ruled the treaty must be authenticated before admission. The record gave Kaage
  the initiative and left Tsubame reacting.

- **Tsubame's outburst — the centrepiece — was absent.** Monban spent all three of
  his opportunities deliberately provoking her ("*your clan knows you owe us…
  you didn't keep track of your own agreement… we were there*"). She accused him of
  forging the letter to his face and itemised it: conveniently perfect, conveniently
  in Lion territory, in no Shinjo archive, unheard of by Unicorn or Lion, known only
  to the Scorpion; verbose where Kamo was plain — "*That is my ancestor. I know how
  he talks. I have his writings. This is not him.*" Then the cipher point: run the
  key and see whether it produces a perfect copy, and "*interesting that we haven't
  done that.*" Kaage cut her off — "*That is quite enough*" — and she lost the day's
  progress. The GM: "you said out loud what everyone was thinking."

- **She publicly credited Midori** in the middle of it: the third version is off the
  record because the magistrate who submitted it withdrew it herself rather than
  "sell a flat lie to an Imperial Magistrate."

- **The three diary versions, by presenter.** Kazumi's, in his general exhibits —
  least damning, Akuyaku refuses the Scorpion ("*the family I'm married into*").
  Monban's — full confession, enciphered. Midori's — a historian's plain-language
  commentary on an original found in a secret pocket sewn inside the binding, which
  she withheld. The GM labelled these A/B/C inconsistently across the session, so
  the record now describes them by presenter. Also established: **Akuyaku was born
  Scorpion and married into the Lion.**

- **Setsuna's motion was bigger than recorded.** Not just dismissal on three
  centuries' silence: "*a motion for summary dismissal with prejudice and a request
  for sanctions and compensatory relief*," built on technical definitions of
  strategic resource, abandonment, competition of claims, and Imperial eminent
  domain — and argued **arguendo**: presume every Scorpion claim true, and it
  follows they held the establishing evidence for centuries without pressing, so by
  Imperial law the claim is forfeit. Conceding the opponent's whole case and winning
  anyway is the part the record dropped.

- **Kaage tabled it on the merits, not pending authentication.** "*I have not heard
  sufficient reason to believe these claims are either unfounded, false, or
  frivolous yet. I am tabling your motion to dismiss on the merits until I have more
  evidence to that effect.*" He also asked for case law and she conceded she has it
  for components but not for this combination of facts. **Tsubame declined to
  assist** — assisting costs the Unicorn the mines for punitive damages.

- **Midori's silence had no stated motive.** The record invented one ("she had
  decided to speak in the morning, when the room was cooler"). Kaage invited her to
  speak, she asked to postpone, and she "quickly retires to her separate rooms and
  doesn't talk to anybody."

- **Isshin was resolved, not left hanging.** The record closed on "nobody has asked
  yet whose misconduct he meant." The session answers it: he **stands accused of
  murdering a Lion Clan samurai**, and Monban **asserted Imperial jurisdiction** to
  pull the case out of a Lion court into Emerald Magistrate hands, with a tribunal
  likely given how many magistrates are present. He also has a duel scheduled. Bound
  **without knots**, deliberately, "because that would imply your guilt."

- **The search of Monban's quarters, entirely absent.** Left alone for hours, Isshin
  drank the sake and searched: more than one family mon, emerald snowflakes on
  everything, sanctified brushes, a bottle of **invisible ink** (which he swapped for
  ordinary ink out of spite), a letter naming him heir to a property, and a crumpled
  letter from his lord — no stipend, he pocketed temple money, "*you are a thief as
  well as a pathetic liar and a disgrace to the clan,*" and assigned "*to the
  protection of an annoying bird*" to be kept alive if he ever hopes to return to
  favour. **Monban's yojimbo posting to Setsuna is a punishment detail**, confirmed
  by the GM out of character. Monban put his family blade to Isshin's neck, was lied
  to, and had him thrown in the deepest cell and kept awake all night.

- **Setsuna's night in the Lion library, absent.** She went after the weakest joint
  of her motion — the sanctions — and found a precedent where the Crane were made to
  pay damages over official communications with the Lion and told never to bring the
  like before Emerald Magistrates again. The Lion keep the case book on a pedestal
  carved with a hunter shooting a crane from behind a duck blind. She found a second
  case on timeliness of unpressed claims, and lost sleep for it. **The flaw the GM
  flagged:** her precedents concern *known* claims left unpressed, not *unknown*
  ones — the Scorpion's likely angle.

- **Otosan Uchi** — the transcript's "Odashan Ushi" is Otosan Uchi, confirmed
  against s08/s18 and the Miya Satoshi page.

### Session 23 ambiguities — not written into the record

- **Who Isshin's childhood pen pal is.** The recording establishes a pen-pal
  relationship formed on a boyhood trip to "the highest mountains in the **Phoenix**
  lands," which points to Shiba Midori, and Midori winks at him — "you're lucky
  you're getting the Shiba thing." But Monban separately addresses someone as "big
  sister" in the same stretch, and the Expanse dialogue is interleaved through all
  of it. Left out of the record rather than guessed; s24 should settle it.
- **"a letter informing him that he is the heir to a piece of property in
  Nyxlands"** — "Nyxlands" is not a corpus place and is almost certainly an ASR
  mangle. Recorded as "a letter naming him heir to a property," location omitted.
- **Whether Setsuna or Tsubame made the authentication objection.** Resolved to
  Tsubame on the chain of play — the objector becomes compromised, and the person
  Monban then provokes into an outburst is described as already compromised, and
  that person is unmistakably Tsubame. Flagged here because the speaker tags do not
  independently confirm it.

## Session 24 — what the record had wrong

Recording `2025-10-06 - Fragile Peace.docx`, 927 normalised lines. The `-fixed`
variant is byte-identical after normalisation. Clean recording — no bleed from the
GM's other game this week — but a large fraction of the runtime is out-of-character
Zoom/Discord troubleshooting, so the in-fiction content is denser than the line
count suggests.

- **The librarian's report is the payoff of s23 and the record inverted it.** The
  record had "letters authenticated as being in his own hand, and short of what the
  case needs." What the [[Head Librarian]] actually reported: four *second-hand*
  copies plus a few authenticated as Kamo's hand, **all predating the battle he
  died in**, being travel correspondence from the years of the return about lands
  beyond Rokugan — nothing touching the Snow Plain at all. And, decisively, **no
  record that Monban's secret treaty was ever in the collection**: "it certainly
  would have been something that would have stood out when we were looking to
  assemble documents on the Snow Plains. It would be quite a find if such a thing
  were there." Monban's sworn provenance is now contradicted by the library itself.

- **The hidden ink said something.** The record had Tsubame find a watermark and
  later go to the Commandant. The concealed message *is* the instruction: "speak to
  the Commandant of the Academy." That is why she goes.

- **Tsubame's exemplar motion was absent.** The single most consequential
  procedural act of the session: enter the authenticated Shinjo Kamo letters not as
  argument but as **handwriting exemplars**, so a disinterested outside expert can
  set them against the secret treaty — with the precedent for an outside expert
  ready. Kaage allowed it and named the problem: "where are you going to find an
  expert historian when every historian in this castle has probably already studied
  them ad nauseam in preparation for this case?"

- **Monban's outburst was absent entirely**, and it is the character beat of the
  session. A failed performance check, heard through the temple's paper walls by
  four people in the corridor, ending in the speech about what the Scorpion buy for
  everyone else — "We do what we must. We are the villain." Aishi was asked to back
  him and refused, thinking "why again did I choose to trust him." Kazumi brought
  him tea and told him to sit down. Kaage: "you will be seated and you will be
  silent, or you will be expelled from this hearing."

- **The corridor scene was richer than recorded.** Aishi was not conspiring, she was
  *annoyed* — no coordination, and she could have used the treaty far earlier.
  Monban's answer explains his whole method: he kept it from her to preserve her
  deniability, because "they watch me, I am the Scorpion that stands out." She asked
  for a signal next time he did something "arguably brilliant." She also answered
  the s23 forgery argument directly: calling a treaty too long and too precise only
  means the Unicorn have never read a Crane treaty or a Lion one.

- **The second letter is a refusal, not a courtesy.** The record had only "her
  husband is being treated honourably." The pair is: Harunobu's own letter (well,
  detained, injuries tended as the Lion tend their own, **the man who took him means
  to keep his horse**, and he overheard talk of an Emerald Magistrate pulling
  strings for him); and **Akodo Akihito's refusal** of Monban's request to have him
  released into Setsuna's household, on the ground that it looks like a hostage
  being arranged. Setsuna: "I cannot for the life of me tell if this is
  good-intentioned and inept, or ... Scorpion subterfuge I cannot fathom."

- **Akihito's letter, read into the record, was reduced to one clause.** The dream
  was of *another man's memories* — the battle, a Lion historian, and someone
  burying the work, the dream ending violently. The cache: the historian's complete
  unedited field record carrying **the historian's own chop and seal**; an unsigned
  draft treaty whose promised "assistance" is **never specified**; a skeleton in a
  shallow grave; and the sealed letter, **which he did not open**. His stated
  reasons for choosing Midori are in the record now because Kaage read them aloud —
  not Monban, not Kazumi ("he would gain the glory ... this is something I cannot
  allow"), not Setsuna ("I do not know this Doji Setsuna ... and in any case, they
  are a Crane"). And the reason under it: "this history was lost to treachery and
  betrayal. I know this on a personal level." **A second, smaller note for Midori
  alone was folded inside**; she steered Kaage off it and it remains unread.

- **Monban claimed the letter in open court, by name.** "That letter is addressed to
  me. Everyone here knows I am the least of the Bayushi. Even Akodo Akihito confirms
  it. I want my letter." Opposed courtesy rolls against Midori decided it; Tsubame
  refused to assist. Kaage: a letter three centuries in its envelope cannot be
  addressed to a living man — "unless we were there, which we were."

- **The letter's text was flattened.** Not merely "beg forgiveness or take the mines
  yourselves." It opens "I do not know you. I do not know why **our agent within the
  Lion Clan army** insisted upon you being the beneficiary" — independent
  confirmation of a Scorpion agent inside the Lion host. Then: grovel before Lord
  Bayushi, offer to end your life if the clan would be served ("it most likely will
  not"), and if you want the mines, "you will find a way to seize them for yourself.
  You will be facing myself and my heirs." Signed with nothing but a **stylised
  drawing of the Shosuro mon** — no seal, no name.

- **Monban's exit line was absent**: "I am the only person here who has protected
  the divine couple. The rest of you wish you had such an opportunity." He was
  instantly compromised, and left by going *over* the three Crab in the corridor.

- **The "no signatures and seals" quote is Kaage's, not the Head Librarian's.** The
  record put it in the librarian's mouth "from the bench." The expert testimony had
  been summoned but had not yet arrived; Kaage read the cache treaty himself.

- **Aishi moved to withdraw the case to diplomacy** after the letter landed, and was
  refused: "you are already at a higher court ... diplomatically resolving this was
  the step you should have attempted before you brought it to the Emerald
  Magistrates." Absent from the record.

- **Setsuna's two cases were unnamed.** *Shinjo v. Asawa* — Unicorn bridge-tax
  rights unasserted for three generations, constructive abandonment under the
  doctrine of latches, reverted to Imperial control; returned twenty years later as
  a **new grant, not recognition of the old claim**. *Daidoji v. Yokoto* — the Crane
  sanctioned for **vexatious litigation** despite formally correct procedure,
  damages to the Imperial Treasury and to the Lion. Her ask: mines to Imperial
  control, Scorpion sanctioned.

- **Kaage narrowed the case**, which the record does not show: "the original claim
  of the Unicorn to the Snow Plains is not in dispute. What is in dispute is whether
  there is legitimate cause to transfer ownership of those mines for services
  rendered as alleged."

- **Kazumi drugged the tea.** A laxative, not expected to be drunk; **Ide Tsubame
  and Shiba Midori both drank it**, and Tsubame had to leave the chamber, which
  handed Aishi an **unopposed floor** she used well. Aishi had asked for sake
  instead and Monban had refused the cup. Entirely absent from the record, and it
  changed the shape of the afternoon.

- **The pact is the opposite of what the record says.** The record called it "a pact
  of non-interference ... made in a form that costs the Scorpion something to break"
  and treated it as a clean win. What Setsuna actually offered: **if the Scorpion
  pledge non-interference in the Crane treaty, she throws her weight behind the
  Scorpion claim to the mines** — reversing, in private, the Imperial-forfeiture
  argument she had made in open court hours earlier, while sitting as an Emerald
  Magistrate. Aishi gave a preliminary yes she has no authority to give, choosing to
  beg forgiveness later. Written up with the Crane treaty-drafting ritual, ten
  honour staked each. The table named it: "this is technically corruption," "that is
  the kind of favour you would trade to corrupt an Emerald Magistrate," and
  "Monban is going to have the biggest whiplash ever."

- **Hida Kasudo's errand was wrong.** Not "to wait on Lady Kitsu": sent by his
  **uncle, who is his lord, to recruit men for the Wall**, and by his **mother** to
  look in on things. He and Nozomu and Kenji are **triplets** and he is the
  youngest. He heard the whole sealed-letter scene through a screen without seeing
  who spoke, and knows Monban as a friend of the Hida daimyō whom the Crab esteem.

- **Ikoma Ichigo is the dead historian's descendant** — which is why Midori went to
  him, guided by Kitsu Ayoko. The record had the conclusion without the reason.

### Kitsuko Ayoko → Kitsu Ayoko (16 files) — reversible

The transcriptions say **Kitsu Ayoko 27 times across 11 recordings**, against a
single "Kitsuko" (2025-04-28). Kitsu is a real Lion family and the canonical
ancestor-speaking bloodline, which is precisely her role; Kitsuko is not a family at
all. Shosuro Aishi says it out loud on this recording — "that is only the provenance
of the **Kitsu**" — and the Castle of the Swift Sword is the **seat of the Kitsu
family**. Same defect class as Okoto/Akodo and Subane/Tsubame. Applied as one
`CORRECTIONS` line plus a sweep of 16 source files and `notes/index.html`; delete
the line and re-run `build_site` to revert. **This one renames a PC, so it is a
larger call than the NPC fixes and wants the owner's confirmation.**

### Resolved by this session

- **Soshi Imako and Shosuro Aishi are two different people.** The 2025-10-06
  recording contains an explicit table correction — someone says "Soshi," someone
  else says "Soshi Imako isn't even here," and the answer is "not Soshi, Shosuro;
  Aishi is just behind a fan." That closes half of the open Aishi/Imako question.
- **"Least" vs "lowest" of the Bayushi.** The s23 table used both while working the
  culture check and s23 was written with "lowest." The sealed letter — the primary
  document — says **least** throughout, so s23 now leads with "least" and keeps "the
  lowest" as the variant the room also turned over.

### Session 24 open threads

- **The second note inside Akihito's letter**, addressed to Midori alone, was never
  read. Still live.
- **"The least of the Bayushi" is not a modern coinage after all** — a Shosuro used
  it three centuries ago. That weakens one leg of the s23 forgery reasoning and
  should be watched as the authentication comes back.

## Session 25 — what the record had wrong

Recording `2025-10-13 - Fragile Peace.mp3.docx`, 1005 normalised lines. Clean —
no bleed, single variant. The record was the most accurate of the pass so far
(the epigraph and the Setsuna lie were both right), but it flattened the two
findings that actually decide the case and inverted one attribution.

- **The seal finding is the ruling, and the record buried it.** Ikoma Ichigo:
  "All land transfers in Rokugan must be witnessed by a member of the Imperial
  House. This has no such seal upon it" — a worthless piece of paper until one
  does. Kaage then made it a holding: "One of these two documents is either
  authentic, or neither of them is. **But none of them are of a valid form of land
  transfer in and of themselves, for lacking the appropriate seal.**" That second
  sentence voids both instruments on their face regardless of forgery, and the
  record has none of it.

- **The ink.** Ichigo observed that the buried document is in worse condition than
  the one that spent three centuries in a library, which is backwards, and that one
  of the two reads as new ink on old parchment — "someone used old paper with new
  ink, whereas this other draft is at least the ink is as old as the paper it's
  on." He would not commit: "I just don't feel confident in saying these two
  documents are written at the same time." Recorded without forcing which document,
  because the recording does not settle it and Kaage's later ruling implies it was
  not settled.

- **Wrong attribution.** The record credits Ikoma Ichigo with confirming that no
  secret treaty is on file and that the letters vanished. Both are **the
  librarian's** testimony. Ichigo authenticated documents; he said nothing about
  the library's holdings.

- **The letters were returned.** The record says they "disappeared overnight" and
  the bullet says "Every one of them gone from the library overnight." They came
  back roughly two days later — **the entire collection, with nothing new among
  them, no secret treaty appearing**. That the collection returned intact is what
  makes Tsubame's argument work: the letters are not loot, they are exactly what a
  forger needs to copy Shinjo Kamo's hand, and then returns.

- **Tsubame failed, twice, and staked honour to do it.** The record has her "moving
  to call the librarian" and Kaage "warning her". These were two full discredit
  attempts — the first would have wiped eight momentum off the Scorpion — and she
  came up short on both, having staked five honour (Monban's status rank) on the
  accusation. She also failed a *truth burns through lies* attempt to catch
  Setsuna's alibi: "I know she's full of shit, but I can't prove it." To disprove
  it she would need to establish whether the letters ever reached Setsuna's hands,
  which the GM said is a more extensive investigation than she has time for.

- **Setsuna argued against her own case, and the record calls it "argued the
  principles rather than the documents."** Paying the s24 bargain, she told the
  court the Scorpion are owed their chance to press, on the ground that a strong
  reading of her own precedents would put every Unicorn holding at risk. Kaage
  destroyed it — the Unicorn never abandoned anything, the Lion held the land in
  keeping, the first Hantei guaranteed the claim — and then "looked at you oddly
  because you are basically undermining the same argument you made the day before."
  **She kept zero successes.**

- **Kazumi's denunciation was a discredit play, not a disclosure.** He structured it
  to leave Monban technically innocent — "I am not saying that Monban himself was
  the one to write the forgery; I would never accuse a fellow Emerald Magistrate of
  such a base action" — offered his own library notes as the comparison standard,
  **then turned his back to the bench and mouthed something at Monban that the court
  did not hear**, and stood smirking through the outburst it produced. His motion
  also asks that *no* ruling be made for the Unicorn either, on the ground that
  neither clan can be trusted. The motion was refused.

- **Monban's counters were absent and they are good.** On the missing seal: the
  transfer of land did not occur until now, so it needed no Imperial authorisation
  until now. On the sealed letter: the Shosuro do not rule the Scorpion, the Bayushi
  do, and lands given to the Scorpion go to the Champion. On timeliness: Toshi
  Ranbo has been contested for generations under more than one Emperor and the
  throne has respected it. And he reduced the librarian to admitting he witnessed
  nothing and could not rule out documents being hidden in his own stacks —
  "your testimony is pretty much hearsay."

- **Setsuna's interruptions, absent.** She put a hand on Monban's shoulder and was
  ignored; paid an honour to try to send him out of the room on an errand and was
  refused; then used her office on the whole room — "He may be a dumbass, but he is
  my yojimbo, and you will not speak ill of him." Her alibi cost another honour, ran
  as a *trick* at target number four, took assistance from aides who "will say
  whatever you tell them to", and she spent both opportunities to make it easier for
  **the next person** who defends Monban's name.

- **Kazumi drugged nobody this week but the callback landed** — he offered Midori
  tea and she declined: "I've got some of my own."

- **Ichigo's authentication scene, compressed in the record.** Four gold-trimmed
  scrolls with lion's-head heads; he wept reading them; identified Hideri's chop on
  sight; came back with library samples to an audible sigh from the bench and proved
  chop, hand and phrasing. "A stain upon our family's honour is lifted." Kaage:
  "I am grateful to finally have something that I can attest to whose provenance is
  clear."

- **Midori deliberately refused the knife-fight.** She applied her authenticated-
  cache argument to the Imperial ruling rather than to discrediting Monban, saying
  so explicitly: "I'm trying not to get into the minefield of having one magistrate
  against another in an evidence battle and accusing each other of falsifying
  evidence." It was the day's most productive argument; Kaage praised it from the
  bench. Momentum for the Imperial ruling went from 8 to 13.

- **Monban's recess, absent.** Meditating in the Garden Of Virtuous Contemplation on
  betrayal by his fellow magistrates, disappointed in Aishi for arriving with one
  piece of paper and **in the Soshi for having to be paid for her work** — which
  means Monban was also Soshi Yamako's customer, separately from Kazumi (s20). Two
  buyers, one forger, two documents with suspiciously similar terms.

- **Kaage's actual close.** "Whether Monban may or may not have acquired the
  documents from the library at an odd hour has no provenance whatsoever upon the
  validity of these documents. I am at this point not sustaining any further
  arguments regarding this treaty. It is highly likely that one of them is a
  forgery. However, the evidence chain is not sufficient to prove any one at this
  time." Nothing thrown out, nothing proved; it comes down to a third-party
  authenticator.

### Session 25 open threads

- **What Kazumi mouthed at Monban** is not recoverable from the audio — the
  transcript renders it twice, differently and incoherently. Recorded as "mouthed
  something the court did not hear" rather than guessed.
- **An old warrior-scholar with his hair in a topknot bun** was shown into the
  chamber mid-session and nobody in the party knows who he is.
- **A Scorpion "humble historian"** is sitting in the Ikoma Hall of Scribes. Midori
  noticed the Hida instead and marked *him* for investigation.
- **"Big sister."** Monban uses it again, of whoever presented the sealed letter —
  which is Midori, and which the owner has since confirmed is who he means
  throughout. See the s27 entry.

## Session 26 — what the record had wrong

Recording `2025-10-20 Fragile Peace.mp3.docx`, 616 normalised lines. Clean, single
variant, no bleed; a good deal of the runtime is a toddler and a violin practice,
so the in-fiction content is denser than the line count suggests.

- **The two spirits were misidentified, and it is the biggest single error of the
  pass.** The record has "[[Shosuro Aishi]] and [[Ikoma Akuyaku]]" walking into the
  arbitration, and builds a Setsuna paragraph on the living advocate sharing a name
  with the dead. What Monban actually says, introducing them, is: **"Blood of my
  mother, Shosuro Amane. Blood of my father, Ikoma Akuyaku."** The ancestor is
  AMANE, and **both of them are Bayushi Monban's own forebears**. He is the
  descendant of the Scorpion who witnessed the treaty *and* of the Lion scout who
  betrayed the Lion — which is why he rode Akuyaku through the flashback arc, and
  it reframes his ten-point argument as a man collecting on his own family.

  This also corrects a 2026-08 voice-pass note: that pass found two Shosuro Aishi
  ledger bullets in s26 and folded "the ancestor" into the living advocate's bullet.
  There never were two Aishi. That was recorded as a per-file accept reason;
  the reason was removed on 2026-09-14 as dead configuration — the token is
  accepted globally by the Shoshuro spelling ruling, so the per-file text was
  never consulted — and this paragraph is the record of it.

- **What the spirits actually did.** They looked at one another with open disgust,
  and Kitsu Takeko — who can make them seen but not heard except by shugenja —
  translated: Amane says Ikoma Akuyaku is "the most accomplished liar she has ever
  had the misfortune of working with" and that nothing he says should be believed;
  Akuyaku says she is only disappointed not to be as good an infiltrator as he is.
  Monban's entire documentary case rests on Akuyaku's journals, and his own ancestor
  impeached them unprompted. The record ends before this happens.

- **Shinjo Altansari is not a Snow Plain figure.** The record has the witnesses
  naming "Shinjo Altansari and Matsu Sakura" as the fixed points they check each
  other against. The recording says **Shinjo Kamo** and Matsu Sakura. Altansari is
  the present-day Unicorn Champion (s09).

- **Kitsu Yue is named, and she is the reason the histories are gone.** The record
  says only "her own ancestor." Ayoko names her, and says Yue felt she had won the
  battle by unfair means, and that **toward the end of the fighting she did
  something that caused the histories to be lost** — and sought a descendant to
  correct the record. The scroll that put the party into the vision **worked once**
  and has done nothing since.

- **Kaage's line.** Not "called it fanciful lore" — *"Are you sure you did not inhale
  some mushroom spores and have a strange vision?"*

- **Setsuna's best work was invisible and absent from the record.** She built the
  entire room for Kazumi's testimony — moved witnesses, closed interruptions,
  focused the chamber — on a courtesy/air check she passed with **seven successes**,
  concealing her hand completely and handing him **five bonus successes**. She also
  steadied a terrified Kitsu Ayoko into the session's clearest testimony on poise
  alone. Both absent.

- **Her cross-examination answer was better than recorded.** Asked how the Unicorn
  were waiting for the pincer if she saw no Scorpion, she conceded the gap and
  closed it in one move: *"If it had been the Scorpion, would it not have been done
  in a way so as not to implicate the Scorpion? That is my understanding of how
  ideal infiltrations work. But I can only speak to what was seen and heard through
  the eyes I was looking through."*

- **The record reversed Tsubame's argument.** It says an edge to the Lion means "the
  Lion could have won without any Scorpion help." She actually argues that **the
  UNICORN could have triumphed without Scorpion assistance** — which is the form
  that kills the claim to payment.

- **Monban gave ten numbered points; the record gives three.** Restored in full,
  including the bound foot, the burning tent, the Shinjo's death closing off
  dialogue with the Imperials, the comparative performance of each magistrate's
  ancestor, and the closer: victory was never won on the field, it was bought as
  *time* for the Imperials to arrive. Plus the detail that **the battle standard of
  the Snow Plain hangs in this castle** — the Lion kept the standard and were
  declared to have lost the war.

- **His second speech failed.** The great clan-by-clan tirade ("the only ones close
  to you who would even consider helping you are the Scorpion, once again") was a
  performance check he lost — Kaage is not moved by emotional flourish. He spent
  what was left putting strife on Tsubame and on the judge.

- **Midori's morality argument did not land.** The record says "the room went
  politely quiet" and treats it as a win — "a room with no answer is where a
  magistrate rules." She failed the roll; there was polite silence and the court
  moved on. What she gained was private: that righteousness in her peers matters to
  her more than she knew, which is her own clan's virtue. Also restored: Aishi's
  challenge ("who is she to dictate what is honourable in war"), Midori's answer
  ("I am a magistrate just as much as you — except you got to talk and I did not"),
  Kaage making the advocate withdraw it, and **the fact that Kitsu Yue's part in
  recovering Kitsu shugenja techniques was credited to Kitsu Somalia instead.**

- **Ayoko's testimony, compressed in the record.** She went white as a sheet, had
  not expected to be called, was assisted by Setsuna and Midori, and was
  **compromised** by the time she finished. She believed Yue was protecting Kitsu
  Somalia, and that Yue did not recognise her own worth.

- **The Akodo citation.** Monban asked whether fear is not against Bushidō, and was
  answered with a citation: he had not carefully read Akodo's *Leadership*. *"Fear
  is natural. Fear is part of every soldier's heart. The choice to go forward
  anyway, even though you feel fear — that is the essence of Bushidō."* Absent.

- **Monban threatened the youngest person in the room.** After telling Ayoko her
  ancestor was junk until these histories surfaced, he distinguished her from a
  magistrate who might have said the same: *"I have already proven your testimony
  isn't really necessary. But I certainly won't forget it."*

- **Why Setsuna asked to be excused.** She has a fear of ghosts as a character
  disadvantage. She **unmasked**, broke decorum to plead against the summoning, was
  not recognised, paid for speaking out of turn, and was refused. She then held her
  composure through the séance by controlled breathing and took net five strife for
  it.

- **The séance debate, absent.** Tsubame turned the Scorpion's own jurisprudence on
  them — it is the Scorpion who have argued successfully in these courts that a
  spirit says whatever its summoner wants. Aishi set conditions. Midori noted three
  shugenja were present so none could bend the spirits. Monban argued for a
  disinterested summoner and noted he is the blood of both the dead.

- **Kaage unmasked too.** *"I have allowed this farce to go on as long as I have.
  Why not."* And then, to Setsuna: *"Because at this point this has gone to absolute
  madness, and I do not see why not to continue with it until it is concluded."* The
  GM noted he takes a hit for it — this will not be one of his better-respected
  rulings.

- **The rite.** Kitsu Takeko, void/theology at difficulty four with Midori
  assisting, rolled a heap of exploders — "the spirits didn't stand a chance" — then
  threw salts into the braziers, which burned green, and the dead became visible.

- **Standing at close of session: Imperial 19, Scorpion 17, Unicorn 6.** The Imperial
  finding overtook the Scorpion during Midori's and Aishi's exchange. The GM: "we're
  not sure who's going to win yet, but we're pretty sure who's going to lose."

### A defect in my own checking, found and fixed

Inserting the s26 accepts hit a **duplicate ACCEPT key** — a pre-existing
`s25-court-of-competing-claims.md` block from the 2026-08 voice pass that my s25
block had silently shadowed (Python keeps the last literal key). My guard was
`assert len(ACCEPT) == len(set(ACCEPT))`, which **can never fail**, because the dict
is already deduplicated before the assertion sees it. That is the same class of bug
as the s13 duplicate, and my check would never have caught either.

Replaced with `scripts/acceptcheck.py`, which parses the source with `ast` and
reports duplicate file keys and duplicate tokens within a block, exiting non-zero.
Regression-tested against a synthetic file with both defects: the old check reports
"unique: True", the new one reports both and exits 1. The s25 and s26 blocks are now
merged into the pre-existing ones rather than shadowing them.

### Session 26 open threads

- **"The Doctor"** — Monban names a second infiltrator alongside Akuyaku, who "may or
  may not have been responsible for the Shiba's ancestor's injuries." Not otherwise
  identified.
- **Shosuro Amane carries herself exactly as Shosuro Aishi does.** Setsuna noticed it
  immediately. Whether that is family resemblance or something else is open.

## Session 27 — what the record had wrong

Recording `2025-11-10 - Fragile Peace.mp3.docx`, 1097 normalised lines. Clean, no
bleed. Export dates run a day late as usual (s27 = 2025-11-11).

- **A session is missing from the chronicle, and it is the verdict.** The recording
  opens with the table recapping a ruling that happened "session before last," and a
  player saying "I've missed two sessions." There is no recording for 2025-10-27 or
  2025-11-03 and no export entry between s26 and s27 — so the climax of a
  six-session arbitration exists nowhere in the record except as second-hand recap
  inside s27. Everything below about the ruling is from that recap, which is all
  there is.

- **The record never says who won.** It says only "that is the case closed and
  closed her way." The recap is explicit: the Imperial argument **reached the post
  first**, the mines go to the Empire, and the Scorpion were close enough that one
  more solid roll would have taken it.

- **Kaage let her draft the judgment.** Not in the record at all: "Kaage gave you the
  privilege of basically helping him write the judicial decision on the matter. So
  you assisted him in crafting the actual legal response and justifying it." It has
  been dispatched to the capital and the decision is public.

- **The gift is a book, and the record never says so.** It is a novel by **Hana no
  Ame** — the same author three separate investigative teams are hunting in the City
  of the Rich Frog, which the record treats as unrelated gossip. Harunobu does not
  read; he is literate enough for military orders and dislikes it. He knows she
  reads, and bought it almost certainly before he went to war.

- **The two errands are one place.** The record has them going west to ask about the
  Lion siege and, separately, to get Harunobu out. Setsuna knows where to write to
  him because that is where he is held, and the Lion army holding him is the army
  besieging **Gatherer of Wind's Castle** — one of the Ide's principal fortresses,
  possibly fallen already.

- **Wrong person, twice over.** The record says "Bayushi Monban asked Kitsu Takeko
  humbly for the return of a certain letter." He asks **Doji Setsuna** for **Akodo
  Akihito's letter** — the one that declined to move her husband. With a bruise
  attached: *"if he was looking out for me, he would have given me the yoriki I
  requested."*

- **Matsu Koda is a fabrication.** The record identifies the Lion at the teahouse as
  "the same Matsu Koda who duelled Kakita Kazumi at Loyalty Castle and apologised to
  her in open court." **Koda does not appear anywhere in the recording**, and Kazumi
  is not in this session at all. The Lion pair are an unnamed young **Matsu** woman
  and **Karu Akiara**, a former Lion now of the **Karu** — a family of ronin who
  provide security in the city, answer to the Miya governor rather than any clan,
  and are not averse to rough work. Setsuna pointed Akiara out to Midori because his
  face is uncannily **Uncle's**.

- **Midori failed the petition and got everything anyway.** The record has a clean
  *"Of course you may."* She stumbled over her words, could not project, and her
  soft voice would not carry — Takeko had to ask her to repeat herself more than
  once, and she took three strife for it. The grant came regardless, and what she
  learned was that **Takeko is moved by wit and charm rather than correctness**.

- **Monban's letter was forged.** Entirely absent from the record: the missive he
  received about his betrothed was not from her — she was demonstrably at the Wall
  on the date, and it bore only a **Crab military chop**, no personal signature.
  Somebody wrote to him in her name to draw him south.

- **The Sword of Hiruma, and why he cares.** Her real letter says the sword was
  stolen from the Hiruma's new castle and that she has been sent **over the Wall**
  after it, the clan being nearly certain the first enemy's servants took it. The
  record has "Monban took the news badly." He roared loudly enough to be heard
  through the walls, punched the floor, and **Ryu and So saw the green snowflakes
  behind his mask and were frightened of him for the first time**. A Hiruma
  physician nursed him through a long illness; the Hiruma take new arrivals at the
  Wall in hand; *"I would have married one if I hadn't met my betrothed."* He is now
  learning a ritual called the **Wayfarer's Path**, and wants to go south, and has
  given his word to go west first.

- **The intruder.** The record has the broom. It omits that the servant was going
  through Midori's things, that the corridor she followed them into **smelled of
  sulphur and held fog**, and that they did not find what they came for.

- **Monban's lecture was to both of them, and he was wrong about the facts.** He
  forgave Kitsu Ayoko for accusing him in the hearing and had to be told she had done
  no such thing — it was Ide Tsubame, and Ayoko's distress on the stand was his own
  doing. The rest is generous: counsel in confidence, a promise to halt the blade,
  and an invitation to correct *him* if he starts to slip. Meanwhile **Setsuna was
  concealing her disdain for the jumped-up peasant**, which the record does not
  mention.

- **The pact has a carve-out.** The record has "nobody speaks of their deaths, and
  nobody speaks of what happened to them at the Snow Plain." Monban made the
  exception explicit: a lord asking a vassal what happened is a reasonable question,
  and nobody is being asked to lie to their own lord — it is simply not offered to
  everyone who asks. It also holds only "until I speak to my champion."

- **Monban has changed how he travels**, absent from the record: pleasant and
  attentive to the retinue, fraternising on the grounds that they all serve the
  Emperor, with Ryu reminding him he is not supposed to. He trains with the Crab
  daily. The man they were told about was a sickly boy who coughed; he now nearly
  matches the youngest brother. *"The situation has changed"* is all he will say.

- **The city, and the teahouse.** The record gives a line. The recording gives three
  cities at one junction: a Unicorn wharf walled in black granite under violet roofs
  with a tower said to reach across the river; a Dragon bank of shrines and a
  neglected jetty whose sides mark the months, with a lantern moved around it; and a
  Lion trade hub with no riverbank at all, working cargo through a walled canal of
  six gates. The teahouse has no name because it changed hands until the name was
  lost.

- **Six samurai in three pairs, all hunting.** The record has "a young Lion woman and
  a monk in Dragon colours." There are also two Ide women who look like Tsubame's
  cousins, and the young man in Dragon colours is **Kitsuki Wataru's son**, a Dragon
  magistrate. Midori read all three groups' lips: the Unicorn looking for a woman,
  the Lion under orders to stop someone slandering the clan, and the Dragon tracing
  someone who had been asking questions here.

- **Wataru has not come home.** Last known travelling through Phoenix lands with
  young Emerald Magistrates, then nothing. Recalled from retirement by his lord the
  **Ruby Champion**. Monban's message to the son: write to your mother, he is on his
  way, *"do not be surprised at his change. Do not ask him about it."*

- **The talisman trade, and who is asking.** Hana no Ame met **Tonbo Kuma**, the
  Dragonfly shrine keeper, asking how meishodo talismans work — which is why a Dragon
  magistrate is here. There are also **fox in the city** who may be involved. Midori's
  reaction is the important part and the record omits it: *"part of the whole meishodo
  thing is why I got killed the last time"* — a council so busy regulating other
  clans' magic that it failed to stop mahōtsukai — and binding a spirit into paper
  offends her twice, once for the spirit and once for the hoarding.

- **The Lion's actual problem.** Hana no Ame's next book concerns an illicit affair
  between a Lion and a spirit, and the Matsu thinks the assignment is nonsense but her
  lord asked. Setsuna cornered her with Monban as a foil — *"you mean there is basis
  in fact for the story?"* — and beat her not on vigilance but on focus. Her advice
  was genuine: a book not yet written is redirected, not stopped, *"it is easier to
  redirect than to stop a moving object."* Her offer of help is also genuine, because
  she wants more books and would prefer the next one not be about ghosts.

- **Leadership and Lies.** Setsuna asked what the famous Lion book was called and was
  looked at as the least informed person in the Empire — *"It is not a book. It is
  THE book."* And Monban on Bayushi's *Lies*: *"when Bayushi wrote Lies, he was
  telling the truth. Lies is full of truth."* It was his school assignment, and he was
  praised for it.

### Resolved by this session

- **"Big sister" is Shiba Midori.** Owner's ruling, 2026-09-13, correcting my call.
  I read the s27 passage ("I may be pissed at her and Akihito for giving that letter
  over, but I have the letter back") as Setsuna, because Monban asks *Lady Doji* for
  Akihito's refusal letter in the same scene. That conflated two different letters:
  the one he is angry about is the **sealed letter Midori presented as evidence** in
  s24 — which is exactly what he says in s25, "instead of giving me the letter that we
  both know was my letter, you presented it as evidence."

  The corpus settles it four sessions later and I should have looked forward before
  calling it resolved: in **s31** Monban comes off a roof unmasked shouting *my big
  sister!* over a scrap of navy blue with an emerald green border, and the woman he
  finds in the skiff is **Shiba Midori** — Setsuna is the one who kneels and examines
  her. Every other instance fits: the Phoenix-mountains pen-pal trip in s24, "if your
  actions embarrass my big sister" said to Midori's own yoriki, and Akihito sending
  the cache to Midori rather than to anyone else.

  **Method note:** when a thread is open across sessions, check the later sessions
  before declaring it closed. The answer was already written down.
- **The former companion's fate**: sent back to a grandfather, then to the Castle of
  the Centipede to try for peace, and failing that to the Wall.

### Session 27 open threads

- **Karu Akiara has Uncle's face.** Both Setsuna and Midori saw it.
- **Kitsu Takeko recognised the Slowtide Harbor mahōtsukai on sight**, with horror,
  from a sketch — and Monban chose not to raise it with her before leaving.
- **Fox in the City of the Rich Frog**, possibly mixed up in the talisman trade.

## Session 28 — what the record had wrong

Recording `2025-11-17 Fragile Peace.mp3.docx`, 706 normalised lines. Clean. The
pre-pass record was 46 lines, the thinnest of the pass, and the session is one long
intrigue at a single table.

- **Isawa Kaede is a fabrication, and it misgendered two people at once.** The record
  had "Isawa Kaede once accused his practice of *caging* spirits and it nearly went
  to a duel," with a Learned bullet inventing her as "a Phoenix who accused Iuchi
  Minoru's practice." The recording has Minoru quote an **unnamed male Isawa** —
  *"an Isawa once put it to me that my magic requires caging that which should never
  be bound"* — stopped short of a duel because **his** superior told him to stand
  down. The Archivist completed the family name to the famous Isawa Kaede, who in
  this corpus (s08, s09) is the Lion Champion's betrothed, a Void shugenja, and has
  no connection to this teahouse.

- **Iuchi Minoru is a woman.** The record uses he/him throughout. The recording is
  she/her without exception — *"she looks back to Midori,"* *"she says, lovingly
  stroking the sides of her teacup,"* *"my grandmother had a set much like this."*
  Same defect class as Ikoma Hideri, Kitsu Somalia and Iuchi Gero.

- **The bait plan is backwards.** The record: "Kaeru Akiara's proposal was to put
  Kakita Kazumi down there as bait," and the Setsuna section warns that this is the
  plan one proposes if what is wanted is a magistrate alone in a known place after
  dark. **Kazumi engineered it.** He paid a servant to cut his sake half with water,
  performed being drunk, and pushed until Akiara said *"maybe you'd be willing to be
  the bait, the sting."* Akiara had already turned his help down flat once — *"you're
  a silk-swaddled boy"* — before the act.

- **The city's geography was wrong and the island was missing.** The record has "the
  Lion hold the south bank, the Dragon and the Unicorn the rest." It is Dragon north,
  Lion south, Unicorn west, **and an island in the middle holding Governor Miya
  Tetsuya's palace**, because three clans meeting requires an Imperial.

- **The reason for staying dark is sharper than recorded.** Not simply that "a badge
  closes mouths." The Unicorn practise a magic the rest of the Empire does not
  understand, and the Magistracy is the law that does not understand it — so to a
  Unicorn a magistrate asking about meishōdō is a tool of the oppressors. *"First
  part would be getting anyone like that to trust us and not think we're there to
  execute them and their families."*

- **Why the party cares at all, absent from the record.** Helping the Lion with the
  book puts the Lion in their debt; favours owed to law enforcement near the Lion
  border buy passage — **and buy leverage over people the Lion are holding. Her
  husband.**

- **What is actually happening at the docks was never stated.** People have been
  going missing, and the Kaeru are leaving the docks unpoliced after dark **on
  purpose**, waiting for whoever works there to make a catchable mistake.

- **Ide Iwena is not hunting the author.** The single biggest omission. Setsuna read
  her twice: the war is distant in her mind and her answer about it was a prepared
  toss-off, and what is actually driving her is **concern for a friend she believes
  is in danger** — not her companion, someone else. Midori arrived at the same place
  and further: Iwena knows the author. Which recasts the Toshi Ranbo line entirely —
  not a lie planted by someone watching the party, but a frightened woman sending
  strangers away from someone she is protecting.

- **Minoru's warning is more specific than recorded.** She delivered it stroking a
  teacup from a set two centuries old and still in daily service, then poured tea
  into it: a sacred relic is *the home and the vessel for a being of great power*,
  and *such a bowl would be such a vessel. Extremely dangerous.* She was telling a
  room full of strangers what is in the cup they are drinking from.

- **Midori tested the jade cup story and it held.** The record has the story as an
  anecdote. Midori ran Truth Burns Through Lies against it; the point it hangs on is
  whether Minoru genuinely saw the spirit; it holds, which makes her a spirit
  speaker — and the second inference follows, that a Unicorn-trained shugenja knows
  how these talismans are made and has at minimum handled them.

- **Monban's approach failed** — the only one in the room that did. He chose courtesy
  over command (correct: Minoru has a streak of grandeur and dislikes being spoken
  down to) and still got *"I am not sure I understand your meaning."* He spent both
  opportunities on not giving offence. His second try, with the Crab as cover and
  academic curiosity as the excuse, got him a door left open — *"I can humour you in
  at least a general sense"* — and directions for calling on her.

- **Restored dialogue**: *"Spirits are partners, not our servants"*; *"you are not one
  of us, but you talk like one"*; Kazumi's *"very well, pretty boy"*; the capital
  being *"a long way away... and we generally don't care"*; Kazumi shouting across
  the table that his mother would cut Monban's tantō off; and Minoru's parting *"may
  the Kami go with you."*

- **Not maho — gaijin magic**, which the table noted is close to the same charge in
  Rokugan but is not the same thing.

### Session 28 open threads

- **Setsuna voted for a reckless plan on timing**: they call on Governor Miya Tetsuya
  in the morning, and after that this stops being possible. Tonight is the last night
  they are nobody.
- **The Kaeru answer to the governor, not to any clan**, and are allowing people to
  vanish in order to build a case. Patient or complicit is not distinguishable from
  outside, and the party declares itself in that governor's palace tomorrow.
- **Whatever Hana no Ame learned** while researching how meishōdō talismans work is
  now the live question, rather than where she is.

### Also corrected: Kaeru, not Karu (s27)

My s27 wrote the ronin family as **Karu** from the 2025-11-10 audio, where the GM
spelled the name into chat rather than saying it. The corpus has **Kaeru Akiara** 9
times, Kaeru Haya 7, Kaeru Ronin 4 — and my line was the only "Karu" anywhere in it.
Fixed, linked, and given a Learned bullet. Same lesson as the "big sister" call:
check the corpus forward before trusting a transcript on a name.

## Session 29 — what the record had wrong

Recording `2025-11-24 - Fragile Peace.mp3.docx`, 923 normalised lines. The `(2)`
duplicate is byte-identical after normalisation. Clean, no bleed. The record was
broadly accurate on shape and missed most of the substance.

- **The handling instructions were never paid for, and that is the session.** The
  record has the receipts and the Fox Clan seller. What it omits is the shopkeeper's
  last remark: some of those papers are *"handling instructions for the talisman
  that they neglected to pay for. I assume they'd be back for them later once they
  figured out they couldn't do anything without them."* Hana no Ame can open the
  talisman. She cannot reseal it or move what is in it. The only copy of the
  instructions is now in Setsuna's hands, and the shopkeeper has agreed to send word
  when she comes back for them.

- **The tail was following the magistrates.** The record says "he was not following
  the party at all — he was after the judge," which reads as a third party. The
  judge *is* the party: a Kaeru police officer shadowing Emerald Magistrates through
  his own district, which the table glossed as the police trying to tail the FBI.

- **Midori did not accuse him; she performed at him.** The record: "Shiba Midori
  accused him outright of setting the man outside on them, and pushed until he
  broke." She played an outraged noblewoman — *a knave, a ruffian* — implied he had
  arranged the tail, and **unmasked into it, sobbing and beating him with her fan**,
  choosing to enrage rather than daze him on the reasoning that her blessed lineage
  made retaliation unthinkable and Monban was a step from the door.

- **Setsuna was compromised, dazed, and unmasked — twice over.** None of this is in
  the record. Daidoji Shin dazed her, learned her **Imperial bloodline**, and later
  her **haunting**. She unmasked deliberately with *"have you not read the novels of
  Hana no Ame? Sometimes what a fine lady needs are the rough hands of a sailor"* to
  clear it — and he answered with *"such a shame they had to turn you into a peace
  cow with the Unicorn, of all people."* Wordplay is the passion of both of them,
  which is why she heard it instantly and gave him nothing back.

- **Shin is a rank amateur** with, in the GM's words, a neon sign over his head.
  Officially the Crane liaison here; unofficially a posting to get an obnoxious man
  out of the way. One of **Daidoji Uji's** more disposable agents. Good at exactly
  one thing — talking a person to death. His bodyguard is **Mori Kasami**, who
  mouths *"I am sorry, I do not know what possessed him"* behind his back.

- **The commercial survey is a diversion, not a request.** The record has Setsuna
  asking for "a written survey of the city's commercial situation." She outranks him
  and used it to inflict an all-nighter on something she has no intention of reading;
  her stated objective was to get him out of their hair. Also restored: nobody sees
  the governor in the morning who was not on his books a fortnight ago.

- **The teacup callback.** The curio shop holds a very good old tea set *"very much
  like the one at the teahouse"* — same age, different maker. In s28 Iuchi Minoru
  delivered her warning about vessels while stroking that teahouse set. The record
  notes "a very good old tea set" and does not connect it.

- **Midori's way in was "small friends"** — a child's colloquial word for meishōdō,
  half-mistranslated across dialects. The record has only "the sort of thing a child
  would ask for."

- **Setsuna's read of the shopkeeper is sharper than "his shutters came down."** He
  is not a dealer and not a criminal: he suspects what passes through his hands and
  has deliberately avoided confirming it, *"because then he'd be in even deeper
  trouble."* He also raised **the missing persons** unprompted, denying involvement
  before anyone had asked.

- **The lever that opened him** was one sentence: *"the police are indeed coming. Do
  you want those receipts in your hands when they arrive, or would you prefer they
  were in ours?"*

- **Buyer and seller are two different people** and he is the middleman — bought from
  a Fox Clan man claiming goods from across the Burning Sands (*"not quite meishōdō.
  I didn't believe him. My customers certainly did, and that's all that matters"*),
  sold to Hana no Ame. The buyer's receipt is deliberately blank but for the chop;
  the seller's carries seal, chop and address.

- **What the instructions actually say.** Faded, complicated, and *"barely Rokugani"*
  — a target-number-four read. A talisman that has failed to hold its spirit **cannot
  be used again**, so a release demands a fresh vessel prepared beforehand; the
  spells are for *resealing*, requiring the spirit to be subdued first. If the
  talisman has been used the spirit may already be loose and the papers do not say
  what becomes of it. The saddle tassel is just pretty.

- **Midori's objection, and her honesty about its limits.** *"This is not working
  with a spirit. This is beating the spirit into submission, shoving it in a box, and
  making it do what you want when you want."* **The spirit's consent is nowhere in
  the document.** Pressed on whether she actually knows it is unwilling — a rite
  might call a spirit that understands the bargain — she conceded she would need a
  Unicorn practitioner to trust her far more than any of them do.

- **The worst finding in the session, absent from the record.** Her plan to ask the
  local kami what had been released ran into this: anyone doing such work will have
  made certain no free spirit remains nearby to carry word of it. **There may not be
  a single ordinary kami left at the centre of the city**, which disables her magic
  there. A silence where there should be voices is evidence of scale.

- **Restored dialogue and staging**: Monban squatting to look Shin in the face
  (*"this might get a little too rough for your feathers"*); the officer dropping
  into a rising-draw stance; Kazumi coming off the roof in a tumble to make the man
  the meat in a sandwich; *"I would so hate to have to find an appropriate ditch. Or
  some nice weights"*; the officer catching himself mid-sentence — *"wait, you don't
  want me to do that"*; and the shopkeeper turning to find a Scorpion behind him —
  *"I do not need to die, I will keep my mouth shut."*

- **Monban's restraint.** He asked the shopkeeper *"have you lied?"* (*"not to your
  knowledge"*), then told him to make friends with certain strangers because whatever
  he is doing here is evidently known. When Setsuna asked him to ease off: *"He was
  honest. He is the middleman. He is not the person we want."*

### Session 29 open threads

- **Whichever branch Hana no Ame is on** — talisman already used and something loose,
  or not yet used and she must return for the papers — the shopkeeper is the hinge,
  and he is now theirs.
- **A Kaeru officer told Monban that outsiders "may disrupt delicate plans already in
  place."** The local police are either running something or waiting on something at
  the docks, and the party declares itself to their governor tomorrow.
- **The Elemental Master of Earth** — the man who replaced the one Midori duelled —
  has been travelling and negotiating with the Unicorn over how much of their art the
  Elemental Council will tolerate.

## Session 30 — what the record had wrong

Recording `2025-12-01 - Fragile Peace.mp3.docx`, 1062 normalised lines. Clean, no
bleed. The record had the events roughly right and missed the causation entirely.

- **Kaeru Haya stranded the ship on purpose, and that is why people are going
  missing.** The record lists her findings as three separate facts — a Mantis ship
  lingering, opium underneath, sailors disappearing. The recording gives them as one
  chain: she **arrested about half the Mantis crew in a drunken brawl and persuaded
  her lord not to release them to the captain**, deliberately, to ground the ship
  until she could catch its supplier. A ship that cannot crew itself cannot sail.
  *"But it seems they've taken to alternate methods of recruiting their ship, so to
  speak. A couple of sailors have gone missing."* She has not connected the
  disappearances to the Mantis — and the connection is her own operation working as
  designed.

  Which is also why Midori was put in the river rather than simply robbed, and why
  the second group on the boards said **"boss says we need one more to get out of
  here tomorrow."** The s31 epigraph already says *they were not robbing her, they
  were collecting her*; s30 now supplies the reason.

- **The gong was an abort, not an alarm.** The record has the ronin "lit a lantern,
  and reached for a handheld gong" as though signalling accomplices. He says it
  plainly: *"I had to sound the alarm to make sure they wouldn't scare away the
  fish"* and *"I would rather scare off the fish than have you bungle the catch."*
  He was aborting his own side's stakeout to stop the magistrates wrecking it. He
  also spent the whole approach making them conspicuous on purpose — swinging the
  lantern, finding every board that creaks.

- **He has a name: Kaeru Naito.** Given when another ronin tells him off for leaving
  his post. He was **new**, and under orders to observe the magistrates only — not
  to engage, not to report.

- **Kaeru Haia → Kaeru Haya**, per the owner's 2026-08-13 merge, and it is what she
  calls herself when she finally introduces herself on this recording.

- **The Lion samurai has a name: Matsu Ren**, established when Setsuna asks who
  Kaeru Akiara has been minding.

- **Monban declined an informant**, absent from the record, and the reason is the
  character beat: there is always a Scorpion to deal with in a city this size, and
  he decided the question you ask an informant tells the informant what you are
  doing. The GM's reaction: *"Setsuna, what have you been doing to him? You might
  actually make an honest man out of him."*

- **The blade at the throat, staged properly.** He got there between the first
  strike and the second, jamming the *sheath* between hammer and gong with the blade
  at the man's neck. *"Make another sound and it will be your last, dog."* — *"Kill
  me, and the family that I found will never stop hunting."*

- **Monban apologised and gained six honour.** Entirely absent. Kaeru Haya demanded
  satisfaction for drawn steel — Naito is ronin but still samurai, so the duel was
  hers to ask for — and he talked it down with a formal apology: her operation should
  not have been disrupted so, and she would find them dependable allies. The GM ruled
  negotiating away a justified duel a major sacrifice for honour: **six honour, to
  33**, his first earned individually, and enough to lift him clear of the threshold
  where disdain for courtesy counts against him.

- **Setsuna's mediation used Monban against himself.** The record says she "mediated
  it." What she said was that the ronin declined to cede ground for the same reason
  he had not stepped aside in their own last disagreement — and that she does not
  begrudge them it. Then, to Haya: you were not briefed, this was a surprise, we
  would be glad to collaborate, *but that will require your working with us.*

- **The count was wrong all night and nobody noticed but the party.** Naito reported
  three magistrates; Haya planned around three. When Setsuna mentioned two at the
  docks, the arithmetic broke in front of her — *"he had to leave one at the water,
  and surely my men have an eye on her."* They did not. **Those were not her men.**
  Kazumi was never counted at all.

- **What Kazumi actually watched**, compressed to two lines in the record: a small
  craft working *up* the river against the current, sliding into the one wedge of
  shadow between the deck lanterns, the dock and the moon; three taps on the hull; a
  line dropped at a low rail; a crane, a net, two tugs, a few bushels. *"This entire
  process is taking about five times as long as [it needs to] because they're going
  slowly, so the gears and the winches and the pulleys won't squeak."* And his read
  of the ground: **nothing dangerous, nothing defiled, none of the hallmarks** — plus
  a conspicuous absence of any security at all.

- **The chase and the captive.** He threw a knife at four range bands, dropped to the
  dock and threw Midori a rope rather than diving in, recovered the knife on the run
  and found blood on it — *and would rather nobody in the party looked at that knife,
  because of the man it was used to kill.* He ran her down through the warehouses,
  cleaved club and straw hat, **threw his katana through her foot** using the memory
  of Akodo Akihito for the reroll, and knelt on her: *"Now, friend. Why did you have
  to push that nice young lady into the river? She didn't smell that bad, did she?"*
  — *"Please. I only wanted her body. You can have it."* — *"I will let you live. But
  you owe me your life."*

- **Midori was attacked twice.** After hauling herself out in wet shugenja robes at
  three or four in the morning, she heard boards creaking behind her, got a hand to
  her daishō, and heard the line about needing one more, and *"it is only bad luck,
  but we will have to make an exception in your case."*

- **Opium is legal.** The offence is the unpaid duty, and Governor Miya Tetsuya has
  been losing revenue steadily — *"an IRS, not a DEA situation"*, in the table's
  gloss. *"But the quantities in this latest shipment are something else."*

- **Monban knows Yoritomo Kuroba and hissed at the name.** Setsuna does not know who
  he is. Where they met is not recoverable from the audio and is not recorded.

- **Midori's objection, in its sharpest form**: not that the Unicorn use spirits, but
  the difference between temporarily asking a servant of heaven to serve, and telling
  a servant of heaven to get in the box.

### Session 30 open threads

- **Kaeru Haya deferred a duel, she did not forgive one.** *"That I do want
  satisfaction for. We can discuss that later."*
- **Where Monban knows Yoritomo Kuroba from.**
- **Kazumi's knife**, and the man it killed, which he is keeping from the party.

## Session 31 — what the record had wrong

Recording `2025-12-08 L5R.txt`, 1024 normalised utterances. **Different format from
everything before it** — `[Speaker N]:` paragraphs with no timestamps — so
`scratchpad/norm_txt.py` numbers the utterances instead, and chunk addressing is by
line number rather than clock. The ASR is also markedly worse than the .docx set
(Kakita renders as "cacoda"/"palsy Mary", Kaeru as "Cairo"/"Carol"), so attributions
were taken only where the surrounding dialogue makes them unambiguous.

- **The ransom exists because of one of Setsuna's own rulings.** The record has
  Kubota's story as an unverified claim about "local bosses". He names the cause:
  a dock boss called **Yaguro** was tried and executed by three magistrates, and
  *"we have you to thank for it"* — Setsuna is one of the three. With Yaguro gone
  the surviving bosses grew bold, took the wife of a dock magistrate (she is
  **Tortoise**), and then took his daughter. That is Kubota's grand-niece, the
  ransom is in his hold, he is **making nothing on the run**, and he took it because
  he is the fastest ship available.

- **Kubota is a Fleet Admiral and a daimyo's equivalent**, not "master of the
  blue-water ship" — of standing enough to have had the Emperor's ear. The table's
  gloss: *"this is the FBI having pulled over the governor's car."*

- **He did anchor.** The record says he "would not". He objected, was told the
  Magistracy would pay for the damage, and then complied — *"they may not work, but
  we'll put them down"* — and it went wrong exactly as he had predicted. The lines
  snapped taut, the ship pitched toward rocks, the crew cut the starboard line, and
  **the other anchor tore away on its own**. *"What do you want me to do? I am fresh
  out of anchors."*

- **Monban knows him, and it is comic.** They have met: Monban was sick on the man's
  boots. He also knows **Kubota's first mate from the Topaz Championship** and says
  he holds a trump card over him — *"if we need leverage, we have it; if we need an
  admission of guilt, we should be able to get it."* Absent from the record.

- **The precedent that explains the whole stakeout.** Setsuna knows the Mantis
  problem from Kitsuki Wataru's casework: two Crane caught with art of unusual
  provenance blamed the Mantis, who pulled rank, told the court they had come to him
  *because* he can get such things, and said he held none of it — being true, since
  he had already delivered it. The magistrates ruled for the Mantis. **Rank gets you
  aboard; without the goods in hand you must let him go.** That is why the Kaeru
  would not be hurried, and the record has none of it.

- **Kubota's parting advice, and the blackmail.** *"You think yourself cloaked in
  Imperial glory with that badge, and you take every chance to mention that you know
  the Emperor. You will not impress the real powers that way. You need to become
  somebody in your own right — somebody known for more than showing his tanto."* And
  then the trade: silence about the sails for silence about the vomiting, since
  *"the same people who talk about you showing your tanto to an old lady"* would
  enjoy the story. **The "least of the Bayushi" reputation has reached a fleet
  admiral on the far side of the Empire.**

- **The weapons, precisely.** Two apiece, identical, wooden, no edge — *"bruised and
  beat up, not actively hurt."* They fought in water stance and stayed in it because
  it was working, using Striking as Water to strip her resistance. And Midori
  **refused to surrender** when she could no longer defend herself, took a critical
  strike for it, and went under anyway.

- **She was stripped of everything.** The record notes the clothes. She wakes and
  reaches for her daisho by reflex and it is gone; so is her purse; **and she does
  not even have a tanto.** Setsuna's medicine check got **zero successes** — the
  record's "Stabilised" is not what happened — and Midori treated herself and
  established a real wound through the right side, a rib, plus ten fatigue.

- **Setsuna commandeered the operation.** The record has Kaeru Haya running the
  search. Setsuna had deferred to the Kaeru all night and then pulled rank
  deliberately: an Emerald Magistrate is missing on these docks and that outranks a
  smuggling case. Haya agreed instantly — *"an Emerald Magistrate is missing; yes,
  that does matter quite a bit"* — and sent her man **Koji** to turn everyone out
  with lanterns. She is addressed as **Captain Haya**.

- **Monban's hair.** Flying up on Ride the Clouds he threw a burst of emerald
  snowflakes and **some of his hair is emerald now**. The green has been in his eyes
  since s27; this is new.

- **Kubota does not know he was stranded on purpose.** He blames his own men for
  drunken brawling, says they have forfeited their pay, and blames *"that stupid
  Miya"* for not releasing them. Kaeru Haya arranged it (s30) and he has no idea.
  He also **told the dockmaster he meant to sail that day**, so the departure was
  announced rather than a flight.

- **Smaller restorations**: the small boats missing from their moorings, which
  Setsuna noticed while playing the naive visitor; Midori going at two-to-one alone
  because delusions of grandeur is a flaw she has; Monban losing **three glory** for
  unmasking and screaming in public; the navy-blue-with-emerald-border robe being a
  deliberate choice by an Emerald Magistrate who *"sometimes decides not to be
  subtle"*; the fishing skiff with its buckets, oars and two poles, tied to the dock
  a good distance from where the cloth tore; and the bill for a fleet admiral's sails
  arriving at Monban's lord in two or three weeks.

### Session 31 open threads

- **Whether Kubota was telling the truth**, and whether a child's ransom was delayed
  this morning. He read as a man who is not a practised liar.
- **Kakita Kazumi**, missing since before dawn, uncounted by everyone including the
  ronin — and the bait plan at the docks was one he engineered himself (s28).
- **The quota is nearly filled.** *The boss needs another. Then we get them and get
  out of here.*

## Session 32 — what the record had wrong

Recording `2025-12-15 - L5R.mp3.docx`, 952 normalised lines, back to the .docx
format. Clean. The pre-pass record was 40 lines for a session that names the
quarry, loses and recovers a PC's soul-blade, and ends on a second bound spirit
nobody has accounted for.

- **The novelist has a name, and the recording says SHINJO Higuchi.** Tonbo Kuma
  gives it, and it matches the description they have been chasing. The whole
  following sequence depends on it: Setsuna says *"my husband is a Shinjo"* and rolls
  a culture check on that family. **Note the conflict:** the same recording names
  Kuma's go opponent **Tonbo** Higuchi, and the existing s33 record calls the author
  Tonbo Higuchi. The GM audibly corrects himself to "Shinjo Higuchi" when naming the
  quarry, which reads as deliberate disambiguation between two people who share a
  personal name — but this is not settled. **Left unlinked in s32 and to be resolved
  against the 2025-12-22 recording at s33.**

- **What Higuchi was actually asking**, which the record reduces to "researching how
  people interact with spirits": *"they wanted to know how people who are not
  shugenja contact the spirit world. I thought that a very strange question, because
  the spirits speak only to whom they choose."* That is a description of what a
  meishodo talisman does.

- **She is staying with the governor** — Kuma's strong supposition, since Miya
  Tetsuya referred her to him. And the governor's possessed guest is a woman with a
  burning look in her eyes who ate her breakfast and threw the bowl into the fire.
  The record does not connect them.

- **A second, larger spirit is still bound, and this is the urgent finding.** The
  record has only "a caged spirit was let out to start it." The fire spirits also
  say it *"called us to join in the celebration of its liberation"* — and that
  **there was a big one in that space too when the little one was released.** A lesser
  spirit was spent as arson; a far more powerful one is still held.

- **Midori's daisho was stolen and recovered**, and the record contains neither. A
  fisherman found the swords dumped in his boat and would not touch them — *"I know
  the rules and so do I."* They carry her own chop, were **forged by Kakita Kazumi's
  father**, and are her **Topaz Championship winnings**. Monban retrieved them and
  did not hand them back, carrying them himself within her reach given the state she
  was in.

- **Setsuna's report, in its actual proportions.** Two thirds of her effort went into
  the Kaeru — their conduct *infallible*, and a recommendation that **they be
  considered for inclusion as a clan** — and one third into the captain. And Kaeru
  Haya **cannot write**: *"none of my ronin know how; if I must have something
  written I go to the lord and use his scribe."* That, not volunteering, is why
  Setsuna holds the pen, and why her chop carries testimony Haya cannot sign.

- **Monban wrote a second, harsher letter under his own name**, absent entirely:
  obstruction of justice, dishonourable conduct toward a magistrate and a governor,
  and **dereliction of duty for abandoning half his crew in a city far from Mantis
  lands with no lord**. Factual, only mildly inflammatory, and almost subtle, which
  everyone found more unsettling than the letter. *"His name is on it and mine is
  not, and it will stay that way."*

- **Monban's lesson from the old Dragon monk**, absent entirely, and it carries the
  session's best character material. He unmasked and showed his face paint; the monk
  averted his eyes. *"The techniques allow you to do what your body can already do.
  You must simply remind it."* Then: *"The Tao must live here, but it must be
  breathed here. You are imbalanced. Very imbalanced, and prone to dream."* The monk
  broke a waterfall over him with Fist of Air on the way out. And underneath it:
  **Monban had an incurable disease, never expected to outlive his gempuku, and died
  shortly after it** — his memories of his own life now marred by *"an existence that
  did not quite happen."*

- **Asahina Nao is the most useful arrival in the city** and the record gives her one
  line as a courier. She is a Crane shugenja of fire and water with **specialist
  expertise in meishodo** — taught its principles, widely travelled in Unicorn lands,
  and has studied with Unicorn shugenja on nearly even terms. Summoned by the
  governor precisely as an expert on possession, and a friend of Daidoji Shin's.

- **Shinjo Miharu.** Setsuna failed her recall on Higuchi and surfaced this instead:
  **a cousin of her husband's, taken prisoner at the same battle** — remembered from
  the postscript of the letter Kaage was reading when Midori pointed out it was not
  in evidence. Which means Midori has been carrying something about that letter since
  s24.

- **The theatre is the Riverfront Theater**, and the **Riverfront Theater Group** is
  the company that staged the play about Kazumi — which is why Setsuna wants to buy
  the ruin.

- **Tonbo Kuma is probably a shugenja**: the water moves when he gestures, the way it
  does around Midori. He keeps one of Hana no Ame's books on his shelf, admires the
  work, and does not connect the author to his visitor. Nobody told him.

- **Monban's Cleansing Spirit failed twice** at the docks. The record has him putting
  the ritual over the group before going in to the governor; there is no successful
  casting anywhere in the session.

- **The discretion was the governor's request, not the party's offer.** *"I will
  clear the island of anyone you consider inessential... I would like this dealt with
  quietly and as non-destructively as possible. If you can get the spirit thing out
  of my friend without burning down my house, that would be ideal."*

- **Smaller restorations**: Kazumi's terms to the thief and the digging trowels his
  new henchman was sent to buy; Kaeru Haya's rebuke about leaving a spirit speaker
  alone and that Midori **has no yojimbo**; Midori healing the man who robbed her in
  front of the whole watch; the go games at maximum handicap and Kuma's verdict; the
  exchange about fire spirits being *"very well fed"*; and Setsuna opening the door
  at the governor's table for Midori to tell Daidoji Shin what burned his theatre —
  aiming for distressing rather than insulting.

### The duplicate-key check earned its keep

Inserting the s32 accepts tripped `scripts/acceptcheck.py`: a pre-existing s32 block
from the 2026-08 voice pass (the Kaeru Haia merge) was being silently shadowed by
mine. Merged into one block. This is the third such duplicate in the pass and the
first caught automatically.

### Session 32 open threads

- **Shinjo Higuchi or Tonbo Higuchi** — settle at s33 against the recording.
- **The larger bound spirit**, still held by whoever burned the theatre.
- **Shinjo Miharu**, and whatever Midori knows from the postscript of Akihito's
  letter that was never read into evidence.
- **Whether Captain Kubota's ransom story was true**, now that two documents calling
  him dishonourable are on their way to the capital.

## Session 33 — what the record had wrong

Recording `2025-12-22 - L5R.mp3.docx`. There are two files for that date; they are
byte-identical (`cf8c12a5117a31027e501b0ac75e92c9`), so there is one recording, not
two. 1,155 normalised lines. The session ends unfinished — the GM says so, and says
they will pick up the pieces next time.

### The name, settled

**The possessed author is SHINJO Higuchi.** The recording says "Shinjo Higuchi" and
nothing else (2:45:04). This matches the s32 recording, where Tonbo Kuma gives that
name for the person researching spirits (s32 line 508: *"the Shinjo Higuchi doesn't
ring any bells to you"*), and where Setsuna's whole culture-check sequence turns on
her husband being a Shinjo.

**Tonbo Higuchi is a different person** — the man Kuma was playing go against when
the magistrates arrived, introduced separately at s32 1:05:34 (*"this one's name is
Tonbo Higuchi"*). Two Higuchis in one city. The old s33 record merged them and used
the wrong one throughout. Corrected, with the merge explained in the Setsuna section
so the change is legible to anyone who read the old page.

The Hana no Ame identification is sound and is supported in-recording twice over:
the GM opens by calling her "the poor author" (0:00:15), and describes the talisman
as the one whose handling instructions "the lady neglected to purchase" (0:02:41) —
i.e. the buyer on the s29 receipt. The s32 recording says it outright at 2:37:59:
*"Higuchi or Hana no Ame."*

### What the record had wrong, or did not have

- **She was cold, not numb.** The old record had her "feeding logs into the furnace
  and not feeling the heat at all." She was complaining of cold on the hottest day
  of summer while sweating through her clothes, and eating like she was starving.
  The contradiction is load-bearing: she said she was cold and then, a minute later,
  that it was too hot in the house, and that is what told Midori there were two of
  them in there.

- **Kazumi stole the pendant.** The old record has him seeing it and taking it off
  her. He asked her whether he was addressing the lady or the being in her body,
  got a flash of recognition and then confusion, and then lifted it off her neck
  with a sleight-of-hand roll without her noticing. It blistered his fingers.

- **The pendant's magic is alien, not meishōdō.** Midori's reading: the method and
  the power are both wholly foreign, someone able to do things she cannot conceive
  of forced a very powerful spirit into it — and **the vessel is empty and was
  emptied recently**, so the spirit had been in Higuchi for about a day. None of
  this was in the record.

- **She stripped and bathed in the fish pond**, and the spirit in her knew Monban
  by reputation and teased him about having flashed an old lady. Monban stripped to
  the waist to lay the barrier. Setsuna excused herself and Kazumi walked her out.

- **Asahina Nao did not know Monban was a shugenja.** He took the mask off and
  showed her the paint. She calls him "the legendary Bayushi Monban."

- **The pull through the barrier earned him a critical slap.** She passed the check,
  came through whole, hit him hard enough to count as a crit, called him a brute and
  went for her clothes. On the second attempt she failed and bounced off the barrier.
  The barrier works both ways.

- **Monban told her who he is.** *"I am no brute. I am a Kuni Warden."* Mask off, in
  front of her. The record had none of this.

- **The reason the plan failed is a sentence at the top of the instructions.** The
  sealing ritual works only on an *unbound* spirit, and a spirit riding a person is
  already bound — bound in a person rather than an object. Midori found it reading
  properly (1:30:10); Monban had read the same papers and they had not made sense to
  him (1:36:30). The old record attributed the reordering to the Heart of Amaterasu
  failing. It did not fail — she summoned it, and Asahina Nao could not be asked to
  assist because the working was past anything she knew of.

- **Monban threw Midori at the target.** The Cleansing Rite needs a hand on the
  person. Midori is small and light. He picked her up and threw her, she caught
  Higuchi by the temples: *"Spirit, I revoke your welcome in this body. Go away."*
  The old record had the two of them running the rite together.

- **The transformation, in full.** Tattoos on his feet and ribs moving — two phoenix
  and a crane flapping their wings, the dragon, lion, crab and scorpion travelling
  round his body; half his hair emerald green; eyes black as the void but for two
  spinning emerald snowflakes; sickly yellow through his veins; the demon wound
  burning; coughing the party had not heard in weeks. And then, before he drew:
  *"Onahime, little sister, time to play"* — a second black shape out of his
  shoulders and head, which stayed out for the rest of the night.

- **The Ifrit manifested inside the barrier**, and that is the only reason anyone
  survived. Midori spotted it. Its void is poor; it spent a void point trying to
  breach the ward and failed. Nobody engineered this.

- **Kuma never entered the fight.** The old record says Kuma "arrived with his
  bodyguard to help." They arrived, walked in on the Ifrit coming out of her, and
  stood there. The GM had not written a stat block for them. Also: **Kuma is
  they/them and Asahina Nao is she** — stated explicitly at 2:31:10.

- **Asahina Nao wanted it destroyed.** *"See? It's dangerous! It must be destroyed,
  if you can."* She failed her sealing checks more than once.

### The offer, and who actually refused it

The record had Setsuna offering a parley and Midori putting up protection. Both
halves are wrong about who did what.

**Setsuna's offer was to carry the Ifrit to the castle holding the Unicorn prisoners
of war, free the prisoners, and let the spirit blow east across the Lion armies.**
She knelt at the edge of the barrier, bowed, said *"spirit, you wish to be freed. I
could bear you to a location where you could be freed"* — and spent two opportunities
pushing that picture at it (2:17:08). Monban objected that he had spent the evening
building a box to keep it in. Asahina Nao asked whether she had lost her mind. Her
husband is among those prisoners.

**Midori relayed every word of it and then refused it.** She translated in full
because she would not have the right to stand otherwise — *"the Phoenix in me"* —
then bared the dead eye: *"the laws of Rokugan are no kinder than the laws of the
dead. We cannot let this monster free."* Setsuna corrected her: it is not a monster,
it is a spirit, it was put into an object against its will, and it had not asked to
keep a body — it asked whether it had to go back into one. Midori heard the sentence
back, admitted she had misread it, looked at it with the full dead eyes and told it
yes, it did have to.

The Ifrit's actual lines, addressed to Midori as interpreter: *"Must I shrink myself
to fill a mortal again? Just free me."* Then, face brought uncomfortably close:
*"there's no other way, I will go with them."* Setsuna held the vessel; what came
through her hands as it collapsed into the jar was sadness with a weight behind it.
Asahina Nao sealed it and said it was almost as though it had given up.

### The quarrel

Monban healed Kazumi's bleeding first, then rounded on her. What he said was not
about the spirit: *"never put yourself in danger without speaking to me first. Your
words are your responsibility. Your life is mine."* She answered *"that is quite
enough, Monban. You don't understand"* and **relieved him of the burden**. He did not
answer at all and walked away. Both unmasked, in front of everybody. He covered the
naked woman with his own top on the way out.

### A build break I shipped three sessions ago — found and fixed

`build_site.py` has been failing since commit `0e09d06` (session 30), and I reported
`build_site` OK for sessions 30, 31 and 32. It was not OK. The failure:

```
KeyError: "session 30: 'Learned' names 'Kaeru Naito', which has no page."
```

Every `## Learned` name must resolve to an entity page or be marked `(unpaged)`. The
s30 pass added a `Kaeru Naito` bullet and no page. Because the ledger loop raises on
the first offender, two more of the same defect were hiding behind it — `Shinjo
Higuchi` (s32) and `The burned theatre` (s32). Fixed by adding
`sources/entities/Kaeru Naito.md` and `sources/entities/Shinjo Higuchi.md` (both
named in the record, both now central), and marking the theatre `(unpaged)` since
the record describes it and never names it.

**Method note.** Running a gate is not the same as reading its output. The lesson
from the big-sister correction was to check later sessions before declaring a
cross-session thread resolved; the lesson here is narrower and worse: check that the
gate actually exited 0 before writing that it passed.

### Session 33 open threads

- **The Ifrit is a witness**, and nobody has interviewed it. It knows who bound it,
  who carried it, and who put it into Higuchi.
- **Who steered the talisman to her**, given a Lion and a Unicorn were both already
  hunting her before she was possessed.
- **The larger bound spirit from s32** is still unaccounted for.
- **Setsuna said out loud, in front of the governor's shugenja, what she would do
  with a spirit weapon if she had one.** Whether anyone in that garden was listening
  is a live question.
- The session was **not finished** — the GM says they pick up the pieces next time,
  so some of this may resolve at s34.

## Session 34 — what the record had wrong

Recording `2025-12-29 - L5R.mp3.docx`, one file, 485 normalised lines — a short
session (1:09) that ends mid-scene because a player had to leave. The GM tells the
rest to carry on without them.

### A title used as a name: "Daimyo Shosuro" is Shosuro Hametsu

The old record called Monban's lord **Daimyo Shosuro** in the prose and gave him a
Learned bullet under that name. He is **Shosuro Hametsu**, established since s09 as
Monban's lord and Bayushi Kachiko's brother, and named in s09, s47, s49 and s54. The
recording says *"my lord's daimyō, Shosuro"* and then, a minute later, *"Hametsu,
you owe me one."* The old record read the title as if it were the name.

**Scope of the defect, stated accurately.** `archivist.ALIASES` already carried
`"Daimyo Shosuro": "Shosuro Hametsu"` (archivist.py:540), so the wikilink always
resolved to the right page and there was never a second page. What was wrong is
narrower: s34's entry on Hametsu's page was headed with a title instead of his name,
and the prose named him that way too, so a reader of s34 had no way to connect the
man giving the order to the lord they already know from s09 and s47. Corrected.

My first write-up of this said the record "minted a duplicate entity" and that "the
phantom page is gone." Neither was true — I checked `ls dramatis-personae/` after
the build and inferred a deletion from an absence, without checking whether the page
had ever existed. The alias in archivist.py settles it.

**And the provenance of the order is new.** Setsuna's own lord asked for a bodyguard
for her, because she has a habit of being in dangerous situations. The favour was
traded round a table until somebody landed it on Hametsu, who *"happened to have an
Emerald Magistrate in my employ who pisses me off with some frequency"* and could
*"think of nothing better to do with him than to attach him to a crane's tail
feathers."* The grudge is specific: Monban once refused him a request any other
Scorpion would have leapt at, **and then called the guards on him for asking.**
Hametsu pulled strings to take him into service afterward, to torture him, because
it amuses him and because Monban keeps costing him money. A bill for the Mantis
ship's sails is coming.

The bind is **asymmetric**, and the recording spells it out: Setsuna is under no
obligation to have a yojimbo and may treat him as dismissed as she likes; he is
under orders until his lord rescinds them.

### The recap is wrong, and the GM corrects it in the same recording

The old lede said *"it was Shiba Midori who talked the Efreet into standing down —
she argued against enslaving it, out loud, while it burned in front of her, and it
listened."* That is a player's recap of s33 (0:05:29), and the GM corrects it
immediately (0:06:09–0:06:50): the ward held, it could kill inside the circle but
could not leave one, *"it knew it was being bound back in a box whether it liked it
or not"*, and *"it just kind of gave up because it was at a point where it had no
valid targets."* This matches the s33 recording, where Midori refused the parley and
told it to get in the box.

The record had inherited the table's misremembering as fact.

### The wrong man is rowing

The old record: *"Bayushi Monban took an unmanned boat and started rowing
upstream."* He said he could row and then did not have to. **Kakita Kazumi took
servant's clothes, greased his hair black, made a performance roll to disguise
himself, beat Monban's vigilance with Effective Harmlessness and took the oars.**
Monban does not know who is rowing his boat.

Kazumi is in the whole back half of this session unseen. He beat everyone's
vigilance to get into Setsuna's quarters and was in the room for the entire bedside
scene; the old record has him only on the roof afterward. His stated intent both
times is to get the box for himself.

### What else the record had wrong, or did not have

- **Asahina Nao's objection is the fact of the session and it was missing.** The
  palace is on an island in the middle of the river with city in every direction.
  Upstream is Unicorn country; downstream is Scorpion or Lion, possibly Dragon. A
  forest is a forest fire. **There is nowhere within reach of this city to release
  a great fire spirit that is not somebody's province.** Nobody answered her. Her
  own proposal was a well, or a dark hole, or taking it to the Unicorn shugenja to
  be sealed past anyone's reach — which Monban refused.

- **Setsuna was maxed out on strife and physically shaking**, by her own account, and
  in no state to process anything. That is why she would not let go, and it makes
  the refusal something other than a decision.

- **She did not hand over the box.** She moved so it was no longer behind her and let
  him take it. Monban knelt, head on hands, eyes level with hers, and there was a
  softness in him she had not seen before. He invoked **a deal between them** — new,
  and unexplained. She woke on *"what are you doing in my quarters? You were
  released."* He left her with *"your dreams will be softer"* and put the blanket
  back over her.

- **Monban let Midori knock**, as angry as he was and as close as he was to walking
  in and taking it. The badge came out only when the servant balked.

- **The box's influence is mechanical and confirmed.** He put it against his skin,
  failed a meditation check, and was stuck in fire as his ring for the rest of the
  night and distinctly more irritable. The old record had the effect right and the
  cause vague.

- **Kazumi had burning as well as bleeding.** Monban had already stopped the bleeding
  in the garden. He carried him into the pool to put the fire out, spent a void
  point on Warrior's Resolve to take five fatigue off him, and hummed a lullaby at
  him.

- **Midori conceded while saying she could not argue.** *"I'm fighting my own dark
  thoughts too much to actually be making cogent arguments right now"* — and, on the
  party: *"no one is willing to wait, or take rest and then make rational decisions,
  so there's no rational decisions to be made."* She went to be there, not because
  she was persuaded. Also hers: *"I died once. It was not worth it."*

- **Monban's plan is to break the box**, not to work a release — go a little upriver,
  break it, and tell the spirit that as long as it goes its own way nobody will
  trouble it, and to stay away from the Unicorn, *"they have a tendency to trap
  things like this."* Asked whether he had a way to make it agree, he said he was
  freeing it and that should be enough. Asked whether *should* was the same as sure,
  he said he was sure enough to swim.

- **Setsuna sleeps for a day and a half** after this, so she is absent from whatever
  happens at the river.

### Efreet vs Ifrit — left alone deliberately

s34 is the only session that spells it **Efreet**; s33, s39, s49 and s54 all use
**Ifrit**. The GM says "Efreet" out loud in this recording (0:17:41) and
distinguishes it from a djinn. `archivist.ALIASES` already maps `Efreet` to the
Ifrit page, so there is one entity and no broken link — only the rendered spelling
differs, and the session's own exported title is "Confrontation with the Efreet",
which the pass does not rewrite. Normalising the body would leave the title and the
body disagreeing, which is worse. Left as is; noted here so it is a decision rather
than an oversight.

### Session 34 open threads

- **"Remember our deal."** Monban invoked a deal with Setsuna at her bedside and
  neither of them explained it. Not obviously anywhere earlier in the record.
- **Kazumi wants the box** and has told nobody. He is rowing.
- **Where the Ifrit can actually be released**, given Asahina Nao is right about the
  geography. Answered eventually — s39 has Midori undertaking to carry it west to
  the Burning Sands — but not here.
- The session **ends mid-scene**; s35 should pick up on the river.

## Session 35 — what the record had wrong

Recording `2026-01-05 - L5R.mp3.docx`, 1,183 normalised lines, three hours. There are
two files for the date; they normalise to identical content (they differ only in the
speaker-tag punctuation the exporter emitted), so there is one recording.

### The envoy

The old record said "young." She is **sixteen**, she is **Governor Miya Tetsuya's
niece**, and she has **no retinue, no experience and no actual authority** — told not
to bring a retinue because it would be faster. Her uncle refused to let her travel
unescorted; she had thought being an Imperial was protection enough.

**The decisive detail was missing entirely: her instructions from the Imperial
Advisor were delivered orally, by one of the Advisor's servants.** The only thing on
paper is the Emperor's own demand. Whoever briefed her can deny every word of it, and
the one witness is a girl they appear to expect not to return. That, not her youth,
is the reason the party read her as a cat's paw.

They had already told her so — between sessions, in a scene the recording only
recaps. She has been too frightened to leave her room since. *"I'm dead. I'm dead.
I'm dead."* The GM's verdict on it: *"you all sussed it out real fast, but we
shouldn't have told her."*

### Setsuna's own line about her husband

Not in the old record at all, and it is the coldest thing she has said about him.
Asked whether the object was to find the Lion and ransom Shinjo Harunobu: *"it's
possible that my goals are not limited to my husband, and so it depends on what other
concessions are available as to whether or not we choose to ransom him or not."* Said
to an Imperial envoy, in a tea house, in front of two magistrates.

### The apothecary was Setsuna, not Midori

The old record: *"Shiba Midori used her authority as an Emerald Magistrate to make an
apothecary hand over the last restricted herb."* **It was Doji Setsuna.** She sent her
own literate scribe with a written list; the scribe read it and warned her the
substance is of questionable legality, that only certain apothecaries carry it and
none would dispense that quantity. She went herself, showed her own chop, told the
man he would sell it to her servant in the amount requested, and left Ishika to
settle the price because a samurai does not haggle. The exposure is hers.

### Monban knows

The old record: *"Bayushi Monban was turned away at the door and does not [know]."*
He does. The sequence:

1. He met the servants coming off the boat and asked to see the bundles. They refused
   — *"I am not allowed to disclose the lady's business"* — and he answered with his
   own formula, *"the lady's words are her responsibility. Her life is mine,"* and
   they still refused.
2. He **failed** a skulduggery roll to see inside, then **succeeded** on a theorise
   roll using his Natural Herbalist specialty: there are things in there that are
   medicine titrated one way and poison titrated another.
3. He asked her outright. *"Are you sick?" / "Yes, in a way. I have been sick." /
   "What way?" / "I would prefer you to not have to lie." / "Then don't lie."* She
   refused, said Midori was ensuring her safety, and gave him one concession: go to
   Midori, and help only if Midori says he can. He has not gone.
4. Kazumi put an arm round him and steered him off — *"there are some issues in which
   a woman is allowed her privacy."*
5. He then made a **sentiment roll with six successes** and the GM gave him: sick in
   the mornings repeatedly over recent weeks, no other complaint, going to a shugenja
   for medicine — *"you can put two and two together."*

He has not been told. That is a different and thinner thing than not knowing, and the
record was asserting the wrong one.

### What else was missing

- **A play about Kakita Kazumi** opens in a month, as one of the first showings at the
  city's new opera house. The trader's servants recognised him by it — *"you're THAT
  Kazumi."* His line: *"every action I take endangers myself. Haven't you seen the
  play?"*

- **A Shosuro mark on the theatre wall.** Monban's afternoon was otherwise fruitless
  — his one Scorpion contact was a young man in a cat mask on holiday from Slowtide
  Harbor who knew nothing, though he did say *"there are servants of the family
  around, I see their marks from time to time"* — and Monban's Lord Bayushi's
  Whispers roll for those marks failed. Then he wandered into the Burnt Theater ruin
  and spotted, on a destroyed section of wall, a mark in the style the Shosuro use.

- **The theatre is purified, not unsettled.** The old record said the disturbance "has
  not settled." The temple completed the cleansing rites; the ground is clean and
  matches what Monban can feel. What a Dragon priest says is that the aftershock of a
  fire spirit breaking loose will leave the place **unnaturally dark** for a long
  time. Different claim.

- **The audience that night was half the city's government** — Daidoji Shin, Miya
  Tetsuya, and a dozen more names, mostly Unicorn with some Lion and the odd Dragon.
  **Nobody of consequence died. A couple of servants are unaccounted for and no bodies
  were ever found.** None of this was in the record, and it is the best unexploited
  lead in the session.

- **Irei Sakube**, a dealer in fine art and antiquities from all over Rokugan "and some
  say beyond," was named to Kazumi as a source and never approached. Given the
  foreign-talisman trade, worth remembering. New entity page.

- **The party has no escort, no standard and no mon**, and no way to raise any. Four
  people in magistrate robes walking into a battlefield will be killed before anyone
  asks who they are. Raised in play and never solved.

- **Tetsuya's warning about the palanquin:** *"you are going to be a walking peacock
  across the Unicorn lands. The Lion will see you coming from miles away."* Setsuna's
  answer: envoys want to be seen.

- **The shopping failed worse than the record said.** Two of four ingredients, with
  substitutions that will be useless at best — including an expensive foreign exotic
  that is a nightshade relative, bought in place of the nightshade. The one mercy is
  that they did not come back with anything more dangerous than intended; the cost is
  that **the dose of the poisons she does have had to be increased.**

- **Midori is short of money** — Lady Tsubasa has not sent her allowance — so Setsuna
  paid for it.

- **Kazumi's packet is deliberately unlabelled.** He refused to write the characters
  for nightshade on it; he tells his poisons apart by the colour of the tie. Handling
  instructions: one or two leaves, never with bare hands, never lick anything
  afterward, wash thoroughly.

- **Kazumi was invisible in the room twice** — once through the whole bedside argument
  at Midori's door, where he leaned in beside Monban's ear and asked what he was
  doing. Monban's exit line: *"and I'm the Scorpion here. I'm the untrustworthy one."*
  He went to his rooms and read the Tao of Shinsei.

- **The cleanest exchange in the session**, between Kazumi and Midori over the brewing:
  *"Don't you want to know what we're doing?" / "I have my suspicions." / "You do not
  need to state them openly." / "If you do not state them openly, I do not need to lie
  about how I know."*

- **The mechanics of the dose.** Midori erred toward too little, so failure was the
  likelier error than death. Drinking it was a fitness roll against a critical hit at
  difficulty seven (poison is normally ten; the titration bought the difference).
  Setsuna took it in Void, chose Sacrifice over Stand, spent a void point and invoked
  Blessed Lineage. Result: **severely wounded in the void ring, plus gut sickness and
  exhaustion.** The old record had the void wound and not the rest.

- **It is a crime.** The table established after play that this is illegal, and that in
  law the death of an heir is a death. Worth recording as exposure, alongside the
  compelled apothecary sale.

### Two spelling catches on my own draft

`build_site` caught **Kitsuki Kage** in my Learned bullet — the corpus name is
**Kitsuki Kaage**, and `archivist.ALIASES` already maps the "Katsuki Kage" the
transcriber produces. Also four wikilinks I wrote on faith and `verify_site`
refused — Governor's Tea House, Tea House With No Name, The Famous Mediocrity, Tao
of Shinsei — all now plain text. Standing method held: write them, let the gate
adjudicate.

### Session 35 open threads

- **The unaccounted-for servants** from the theatre fire, and no bodies.
- **The Shosuro mark** on the theatre wall, and the marks the visiting Scorpion says
  are about the city.
- **Irei Sakube**, never approached.
- **Whether Hana no Ame travels west with them** — Setsuna left the invitation and
  the answer had not come.
- **The escort problem.** They are going into a war zone with no standard.
- **Whether one dose was enough.** Midori measured to fail rather than kill.

## Session 36 — what the record had wrong

Recording `2026-01-12 L5R Fragile Peace.txt` — the first plain-text transcript in the
pass, and **much worse quality than the Cockatoo .docx exports**: no timestamps,
speaker attribution collapsed (one tag carries the GM and several players), and heavy
word-level garbling. 811 normalised utterances. Everything below is what is legible
with confidence; several smaller beats were left out rather than guessed at.

New helper installed as `scripts/norm_txt2.py`. The earlier `norm_txt.py` assumed
`[Speaker N]: text` on one line; this file puts the tag on its own line, so the old
parser produced 1,622 useless `(cont)` rows. The new one joins tag to body.

### The record buried the two largest facts in the session

**1. Monban contracted a murder.** The old record: *"He wanted something for a woman,
and he traded future favours for help getting a servant to carry the gift."* What the
recording has him say, in Cadence, to a Scorpion informant in a pleasure house:

> *"I could have use for a servant to bring foodstuffs into the rooms. And have the
> interesting ingredient served to her. It would have to be quick. I don't need her
> to explode. I need her to expire. Quickly."*

He already had a Western flower and judged it would take too much. The cousin — *"I
don't do that, I never have, my job was to get information"* — turned out to be well
versed anyway, could manage quick but not silent, and Monban took quick, on the one
condition that nothing trace back to either of them. They leave in the morning, so it
was set for **the noon meal**. The price is future favours, and the cousin named the
shape of them aloud: the family will have a target it needs removed, and a man who
buys poison can be assumed willing to use it again.

**The woman is never named in the recording.** The record must not guess, and does not.

**2. Monban is wearing the Ifrit.** The session ends with him undressing for the bath
and a **warm golden chain around his neck that was not there the day before**. He
knows it is there. He does not want it off. It is comfortable. He does not remember
taking the box and does not remember most of his night. In his quarters are three of
the little boxes with **the protective seals deliberately scratched off**, Midori's
magical locks broken, and every one of her warnings scratched over with *"fuck you, I
do what I want."*

The GM says it outright in the closing minutes: *"I only planned the ninja attack. The
rest of it was you guys. I had to explain why Monban was behaving weirdly."* Kazumi,
in play: *"almost like he was possessed."*

That reframes the whole night. The old record had none of it — not the amulet, not the
scratched seals, not the blackout. It had him "going to pray"; he cast Cleansing
Spirit on his own intoxication and **failed**, and stayed drunk.

### The dark blue cloth is not from session six

The old Setsuna section: *"Dark blue with no clan mon is what the men who ambushed the
road wore in session six, the ones who released two Emerald Magistrates on sight of
rank and took Asako Taishi anyway. They are back."*

The recording rules it out. Midori asks whether it is a colour she has seen recently,
or on any samurai of her acquaintance, and the answer is **no** on both, and *"it
doesn't look like it belongs to clothing any samurai have."* It is shinobi cloth, cut
so that held against a shadow it is near impossible to see. There is no prior sighting
to match it to. The connection was invented, and it was load-bearing for the old
reading of the session.

### Kazumi got the box, and it was already empty

The old record had him *"looking for"* it. He went over the roof, opened the tatami,
shimmied down the wall and took it on **eight successes**, well past Midori's
vigilance — and it was empty, and the GM made him certain of it. Midori had already
given the genuinely empty vessel to **Kitsu Ayoko** for safekeeping; the box in
Monban's quarters was there before he got home.

### What else was missing or wrong

- **Ryu is Monban's servant, not Kazumi's.** The old Learned bullet said "Kazumi's
  subordinate." Kazumi sends for him and says *"go find your master."* Ryu found him
  unable to walk a straight line and hired a cart; told the passenger was an Emerald
  Magistrate, the cart-pusher said he was His Majesty the Emperor and still had rent
  to find.

- **The poison was delivered.** A man Monban did not know was waiting in the boat —
  plain black shirt, brown trousers, a market bundle — who leaned over, said his lord
  sent his regards, put the bundle in his hands and stepped off. He is carrying it.

- **Setsuna ordered a killing.** She drew the shuriken out of the wall herself and
  wrapped it in cloth, because a shuriken is a classic poison delivery, then handed it
  to Kazumi: *"this shuriken needs to be returned to its rightful owner,"* with a
  stated implication of force. *"I will see that it is done, Lady Doji. With extreme
  diligence."* Absent from the old record entirely.

- **She got up on a fitness roll** against a hidden TN, taking all the strife, dressed
  over her ladies' objections, and gave herself an hour. Her face was most of the way
  to her own funeral paint before she applied any. She recovered no fatigue and no
  strife. Midori's treatment failed; she brought the chamomile straight back up.

- **The dose may not have worked.** Midori cannot tell whether she measured too little
  or the body is simply taking it badly — whether there is enough poison in her to
  make her this ill and not enough to finish what it was for. Knowing would need a
  more intrusive examination than the morning allowed. This is a live thread.

- **Misato tapped her kimono in public** when Kazumi asked where she keeps the writ —
  in front of the governor, the household and three Emerald Magistrates, none of whom
  stopped her. And it was **Kazumi**, not Setsuna's later analysis, who explained the
  seal-lifting forgery risk out loud in that room.

- **Kazumi went round to the door.** He looked through the window from the roof and
  then walked back through the building to knock, rather than dropping in, so as not
  to frighten her further. She threw herself at him: *"someone was here, they could
  have killed me, and they did not. Why did they not kill me?"*

- **The search:** fast, in the dark, exhaustive, for one specific thing they did not
  find. Footprint impressions in the tatami, dust scuffed about, and the window she
  had latched against the chill standing open on a bright moonlit night. Anyone with
  that long in the room could have killed her many times over.

- **The ink is dark blue**, the same colour as the cloth. Kazumi passed the note over
  a flame for hidden writing and got nothing, and could not place the ink.

- **Midori knows what Kazumi is.** She slipped him the fabric: *"someone you have a
  professional interest in?"* His eye twitched.

- **The governor offered Monban the post of Misato's yojimbo** and was declined — he
  is not sure Setsuna can even dismiss him, given who assigned him. He agreed to watch
  the girl anyway. The governor **will send some of his own men** on the journey, which
  is more than the "promised guards" the old record had. He also named the cost of the
  palanquin: six men carrying a box and no speed at all.

- **Monban's defence is on the record and was missing.** Asked why Setsuna looked the
  way she did, and told it was because her bodyguard was absent: *"Remember when I
  asked you last night what was going on? I asked the Shiba what was going on and I
  was told none of your business, go away. Well, I went away. Now I'm back. So what's
  the problem?"*

- **The cousin's advice, unasked:** *"your family is going to use you, abuse you and
  exploit you until you're useless. Get out while you can."* Monban: *"I am the
  Scorpion that serves... I do not run away from my responsibilities. I do not hide.
  I do not lie."*

- One stretch of table talk about reversing the mine ruling was **explicitly flagged
  player-to-player, not character-to-character**, and is deliberately not in the
  record.

### Session 36 open threads

- **Who the woman is** that Monban paid to have poisoned at the noon meal, and whether
  the amulet chose her or he did.
- **Getting the chain off him**, and Midori needing a clean vessel to start over.
- **Whether the dose worked.** Midori does not know.
- **Aoi**, and which of the two intruders they are — the one who wanted the seal, or
  the one who stood over Setsuna and took nothing.
- **The shuriken** Setsuna handed to Kazumi to return.
- Transcript quality: `.txt` recordings are markedly worse than the `.docx` exports.
  Expect more "left out rather than guessed" in any remaining `.txt` session.

## Session 37 — what the record had wrong

Recording `2026-02-02 - Fragile Peace.txt`, 1,033 normalised utterances. Same poor
`.txt` quality as s36 — no timestamps, collapsed speaker tags, heavy garbling. Some
beats were left out rather than guessed at.

### A new player character

**Ikoma Tadayoshi is a PC, not a hired musician.** The old Learned bullet: *"A Lion
musician, brought in to play at the afternoon tea."* A new player joined for this
session and the GM spends the opening minutes introducing the character, and the
closing minutes thanking him for playing along while they worked him in. He appears
as a party member from here on (s39 already has him spreading a story about a Crane
conspiracy and volunteering to escort the envoy as bait).

What the introduction gives: guest of the governor for about a week, back from touring
Unicorn lands studying music, and Miya Tetsuya is a patron of the arts who has been
enjoying his compositions. A harbinger figure — things go wrong where he goes. Trouble
with women, which may trace to promises made in childhood to certain shape-shifting
spirits and not kept. During the alarm he thought he briefly saw **two of the
governor's niece**.

### One niece, two pages

The old record carried a Learned bullet for **"Miya's Niece"** alongside Miya Misato.
They are the same person, and the recording never separates them — Tetsuya says "my
niece," the party says "the Miya," and both forms appear in one breath.

The duplicate came from the export, which filed her twice. Fixed in `archivist.py`:
`ALIASES` now points `Miya's Niece` at `Miya Misato`, and the extra export page is in
`SUPERSEDED_BY_LOCAL`.

### The decoy was in effect, and that is why Midori was taken

The old record had men who *"used her as a weapon"* and a niece bound in a separate
room, and no explanation of why anyone went near either. The s36 plan was running:
**Shiba Midori slept in the Imperial Envoy's room dressed as the Imperial Envoy.** The
attackers came through the door, one got a proper look at her face mid-assault and
said she was not the target — less politely than that — and they let her go.

**Four guards died**, not one. Tetsuya had moved Misato elsewhere and told his men to
guard a location without telling them why or that a move had happened; the only people
positioned to notice were the guards who were killed. Midori then got back to her own
room and found **Misato and Kitsu Ayoko tied up in it**, and her things gone through.

### The roof, and who Monban suspects

The old record had both findings and neither geography. **West side**, above the
second-level room (interior, one door, no windows): tiles picked off and broken, scuff
marks, **rope fibres wedged between two tiles**, climbing-claw scratches too small to
be Monban's own, and the attic panel removed and shoved aside. **East side**: tiles
lifted and carefully replaced, no claw marks anywhere near, **overlooking the guest
quarters**.

**He reported only the west side to the guards.** He said nothing about the east,
because he thinks it is Kakita Kazumi — who turned up at the docks with his hair dyed
black and ran off, and who this morning claimed he had been sparring. He then went and
found him, in a conversation so elaborately about the weather that nobody nearby
understood a word, and asked him on the roof whether he had been up there watching both
rooms. Kazumi said no. **He had been watching one.**

### The shore search found something, and they set a trap

The old record stopped at *"Bayushi Monban went up on Riding the Clouds to run the
shoreline from above while Kakita Kazumi walked it."* They found **two-foot bamboo
tubes, watertight, scraped by the rocks, buried under the reeds** carefully enough to
be nearly missed. Kazumi's reconstruction: cross at a busy hour, slip off a boat, into
the reeds, out after midnight. **Two groups.** The tubes were uncollected, so the men
who used them have not left.

**Kazumi then coated the insides with a numbing poison**, with Monban standing between
him and the guards on the wall, and they restored the site exactly — Monban made a
survival roll to put the dirt back. Afterwards they wandered the shoreline looking
foolish, in case anyone was watching from the water. Midori's floor mats were also
**damper than heavy fog alone would explain**.

### What else the record did not have

- **Setsuna slept through all of it** on Midori's sleeping draught, the only person in
  the castle who got a night's rest. She came to breakfast knowing nothing.

- **She failed the roll to keep her face neutral.** She thinks this is the city
  magistrate's failure and it was plain to see; the governor saw it, and gave it back
  in public — somebody has made a joke of his castle's security, and somebody seems to
  find it funny that men died protecting them while they slept in their sick bed.

- **Monban and Midori have matching bruises.** He asked why the pattern on her was
  familiar to him. She said sparring. *"It was not my idea."*

- **Monban's alibi**: if someone had not been messing with the mail he would have been
  there, but he had to step out on personal business.

- **The tea guests**, in full: Daidoji Shin with his bodyguard Doji Kasami; Asahina
  Nao; Shinjo Higuchi still recovering; one Lion; two Unicorn (an Ide with an Utaku);
  three Dragon; another Phoenix; a Crab pair including a Yasuki; and two Crane, both
  Doji and both cousins of Setsuna's. **Not one Scorpion in the room.**

- **Setsuna baited Daidoji Shin** into the investigation deliberately, so that he
  becomes the visible investigator and the magistrates can work underneath him.

- **Midori failed to open the ceremony**, nobody noticed it had begun, everyone kept
  talking — which was worth more than succeeding, for listening. She had no sleep and
  nine fatigue.

- **The Ide trader is the thread.** He wants to move goods from the furthest Unicorn
  lands through Crane networks to the capital and beyond. Promised samples his people
  have not produced. Told the hatamoto his networks are undisturbed by the conflict and
  that he has means of crossing rivers others lack; told Setsuna he is delayed because
  caravans must route round an expanding war zone and he is relying on unconventional
  means. Daidoji Shin was already watching him. Tadayoshi reads him as carrying himself
  above his apparent station — possibly of greater standing in his clan than he lets on.

  And unprompted, he said the person he knows with an appetite for **curiosities from
  beyond the border** is a **Crane**, not a Unicorn, and that he cannot account for
  where that interest came from.

- **The Yasuki's grievance is strategic intelligence.** He is part of the effort
  keeping the Wall supplied, and the Lion are blocking his cargo down the river while
  pulling supplies toward the war, and pressing him to sell to them instead. His ships
  cannot move.

- **Tadayoshi's first piece** came from the furthest edge of the Unicorn lands, and
  Setsuna is fairly sure she has heard her husband hum it. His second was the Tea
  Seller's Song, a childhood favourite of Midori's, and it stopped the room.

- **Nobody's mask slipped.** Tadayoshi canvassed the guests about the night and got the
  same account from everyone: bells, screaming, no information, no sleep.

- **Why the Lion have not taken this city**: doing so would mean offending not just the
  Unicorn and the Dragon but the Emperor directly.

- **Kazumi and Monban have both died and come back.** Monban: *"something tells me you
  are no longer a duellist."* Neither remembers anything between, and both have noticed
  changes in themselves since. Consistent with the Monban backstory recovered at s32,
  and new for Kazumi.

- The session ends with the two of them heading for **the Crane guests' rooms**, on a
  clue Monban gave Kazumi several sessions ago, with Monban walking on Kazumi's right
  so that a drawn blade would not reach him.

### Finishing the s33 ruling: the Higuchi aliases were still wrong

Found while fixing the niece duplicate, and it is my own unfinished work. At s33 I
corrected the prose to **Shinjo Higuchi** and left `archivist.py` alone — where
`ALIASES` still carried `"Hana no Ame": "Tonbo Higuchi"`, `"Hanano Ame"` and
`"Higuchi"` likewise, and `RENAMES` carried `"Hana no Ame": "Tonbo Higuchi"`. So every
`[[Hana no Ame]]` link in s27, s28, s29, s32 and s33 — thirteen of them — was still
resolving to the wrong person's page after I reported the correction done.

The export had made it worse than a spelling problem: its `Tonbo Higuchi.md` describes
**two people as one character**, a man excused from a go board and, three paragraphs
later, *"a disheveled woman in a purple dress"* who ate a goldfish raw. And it has a
third page, `Shinjo Higoichi.md`, for the same woman under a garbled given name.

Fixed by taking the local pages as authority:
- removed the `"Hana no Ame" -> "Tonbo Higuchi"` rename, which is what produced the
  merged page;
- added `Tonbo Higuchi`, `Hana no Ame` and `Shinjo Higoichi` to `SUPERSEDED_BY_LOCAL`;
- repointed the aliases at `Shinjo Higuchi`;
- wrote `sources/entities/Tonbo Higuchi.md` for the go opponent alone.

Three pages for two people are now two pages for two people. `verify_site` 0 broken,
0 unresolved.

**Method note.** Correcting prose is not correcting the record when a rewrite table
routes the links. After any name ruling, grep `archivist.py` for the old spelling
before reporting it done.

### Session 37 open threads

- **The tubes in the reeds**, poisoned, and whoever comes back for them.
- **The Ide trader**, his routes the war does not touch, and the samples that never
  came.
- **The Crane with an appetite for curiosities from beyond the border**, named by the
  Ide and not identified. Kazumi and Monban went to search the Crane guests' rooms.
- **Who on the island told them which room** and could not tell them which face.
- **Misato is hidden** somewhere by her uncle and has not been seen.
- **Kazumi and Monban's deaths**, and what changed in each of them.

## Sessions 41–55 — continuity review against the corrected record

Sessions 41–55 (plus 38–40, which have no recording) were hand-authored from the
same sources **before** the correction pass, so the risk was that they carry forward
facts the pass has since overturned. Swept mechanically for every name and fact the
pass changed, then read where anything hit.

**Clean:** no superseded spelling survives anywhere in 38–55 — checked Kitsuko,
Shoshuro, Ide Subane, Kitsu Yui, Katsuki, Karu, Miya Amaya, Daimyo Shosuro, Miya's
Niece, Efreet, Okoto, Shinjo Higoichi. No fabrication the pass removed reappears —
Matsu Koda, Isawa Kaede, Shinjo Altansari are absent. `verify_site` reports 0
superseded spellings rendered.

**Chains that hold.** The Ifrit is coherent end to end: sealed in a jar at s33, taken
by Monban at s34, worn without his remembering at s36, inside him and bargained over
at s39 (*"the old boxes are spent"* — consistent with him having emptied them), speaking
in his head at s41, freed at s49, gone at s54. s38 picks up s37's cliffhanger exactly:
the two of them search the Crane guest rooms and find contact poison in the ceiling.
And s52 explains the death Monban and Kazumi refer to at s37 — the masks, Jigoku, and
the bargain with Onahime — so the s37 exchange is corroborated downstream rather than
contradicted.

### Three corrections made

**1. Tonbo Kuma is they/them, and two sessions had him as he/him.** The 2025-12-22
recording settles it in the GM's own words at 2:31:10 — *"Tonbo Kuma is the they-them"*
— in the same breath as confirming Asahina Nao is she. The 2025-12-15 recording uses
"they" throughout (*"Kuma will say that they..."*, *"Kuma said that they spoke with him
two or three days ago"*). s32 had "his shelf", "he is an admirer", "he gestures"; s55
had "his group", "it is his turn", "his go game". Corrected in both, and in the
`Tonbo Higuchi` entity page I wrote yesterday, which had the same slip.

**2. s42 said only two people know about the tea.** *"a thing only Shiba Midori and
Kakita Kazumi know the cause of."* That is the claim the s35 correction removed:
Monban failed to see inside the bundles, deduced their contents from his own
herbalism, was refused to his face, and then made a sentiment roll the GM answered
with *"you can put two and two together."* He has not been told, which is a different
and thinner thing. Reworded to say exactly that.

**3. s38 presented the breathing tubes as the discovery.** They are the *second* set.
The export distinguishes them itself — it has separate item pages for `Bamboo
Breathing Tubes` (two-foot, watertight, buried among reeds) and `Snapped Reins
Breathing Tubes` (under shoreline rocks), and says plainly that the reins were *"a
different set... in a subsequent investigation."* s38 named only the reins, which
silently dropped the bamboo set recovered on the s37 recording — and with it the fact
that Kazumi poisoned those and left them in place. The export corroborates that too:
it has a `Numbing Poison` page saying Kazumi applied it to bamboo breathing tubes to
trap whoever came back. s38 now says two sets, and that more than one party came in
through the water.

### Threads left dangling, not contradicted

Flagged rather than corrected — nothing is wrong, these simply never come back:

- **The second, larger bound spirit** from the burned theatre (s32). Never mentioned
  again in 38–55.
- **The bamboo tubes in the reeds**, poisoned and left as a trap at s37. Nobody is
  ever shown springing it.
- **Aoi**, who signed the warning on the envoy's wall at s36, is named nowhere after.
- **Irei Sakube** (s35) and **the Crane with an appetite for curiosities from beyond
  the border** (s37) are never followed up under those descriptions, though s38's
  search of the Crane quarters is plainly the next step on the same trail.

## Chasing the two dangling threads

Both chased against **all 73 recordings**, extracted to plain text and searched
together, rather than against the corpus. One is a fabrication; the other is
genuinely unresolved.

### Aoi did not sign anything, and is not that Aoi

The old s36 record: a shuriken pinning a note reading *"Turn back. Aoi."*, and a
Setsuna paragraph built on it — *"nobody signs a threat to an Imperial envoy…
whoever Aoi is, they chose to be identifiable."*

What the 2026-01-12 recording actually has, as the guards bring the paper back:

> *"On which is crudely scrawled. **Two characters in blue ink. Turn back.**"*

and then, as a separate hesitant aside: *"Um, Joy."*

The Archivist turned that aside into a signature, and then — because an `Aoi`
already existed in its NPC files — **wikilinked it to her**: one of the three
Kitsu of a vassal family keeping the [[Border Waystation]] in s5, who admires
fashion and wishes she had half of Setsuna's wardrobe. The two were merged onto
one page, so the record had a waystation hostess signing a warning to an Imperial
envoy thirty-one sessions later.

**"Aoi" appears in exactly one of the 73 recordings, and it is the s5
waystation scene.** Nothing after s36 names her. And a note the GM describes as
*two characters* does not also carry a name.

The signature is removed. The note is two characters, unsigned, in the same dark
blue ink as the cloth in Setsuna's rafters — which is a better fact than the
invented one, because an unsigned warning-off from someone who could have killed
the envoy and did not is the more interesting object.

### The second bound spirit is a real loose end

The s32 fire spirits said a larger one was in the room when the little one went
out, and is still bound. Searched every recording from 2025-12-15 to 2026-09-07
for it — *bigger/larger/second/other spirit, still bound, theatre, arson,
meishōdō, talisman*. The only later hits are the Burnt Theater scene in s35
(already recorded) and an unrelated fire-spirit negotiation in the 2026-07-20
session.

**Nothing in any recording resolves it.** It is not a gap in the pass; it is a
thread the table has not returned to. Left standing, and now standing on
evidence rather than on my not having looked.

### The fix this exposed: struck identifications were not struck from the cast

A session's cast is read off the **export's** recap/moments/timeline, so removing
a fabricated identification from the prose never removed the person from the
session. Every fabrication the pass struck left the same residue — the page went
on listing a session its subject was never in:

| Page | Still listed | Removed from the prose at |
|---|---|---|
| Matsu Koda | Session 27 | s27 — nowhere in the recording, and Kazumi is not in the session |
| Isawa Kaede | Session 28 | s28 — the recording has an unnamed male Isawa |
| Aoi | Session 36 | s36 — see above |

Fixed generally, not case by case: `archivist.MISREAD_APPEARANCES` maps a session
number to the pages the export puts in it that the recording does not support,
and `Ledger.appearances()` drops them. Each entry carries its ruling. All three
pages are now clear of the session they were never in.

### A defect of my own, shipped and now fixed

Moving the accept table out of `factguard.py` on 2026-09-14 left a **residual
`ACCEPT = {…}` literal 756 lines long below the new loader**, which silently
overwrote it. So `factguard` went on reading the old Python literal while
`acceptcheck` read the JSON, and the two drifted apart for three commits —
including the commit that retired the 14 dead reasons, which therefore **had no
effect on the gate at all** when I reported it done. The splice that extracted
the table had searched for the first column-0 `}`, which closed `ACCEPT_ALL`, not
`ACCEPT`.

Removed the literal; `factguard` now reads the JSON, and the 14 retirements and
the two new Aoi reasons are all genuinely in force. Gates re-run and pass with
the loader actually in effect.

`acceptcheck` now **cross-checks that factguard's loaded table is the same table
as the file**, and fails if they differ. Regression-tested by injecting a drift:
the check exits 1 and names the divergent files.

**Method note.** "The gate passes" is not the same as "the gate is reading what I
changed." When a config moves, prove the consumer picked it up before reporting
the move done — this is the same failure as reporting `build_site` OK at s30
without checking the exit code, one level further in.

## Audit: every export-invented identification, checked for the same residue

Done mechanically against an enumerable set rather than from memory. **Every
deliberate removal in this pass has an accept-table entry**, so the accept table
is the list of names the pass struck. Cross-referenced each accepted token
against the entity page titles: **13 accepted tokens are the title of a real
page**, meaning a person or place the pass removed from a session's prose.

Three of the thirteen still carried the residue — the page went on listing a
session its subject was never in. The other ten were already clear.

| Page | Listed | Verdict |
|---|---|---|
| Akodo Atsushi | s19 | **Misplaced.** The hostile exchange over the journals was with the War College quartermaster, whom the 2025-09-01 recording never names. Atsushi is a different Lion; his own entry puts him at a tea house with Kitsu Takeko. |
| Tonbo Higuchi | s33 | **Misplaced.** The export thought he was the possessed novelist and put him in the exorcism. He is Tonbo Kuma's go opponent, met once in s32 and excused from the board. |
| Mantis Captain | s32 | **Not misplaced — duplicated.** He was there. He has been named since s31, and the role page is an empty placeholder beside Captain Kubota's. |

The first two are now in `MISREAD_APPEARANCES`. The third is a different defect
and needed a different fix.

### The wider sweep, and five split identities

The accept table only catches names the pass had occasion to *remove*. A name the
prose never mentioned could still be sitting in a session on the export's word
alone. So, separately: for every session, every page the export puts in its cast
that the corrected source never echoes — and of those, the pages where **that is
true of every appearance they have**, which is the signature of a page existing
on export assertion alone. 49 pages.

Most are a different defect again: the export minting a page for a role or a noun
(`Tea Mistress`, `Unicorn Duelist`, `Three Unidentified Figures`, an item called
`Family`, another called `Quack`). But five were **one person split in two by a
mis-heard name**, each a thin page beside a fat canonical one:

| Export page | Is | Appearances before → after |
|---|---|---|
| Onohime | [[Onahime]] | 1 → Onahime 1→2 |
| Okoto Totori | [[Akodo Toturi]] | 1 → Toturi 8→9 |
| Lady Takeko | [[Kitsu Takeko]] | 1 → Takeko 6→7 |
| Torunako | [[Akodo Toronoko]] | 3 → Toronoko 8→11 |
| Mantis Captain | [[Captain Kubota]] | 1 → Kubota 1→2 |

Merged with `RENAMES` + `ALIASES` where the canonical page is the export's, so
content survives the merge; with `SUPERSEDED_BY_LOCAL` + `ALIASES` for `Onohime`
and `Okoto Totori`, whose canonical pages are local and where a rename collides
with the duplicate check. All five duplicates are gone and every appearance
landed on the right person.

### What is left, and not taken

**45 pages had no appearance the corrected sources echo.** Worked through
individually — see the section below. The short version: the seam was not a seam.

## Working through the 45 — the seam was not a seam

Each of the 45 pages checked against the **recordings**, not the corpus. The
result overturns the premise: the "no echoed appearance" signal was mostly
measuring that the corrected prose is terser than the export, not that the export
invented anything. **Not one of the remaining pages is demonstrably invented.**

Three rounds of checking, because the first two were not good enough:

1. A phrase search for each title across all 73 recordings. Too loose — several
   pages "matched" on a single common word (`elemental`, `physician`, `matsu`),
   which proves nothing.
2. That left five with no hit at all. Two of those are untestable rather than
   unsupported: `Matsu Seishi` (s38) and `Miya estates` (s39) sit in sessions
   that **have no recording**. Absence of evidence, and the record says so.
3. The other three searched inside their own session's recording, allowing for
   the transcriber's spacing. All three are there: **`motososa`** in the
   2025-06-16 recording, **`akio`** in the 2025-10-06 one, **`snow field`** in
   the 2025-06-23 one. Moto Sosa, Shosuro Akio and the Open Snowfield are real;
   my matcher was wrong, not the pages.

### What the sweep did turn up

**A sixth split identity.** `Lady Matsu` is an empty placeholder with one
appearance, beside [[Matsu Tsuko]], who has content and is the Matsu daimyō. The
recordings use the two interchangeably — *"the Lady Matsu, Lady Daimyō Matsu"* —
and put her in command of the Lion host. Merged.

**A conflated location.** The export's `City Between the Rivers` page opens by
calling it *"also known as the City of the Rich Frog."* It is a different city:
the 2025-11-10 recording routes the party **from** the City of the Rich Frog
**to** it and on toward the Golden Yurts of the Ide, and following the river
north from there approaches Battle Maiden Castle. Replaced with a local page that
says what the recording says.

**Three facts my own rewrites had dropped**, all recovered from the recordings
while checking pages I suspected of being artefacts:

- **Monban's katana is named.** I read *"I will draw family the blood-bound
  blade"* in the s33 transcript as garble and left it out. It is not garble — the
  2026-05-04 recording says it twice, once as *"my katana. Uh, Family, the
  blood-bound blade."* The blade is [[Family]]. Restored to s33.
- **Matsu Tsuko commands the Lion army** at s35, and the party knew it when they
  set out — *"the Lady Matsu has control of the army right now… ninety-nine per
  cent odds Lady Matsu's there. She wouldn't miss a good fight. Certainly not one
  her own family started."* Restored.
- **There were three figures in the boat at s36, not one.** I wrote one. The GM
  says *"there's three of them to your eyes"* — to a man who had just failed to
  clear the intoxicated condition, which the record now notes rather than
  resolves.

**One page whose framing is wrong but whose subject is real.** `First Enemy
Blood` was filed as *"a faction within Rokugan, represented by Bayushi Monban."*
Taken up separately below, on the owner's note that the phrase is Monban's and
that what it refers to is not yet settled.

### Method note

Three of the five "not found" results were my search being wrong, and I nearly
reported them as fabrications. A negative result from a matcher is a claim about
the matcher until it has been tested the other way. Check the tool before
indicting the data.

## "First enemy blood" — the evidence, and a question left open

Owner's note, 2026-09-14: the phrase is one Monban uses and **what it refers to is
not yet settled**. So this gathers what the recordings show and stops there.
Nothing in the chronicle should harden past it.

**22 occurrences across 14 of the 73 recordings**, and they are two different
things.

### "The first enemy" — settled, and already right in the corpus

A plain noun phrase for the power beyond the Wall, used by several speakers, not
only Monban:

- *"These aren't the enemy. The first enemy is the enemy. My skills are a
  mahō-tsukai killer."* (2025-04-21)
- *"They're literally fighting the first enemy. They need our help."* — of the
  Wall (2025-11-10)
- *"the Sword of Hiruma has been stolen by servants of the first enemy"*
  (2025-11-10), which s27 already records
- *"raised activity in Shimanen Forest of first enemy minions of **the Foolish
  One**"* (2025-11-10)

### "First enemy blood" — a form of address, never a body of people

Every use attaches it to a **relationship word**, and nobody but Monban says it:

| Recording | Said of | Form |
|---|---|---|
| 2025-04-28 | Akodo Akihito | *"he is our brother and first enemy blood"* |
| 2025-09-01 ×2 | Akodo Akihito | *"My brother in First Enemy Blood"* |
| 2025-10-06 | Akodo Akihito | *"a letter to my brother in First Enemy Blood"* |
| 2026-05-18 | the party | *"family, and first enemy blood hug"* |
| 2026-07-13 | Shiba Midori | *"my big sister and first enemy blood"* |
| 2026-07-20 | Shiba Midori | *"My big sister in first enemy blood"* |
| 2026-08-24 | Akodo Akihito | *"[brother] in first enemy blood"* |
| 2026-09-07 | a Crab, shown the demon wound | *"We are family, you and I. Family and first enemy blood."* |

**The nearest thing to an explanation** is 2026-08-24, where he puts it as a
question first: *"We have shared battle with the first enemy, have we not? Just
like your cousin. My brother in first enemy blood."*

The chronicle already reads that as kinship claimed through having stood against
the Shadowlands together — s54 says so outright, of the Lion niece who is no
relation to him by blood and calls him uncle anyway. That reading fits all eight
uses. **It is still a reading, not a ruling**, and it does not say whether the
phrase names an oath, an order, something Kuni, or simply a way of speaking.

### The export page was not about the phrase at all

`Factions/First Enemy Blood.md` is a summary of the s24 arbitration — diamond
mines, the Castle of the Swift Sword, forgery, the letter condemning the *"least
of the Bayushi"* — filed under a phrase that appears nowhere in any of it, and it
**repeats the invented mines claim the pass struck at s12**. A confabulated page
wearing a real phrase as a title.

Superseded. The local replacement is filed as **lore, not faction**, lists the
usage above, and says in terms that the referent is held open on the owner's call.

## The demon wound and the Onahime bargain — same treatment

Gathered across all 73 recordings: **19 mentions of the wound in 9 recordings, and
Onahime in 10** (spelled Onahime, Onohime and Onihime by the transcriber, one
person). Unlike "first enemy blood", most of this **is** settled — the
2026-08-10 recording, which is session 52, has Monban explain the whole thing
unprompted when a companion asks whether it is Shadowlands taint or mahō.

### What was already right

s52 carries the bargain accurately and well: masks to enter [[Jigoku]], she kept
him alive and brought him out, what she asked was to take a piece of him with her
when she left, and she is not an evil thing. s5 carries the wound itself — a scar
that **rings his whole neck**, which lit red and burned when [[Matsu Tomoe]]
reached for it without touching it, and his answer that he had walked that place
and returned whole, *judged worthy by he who makes those choices*.

### What the same recording had and the record did not

- **The wound carries three characters.** One [[Onahime]]'s, one the
  [[Lady of Decay]]'s, and **a third at the back** — he began to describe it and
  did not finish, and nothing else in 73 recordings returns to it. Held open, the
  same way "first enemy blood" is held open.
- **The mechanism behind the coughing.** Certain kihō bring Onahime up whether he
  means it or not; spending more of them afterwards brings the Lady of Decay out
  properly, *"and I'll stop coughing and getting sick again."* That ties together
  a thread running from s33 — where calling her sets the wound burning and starts
  him coughing "the way he had not coughed in weeks" — and it was never stated.
- **He was eaten and he exploded** getting through Jigoku, and came out anyway.
- **He named the risk himself**, unprompted: to anyone who does not know what they
  are looking at, all of this looks exactly like a man possessed by an evil
  spirit. That is his reading, not an accusation somebody made.

All four restored to s52, with Learned bullets for the Lady of Decay and the
wound.

### Two pages written

**`The Demon Wound`** (lore) — the collar scar, the three characters and the
unfinished third, what makes it burn (spiritual working, calling the Lady of
Decay, standing over water infused with negative energy), what it costs him
mechanically, and who he has deliberately shown it to.

**`Onahime`** rewritten from four thin lines. It ended *"Something bearing her
aspect now speaks and shows through him"* — a hedge written before the
explanation existed. It now carries the bargain, how she manifests (blackness
from the left of his face ringed like a snowflake, a second shape off his
shoulders and head, half a demon and half a handsome man with a wicked smile,
and a woman laughing childishly because she is enjoying herself), and the witness
problem: *"The lady Doji is mine, and Onahime will have her doom"* — screamed in
a tent, seen by [[Shiba Midori]] and [[Kakita Kazumi]] and possibly
[[Ikoma Tadayoshi]], while [[Doji Setsuna]] was knocked down before the change
finished.

### One thing checked and deliberately not treated as a table secret

The s33 recording has *"they didn't know that their buddy had signed a demon
contract. Nobody knew, damn it… nobody's allowed to know about that."* Read in
context that is **in-fiction**: the players are saying it to each other, openly,
about what Rokugan does not know. It is a character secret, not a table one, and
the 2026-05-04 notes track it as an escalating witness problem rather than
something concealed from the group. Recorded as "no one in the Empire knows what
he signed," which is what the pass has held since s33.

## Open questions — revisit after the pass

- **Export session dates run a day late.** For 29 of the 35 export-era sessions
  the recording is dated the day before the Archivist's `date:`; six match. Not
  corrected — it moves every session page's date.

- **`unknown:` cannot gate anything new in sessions 1–39.** `Ledger.appearances()`
  builds a session's cast from the export and only falls back to the rewrite when
  the export has nothing, so an entity the Archivist never heard of never enters
  the ledger and never gets marked *apart*. Hit this with `The Blue Demon` in s7;
  the front-matter line is kept as the correct adjudication and the prose does the
  work. Fix would be to union the two sources rather than prefer the export.

- ~~**`factguard.ACCEPT` lives in this unversioned folder.**~~ **RESOLVED
  2026-09-14.** The table is now `sources/factguard-accept.json` in the site repo,
  on the same side of the line as `sources/` and for the same reason. This log
  lives at the repo root beside `REWRITE.md`, which is the existing precedent for
  an unpublished pass log. `scripts/factguard.py` loads the JSON;
  `scripts/acceptcheck.py` gates it.

  Extracting it surfaced something the old checker could not see: **14 per-file
  reasons were shadowed by entries later promoted to `all`** — `shoshuro aishi`
  across s12, s13 and s26, and `kitsu yui` / `yui` / `yui s` across s14 to s18.
  Nothing was lost by them, because those tokens are still accepted via `all`;
  the per-file text was simply dead and read as live.

  **Removed on the owner's call, 2026-09-14.** Checked first: the eleven Kitsu
  Yui entries only restate the global merge reason. The three `shoshuro aishi`
  ones carried real file-specific reasoning — the invented mines claim that the
  s12 and s13 Setsuna sections rested on, and the s26 duplicate ledger key — but
  this log already records all three at greater length, in the s12 and s26
  sections, so the accept entries were the redundant copy rather than the record.
  They are in git history either way, which is the point of having versioned the
  table first. 183 per-file tokens across 36 files became 169 across 35.

- **Onahime / Kuni Wardens** said the Hunter visages were painted on Monban's
  *mask*. The s6 recording has him take the mask off to show them painted on his
  *face*. Both pages corrected; check nothing later contradicts it.
