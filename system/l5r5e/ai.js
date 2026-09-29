// system/l5r5e/ai.js — AI suggestions for the creator's narrative answers. OFF by default.
//
// Ported from the pregens archive's creator (sortilege-l5r5e-pregens, assets/creator.js), whose
// prompts were tuned across several of the owner's audits: third person, plain register, the
// machine-prose tics banned by name, one question's book walkthrough as reference, the pick a
// question also grants (questions 9–12) named so the answer produces it, earlier suggestions
// listed so the next one differs, and one retry when a simile guesses at a feeling. The prompt
// text below is the archive's, verbatim.
//
// It is enabled from the GM's Settings pane (gm/; system/l5r5e/settings.js): an Anthropic API key, a model, and a switch.
// All three live in this browser's localStorage only — nothing is committed, synced or sent
// anywhere but api.anthropic.com — so the creator offers suggestions in the browser where the
// GM set the key, and nowhere else. With no key, or the switch off, the creator shows no AI
// controls at all.
window.L5RAI = (function () {
  const D = window.L5RData;
  const G = () => window.L5RChargen;
  const LS = 'sortilege.l5r5e.ai';
  const MODELS = [
    ['claude-haiku-4-5-20251001', 'Haiku 4.5 — what the prompts were tuned on'],
    ['claude-sonnet-5', 'Sonnet 5'],
    ['claude-opus-5-5', 'Opus 5.5'],
  ];
  function settings() {
    let s = null;
    try { s = JSON.parse(localStorage.getItem(LS) || 'null'); } catch (e) { s = null; }
    return Object.assign({ enabled: false, key: '', model: MODELS[0][0] }, s || {});
  }
  function saveSettings(patch) {
    const s = Object.assign(settings(), patch);
    try { localStorage.setItem(LS, JSON.stringify(s)); } catch (e) { /* private mode */ }
    return s;
  }
  const enabled = () => { const s = settings(); return !!(s.enabled && s.key && s.key.trim()); };

  let C = null; // the draft being answered (set by the creator on each call)
  const pickName = (kind) => { const id = C && C.pec && C.pec[kind]; const e = id && D.entity(id); return e ? e.name : null; };
  // what an advantage says, as plain text, from its entity
  function ruleTextFor(name) {
    const e = D.all().find((x) => x.name === name && G().PEC[G().kindOf(x) || '']);
    if (!e) return '';
    const out = [];
    const walk = (v) => { if (v == null) return; if (typeof v === 'string') out.push(v); else if (Array.isArray(v)) v.forEach(walk); else if (typeof v === 'object') { if ('s' in v) out.push(v.s); if ('value' in v && typeof v.value === 'string') out.push(v.value); if (v.body) walk(v.body); if (v.items) walk(v.items); } };
    (e.props || []).forEach(walk);
    (e.blocks || []).forEach(walk);
    (e.rules || []).forEach((r) => out.push(G().rule(r).text));
    return out.join(' ');
  }

  /* ─────────── the archive's prompts, verbatim from here to ANGLES ─────────── */
  var VOICE =
    "Write in the third person, about the character. Use their name, or they/them " +
    "if no name is given. Never write \"you\" or address the player.";
  var SHAPE =
    "One or two sentences, at most 200 characters. Give the sentence itself and " +
    "nothing else: no preamble, no framing, no quotation marks, no trailing gloss.";
  // "Grave and poetic" was the old instruction and it is what produced the
  // over-written results. Ask for a colleague's account, not a narrator's.
  var REGISTER =
    "Plain and concrete. Write the way someone who works with them would " +
    "describe them to a stranger — not the way a story would introduce them. " +
    "Human scale: one person, one place, one incident. No grand totals, no " +
    "sweeping spans (\"three provinces\", \"a hundred men\", \"all his life\"); " +
    "one specific thing is more interesting than a large vague one.";
  var TENSION =
    "Give it some tension, but make it a fact rather than a mood: something that " +
    "costs them, that they are bad at, that contradicts what they say they are, " +
    "or that has not been settled yet. Do not reach for atmosphere.";
  // Named individually, because naming the exact tic works and asking for
  // "good writing" does not.
  var AVOID =
    "Avoid the house style of machine-written prose. In particular, never end a " +
    "sentence with a detached participial or appositive flourish — the " +
    "\", asking nothing of the spirits but their names\" move, or " +
    "\", her hands still steady\", or \", knowing what it would cost\". If the " +
    "sentence works without a trailing clause, it is finished; stop there. " +
    "Never speculate about an inner state with a simile clause. That means no " +
    "\"as if\", no \"as though\", and no \"like she/he/they \u2026\": " +
    "\"as if the weight changes under observation\", \"as if she hasn\u2019t " +
    "noticed\", \"like she\u2019s swallowing something down\". It is the " +
    "trailing flourish wearing a simile, and banning only one of its wordings " +
    "gets you the others. State what happens and let the reader draw the " +
    "inference. A plain comparison of one thing to another is fine \u2014 " +
    "\"a scar like a fishhook\" \u2014 it is the guess at what someone is " +
    "feeling that is banned. " +
    "Also do not use: the \"not just X, but Y\" or \"more than X — Y\" " +
    "construction; a dash or colon pivot carrying the point at the end; three " +
    "abstract nouns in a row (duty, honor, sacrifice); opening on a participial " +
    "clause (\"Having served…\"); a closing clause that restates the sentence in " +
    "grander words; the words weight, quiet, echo, whisper, tapestry, testament, " +
    "navigate, delve, resonate, unwavering, steely, haunted, or \"speaks volumes\". " +
    "Do not restate the question. Do not explain the answer after giving it. " +
    /* Counted across 29 finished characters: these are the shapes the
       suggestions reached for over and over, so they are named the way the
       trailing flourish is. The nouns were always specific; the sentence was
       always the same one. */
    "Six more, which are this tool's own habits and are banned by name. " +
    "First: the hands. Do not put a character's inner life in their hands, " +
    "fingers, fingernails, knuckles or jaw — no hands going still, finding a " +
    "table edge, moving to sleeves, tightening, or stained and hidden; no jaw " +
    "tightening. Twenty-seven answers in this archive did one of those. Hands " +
    "are allowed only when they are the actual subject: a smith's burns, a " +
    "missing finger. Second: \"not X, but Y\" in any wording — \"not " +
    "fidgeting, but the precise adjustments a puppeteer makes\" — the ban " +
    "covers the bare form as well as \"not just\". Third: a mid-sentence " +
    "dash that renames what was just said (\"eats theirs first — a scout's " +
    "habit that\u2026\"). Say it once. Fourth: the unawareness coda — \"and " +
    "they do not seem aware they are doing it\", \"she never explains it\", " +
    "\"she does not file them even\". Whether they notice is not the answer. " +
    "Fifth: three -ing clauses in a row (\"checking the fraying, retying the " +
    "knots, running his thumb\u2026\"). Two is a list; three is a tic. Sixth: " +
    "the cost clause — \"which means\", \"which costs\", \"but cannot\", " +
    "\"but turns down\" — bolted on to make a virtue into a flaw. Tension is " +
    "asked for above; a formula for it is not. " +
    /* Four more, named on the Blood of the Lioness audit (2026-09-07), where
       the owner rejected each by quoting it. Quoting the rejected shape is
       what has worked; adding adjectives to the ban has not. */
    "Four more, rejected by name. The observing-tell clause — showing that a " +
    "character reads people by having them watch a face: \"to watch how " +
    "Junnosuke's face moves before he speaks\", \"reads a room's currents\". " +
    "The closing observation — a two-word sentence tacked on after the fact: " +
    "\"She has noticed.\" The comparison tail — \"rather than ask a Lion for " +
    "the key\": say what he did, not what he did instead of. The aphorism — a " +
    "balanced line that sounds like a saying: \"the first thing anyone sees and " +
    "the last thing they mention\". Plain declaratives instead, every time. " +
    "One sentence unless the question says otherwise, and shorter is better: " +
    "the strongest answers in this archive are eight to twenty words. " +
    /* Seven more, named on the Mask of the Oni audit (2026-09-07), again by
       the owner quoting the rejected line. */
    "Seven more, rejected by name. The withheld-secret clause — a relative " +
    "clause that gestures at a secret instead of stating a fact: \"in the " +
    "winter she does not speak of\", \"the years she does not name\". An " +
    "abstract noun doing the feeling — \"feels the choice move from her hands " +
    "into theirs\", \"so the choosing is no longer his\": say what she does. " +
    "The comparative escalation tail — \"which costs her more than the " +
    "exhaustion ever did\". The antithesis pair — \"maps them on paper while " +
    "she maps them in her body\". The doom tail — a future death appended to " +
    "a present fact: \"the passages she will die in\". Negated action as " +
    "characterisation — \"does not warn her away\", \"has never once asked\", " +
    "\"does not seem to know she is doing it\": what someone pointedly does not " +
    "do is not a portrait. Polysyndeton to a reveal — and… and… and… building " +
    "to the last clause. What passes: a person, a concrete act, a place, a time.";
  /* One rejected shape and one good one. They are deliberately about different
     characters: an earlier version used the same character for both, and the
     answers for that archetype came back as paraphrases of the good example
     rather than as their own sentence. */
  var EXAMPLE =
    "For calibration. A rejected answer, for a diviner: \"Nergüi traced a " +
    "murderer's path through three provinces by reading the bones of her victims " +
    "in Nagiko's presence, asking nothing of the spirits but their names.\" — " +
    "inflated scale, an ornamental verb, and a trailing flourish that adds " +
    "nothing. A good answer, for an unrelated character, a quartermaster: " +
    "\"She signs for grain she knows is short and makes the difference up out of " +
    "her own stipend.\" — one incident, " +
    "ordinary scale, and the tension is a fact rather than a mood. Match the " +
    "second in register, not in subject.";
  var STYLE = [VOICE, SHAPE, REGISTER, TENSION, AVOID, EXAMPLE].join(" ");

  /* Questions 9 to 12 ask a narrative question AND grant a mechanical pick, and
     the two are meant to be the same fact seen twice. The suggestion used to
     ignore the pick entirely — a character who had taken Blessed Lineage got an
     accomplishment about smuggling — so where a pick exists, the prompt names it
     and asks for the answer that produces it. Naming it, not describing it: the
     sentence should read as the deed, not as a gloss on the advantage. */
  function grants(kind, picked, want) {
    if (!picked) return "";
    // Give the model what the advantage actually says. Naming it alone was not
    // enough: a long concept note pulls hard, and a character whose concept is
    // loud about one difficulty got answers about that difficulty while holding
    // an unrelated adversity. The rules text plus an explicit precedence rule
    // is what makes the pick win.
    var rules = ruleTextFor(picked);
    var plain = rules
      ? String(rules).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()
      : "";
    return " This character has taken the " + kind + " \"" + picked + "\" for this " +
      "question" +
      (plain ? ", which reads: " + plain.slice(0, 600) : "") + ". " +
      "The sentence must be " + want + ", so that the " + kind + " reads as its " +
      "consequence. Use the concept notes for the texture around it — the people, " +
      "the place, the work — so that both show up in the same sentence wherever " +
      "they can. Where they pull apart, the " + kind + " they actually took " +
      "governs what the sentence is about, and the notes supply only the setting. " +
      "Do not name the " + kind + " itself and do not quote its rules text — show " +
      "it happening.";
  }

  var SETTING = "Legend of the Five Rings 5th Edition, a samurai drama RPG set in " +
    "the fantasy realm of Rokugan.";
  var PROMPTS = {
    giri: "You are helping create a character for " + SETTING + "\n\nWrite a single sentence describing this character's giri (duty/obligation to their lord). Giri is what they must do even at personal cost. It should be specific to their clan, school, and lord.\n\n" +
      /* Shape rules from the Blood of the Lioness audit, where four of nine
         giri were not duties: one was a want, one was a lord forbidding
         something, and the lord named in the field was absent twice. */
      "A giri is a duty the lord SETS: name the lord, and say what they have " +
      "tasked this character with. It is not a want dressed as a duty (\"must " +
      "discover how the previous commander died\" — that is a ninjō), and not a " +
      "prohibition (\"must keep his duelists from challenging her\" is the lord " +
      "forbidding, not tasking; if the lord has a standing rule, state it as " +
      "the lord's rule). If the character reports to someone other than their " +
      "lord — a commander they are placed under — name both.\n\n" + STYLE,
    ninjo: "L5R 5e character creation. Write a single sentence describing this character's ninjō (personal desire). The ninjō should sit in tension with their giri — something they want for themselves that conflicts with their duty.\n\n" +
      "A ninjō is a WANT, stated as one: \"wants to…\". Not a situation, not a " +
      "suspicion (\"suspects a blade was Scorpion-forged\" is a case file), and " +
      "not the giri said again with feeling. Give the want a face where you " +
      "can — a person in this party or already in the character's life — or an " +
      "object somebody has and will not give up. Rejected: \"wants to keep the " +
      "infirmary stocked so thoroughly that no soldier ever dies of a wound she " +
      "could have treated\" (it restates the duty). Accepted: \"wants to forge " +
      "the blade Akodo Tsanuri carries into the field. Tsanuri carries his " +
      "family's blade, and will die holding it before he sets it down for a " +
      "Kakita's.\"\n\n" + STYLE,
    standout_quality: "L5R 5e character creation. Write a single sentence " +
      "naming and briefly framing the standout quality — a memorable trait or " +
      "moment — that earned this character their +1 ring increase. Concrete " +
      "and unmistakable.\n\n" +
      /* Every suggested answer here was a strength with its cost bolted on:
         "…, which means she now spends entire study sessions recalculating",
         "…, which costs him tournaments but makes him", "…, but cannot hear
         when someone is lying". A good device once; as a template it makes
         everyone the same person.

         NOT YET EFFECTIVE (2026-09-06). The ban below is by name and it came
         back anyway on the first character built after it: Kaiu Anzu, "can
         read a ruin's load-bearing bones and predict where it will fail long
         before the collapse, BUT SHE CANNOT look at what the Shadowlands did
         to make those bones brittle". Flagged for a follow-up pass once a few
         more characters exist, so it is not tuned on one sample (owner,
         2026-09-06). The fix to try is the one that worked for the trailing
         participial flourish: quote the rejected shape as an example rather
         than prohibiting it, since a named ban has now failed twice. */
      "The quality itself is the answer. Do not append the price of it: no " +
      "\"which means\", no \"which costs\", no \"but cannot\", no \"but " +
      "turns down\". If it is genuinely double-edged, that can show in what " +
      "the thing is, not in a clause explaining the downside.\n\n" + STYLE,
    clan_relationship: "L5R 5e character creation. Write a single sentence describing how this character carries, or resists, their clan's ideals. Specific to the clan they belong to.\n\n" + STYLE,
    /* Question 14 asks what people NOTICE, and the book's answer is a
       deviation from the norm rather than a portrait — "slight oddities of
       appearance to trivial mannerisms", recorded under Personality, Habits
       and Quirks, with "chewing one's lip when nervous" as its own example.

       Asking for build, bearing, voice and dress got general impressions back:
       composed, watchful, plainly dressed. Those are conclusions a stranger
       draws, not things a stranger can see, so the answer said nothing anyone
       could point at. Naming that failure with examples is what works here;
       asking for "something concrete" does not.

       It also asked for the accoutrement, which is its own field on this same
       step, so the sentence was spent answering the next question. */
    first_impression: "L5R 5e character creation. Name the one thing a stranger " +
      "notices first about this character. It should veer from what is expected " +
      "of someone of their clan and station — that is why it gets noticed at " +
      "all.\n\n" +
      /* The question was being answered with a habit you could only learn by
         watching someone for an hour: eating from other people's bowls,
         stopping mid-sentence to reread a ledger, nodding along to a
         fortification survey and then contradicting it. Every one of those
         needs to be in the room with them for a while. The question is a
         stranger's first look. */
      "THE TEST: three seconds, across a room, before a word is spoken. If " +
      "seeing it needs a conversation with them, a shared meal, or watching " +
      "them more than once, it is the wrong answer to this question. Anything " +
      "that begins \"when someone…\" or \"when they…\" is describing a " +
      "habit, not a first sight.\n\n" +
      "What does qualify: build, height, bearing, the state of their face or " +
      "hair, a scar or a mark, how they hold themselves, how they move across " +
      "a room, how their voice sounds to someone they are not talking to.\n\n" +
      "It must be observable. Not an impression, a bearing, or an air: " +
      "\"composed\", \"watchful\", \"an unsettling stillness\", \"carries " +
      "herself with quiet authority\" are all conclusions a stranger draws, not " +
      "things they see. Give the thing that would make them draw it.\n\n" +
      "Do not name anything they carry or wear. That is a separate answer on " +
      "this same question.\n\n" +
      "Describe the thing; do not assert that it is visible. \"A real visible " +
      "flinch\", \"a noticeable habit of\", \"an observable tendency to\" are " +
      "the instruction leaking into the answer — if the reader can see it, " +
      "saying so is wasted words.\n\n" + STYLE,
    accoutrement: "L5R 5e character creation. Name one distinctive thing this " +
      "character carries or wears most of the time, in at most two short " +
      "fragments: the object, then — only if there is one — a single concrete " +
      "particular. Exactly this shape: \"Commander's insignia. Hangs on a braided " +
      "cord.\" \"Rice bowl. Repaired with kintsugi.\" \"Brass compass.\" No verb of " +
      "wearing or keeping, no clause about what it means to them, no second " +
      "detail. Rejected: \"She wears a commander's insignia on a cord she has " +
      "rebraided seventeen times, each time tighter than the last.\"\n\n" + STYLE,
    stress_reaction: "L5R 5e character creation. Write a single sentence " +
      "describing what this character does when they are under more pressure " +
      "than they can carry. Visible, physical, particular to them.\n\n" +
      /* Fifteen of twenty-nine answers opened on the literal clause "When …,"
         and four used the phrase "past his composure" — the mechanic's own
         name pasted into the fiction. */
      "Do not open the sentence with \"When\". Do not use the word " +
      "\"composure\": that is the game's term for the mechanic, not something " +
      "anyone would say about a person. Do not reach for the jaw, the hands, " +
      "or stopping mid-sentence — three answers here already stop mid-" +
      "sentence.\n\n" +
      "Aim at what the people around them have to deal with, not at the tell " +
      "itself: what they start doing, stop doing, or make everyone else do.\n\n"
      + STYLE,
    parent_opinion: "L5R 5e character creation. Write a single sentence reporting a parent or guardian's opinion of this character — what they are proud of, frustrated by, or worried about. Report it in the third person; do not write it as the parent speaking.\n\n" + STYLE,
    accomplishment: function () {
      return "L5R 5e character creation. Write a single sentence naming this " +
        "character's greatest accomplishment so far — a deed, not a trait, with a " +
        "place or a person in it." + grants("distinction", pickName("distinction"),
          "the deed, circumstance, or history that this distinction records — " +
          "some are earned and some are inherited, so do not force it into a deed " +
          "if it is not one") + "\n\n" + STYLE;
    },
    challenge: function () {
      return "L5R 5e character creation. Write a single sentence describing what " +
        "holds this character back the most in life. A standing difficulty they " +
        "carry, not a mood." + grants("adversity", pickName("adversity"),
          "the difficulty it names, as it shows up in their life") + "\n\n" + STYLE;
    },
    peace: function () {
      return "L5R 5e character creation. Write a single sentence describing the " +
        "activity that most makes this character feel at peace — something they do " +
        "for themselves, unrelated to duty." + grants("passion", pickName("passion"),
          "that activity, and what it looks like when they are doing it") +
        /* Thirteen of twenty-six were the same short film: a place, a posture,
           an object in the hands, a small repeated action, a coda. */
        "\n\nName the thing that settles them. Do not stage it as a scene: no " +
        "sitting alone somewhere after everyone has left, no object warming in " +
        "their hands, no time of day. The activity, and at most what it gives " +
        "them.\n\n" + STYLE;
    },
    fear: function () {
      return "L5R 5e character creation. Write a single sentence describing the " +
        "concern, fear, or foible that troubles this character most." +
        grants("anxiety", pickName("anxiety"),
          "that fear, and where it costs them") + "\n\n" + STYLE;
    },
    past: "L5R 5e character creation, Path of Waves. This character has no lord; a past replaces giri. Write a single sentence naming what drives them and what it costs — an obligation, a pursuer, or a choice that still follows them.\n\n" + STYLE,
    known_for: "L5R 5e character creation, Path of Waves. Write a single sentence describing what this character is known for where they have travelled, and to whom.\n\n" + STYLE,
    prized_possession: "L5R 5e character creation, Path of Waves. Write a single sentence about the one possession that matters most when everything they own fits in a pack — what it is, and why this one.\n\n" + STYLE,
    group_history: "L5R 5e character creation, Path of Waves. Write a single sentence of shared history between this character and one other member of their group, answering the prompt they chose.\n\n" + STYLE,
    raised_by: "L5R 5e character creation, Path of Waves. Write a single sentence describing who raised this character and how they regard it.\n\n" + STYLE,
    mentor_relationship: "L5R 5e character creation. Write a single sentence describing the relationship between this character and a mentor — what they were taught, and at what cost.\n\n" + STYLE,
    relationship_person: "L5R 5e character creation. Write a single sentence about " +
      "one person in this character's life: who they are to each other, and what " +
      "sits between them. A rival, an ally, a relative, a creditor, a former " +
      "teacher — the relationship, not a description of the other person.\n\n" + STYLE,
    relationships: "L5R 5e character creation. Write a single sentence naming one or two people who matter to this character — a rival, an ally, a family member — and what stands between them.\n\n" + STYLE,
    death: "L5R 5e character creation. Write a single sentence describing how " +
      "this character expects to die — what they believe is coming, not a scene " +
      "the GM would run.\n\n" +
      /* Fourteen answers were the same idea: the character dies of their
         defining flaw, mid-task, with the irony spelled out. And all of them
         were shot from outside the character, in the third-person present,
         which is a camera rather than a belief.

         NOT YET EFFECTIVE (2026-09-06). Two characters built since: Asako
         Yukitsuna, "will die at her desk in the Phoenix archives,
         mid-sentence in a report, because she finally found the
         contradiction"; Kaiu Anzu, "will die certifying something as sound
         when the stones have already failed, and she will know it as it
         happens". Both dodge the letter of the bans below -- neither says
         "dies …ing" -- and keep the idea whole: the ironic death of their own
         flaw, narrated from outside. Flagged for a follow-up pass once a few
         more characters exist (owner, 2026-09-06); the fix to try is a quoted
         rejected example rather than another prohibition. */
      "It is their expectation, so it can be wrong, ordinary, or have nothing " +
      "to do with their flaw. Do not write the death scene: no \"dies " +
      "…ing\", no present-tense staging (\"bleeds out in an archive " +
      "basement\", \"collapses in the wings\"), and above all do not have " +
      "them die of the very thing they are bad at, with the irony explained. " +
      "That was every answer in this archive and it makes each character a " +
      "moral about themselves.\n\n" +
      "What works: a plain expectation (\"on the field, commanding\"), a " +
      "resignation, a fear about the manner rather than the fact, or an " +
      "indifference. Their voice, not a narrator's.\n\n" + STYLE,
    "default": "L5R 5e character creation suggestion. " + STYLE
  };

  /* One of these is picked per call. They are ways in, not topics: the same
     fact looks different depending on whether you catch it as an incident, a
     habit, or something a third party noticed. */
  var ANGLES = [
    "a single incident, on a particular day, with someone else present",
    "a standing habit — the thing they do every time, not once",
    "what somebody else notices about them and has not said",
    "a workaround they have built, and what it costs to maintain",
    "the practical consequence at work, in the middle of their duty",
    "something that happens when they are alone",
    "a small thing they are unreasonably good or bad at because of it",
    "the way it shapes who they will and will not be in a room with"
  ];

  /* ─────────── end of the archive's prompts ─────────── */

  // this creator's field → the archive's prompt, and the question it answers
  const FIELDS = {
    standout: ['standout_quality', 4], giri: ['giri', 5], past: ['past', 5], ninjo: ['ninjo', 6],
    q7text: [null, 7], accomplishment: ['accomplishment', 9], challenge: ['challenge', 10], peace: ['peace', 11],
    fear: ['fear', 12], mentorText: ['mentor_relationship', 13], impression: ['first_impression', 14],
    acc: ['accoutrement', 14], prizedText: ['prized_possession', 14], stress: ['stress_reaction', 15],
    person: ['relationship_person', 16], parent: ['parent_opinion', 17], group: ['group_history', 17],
    raised: ['raised_by', 18], death: ['death', 20],
  };
  const promptKey = (f) => { const x = FIELDS[f]; if (!x) return 'default'; if (x[0]) return x[0]; return C.mode === 'core' ? 'clan_relationship' : 'known_for'; };
  const questionOf = (f) => (FIELDS[f] || [])[1] || null;
  const GUIDANCE_MAX = 4000;
  // the core's walkthrough of the question; Path of Waves and Writ of the Wilds print none
  function questionGuidance(f) {
    const n = questionOf(f);
    if (!n || C.mode !== 'core') return '';
    const g = (G().walkthrough(n) || {}).text || '';
    if (g.length <= GUIDANCE_MAX) return g;
    const cut = g.lastIndexOf('. ', GUIDANCE_MAX);
    return g.slice(0, cut > GUIDANCE_MAX / 2 ? cut + 1 : GUIDANCE_MAX);
  }
  // the character so far, as settled facts; the field being replaced is left out
  function characterContext(omit) {
    const b = [];
    const skip = (omit || '').trim();
    const add = (k, v) => { if (v == null || v === '' || (skip && String(v).trim() === skip)) return; b.push(k + ': ' + v); };
    const d = G().compute(C);
    const v = G().toSheet(C);
    const a = C.a || {};
    add('Mode', (G().MODES.find((m) => m.key === (C.mode || 'core')) || {}).title);
    add('Name', v.Name);
    if (d.clan) add('Clan', d.clan.name);
    if (d.family) add('Family', d.family.name);
    if (d.region) add('Region', d.region.name);
    if (d.upbringing) add('Upbringing', d.upbringing.name);
    if (d.school) add('School', d.school.name + (C.role ? ' (' + C.role + ')' : ''));
    b.push('Rings: ' + G().RINGS.map((r) => r + ' ' + d.rings[r]).join(', '));
    const sk = Object.keys(d.skills).filter((k) => d.skills[k]).map((k) => k + ' ' + d.skills[k]);
    if (sk.length) b.push('Skills: ' + sk.join(', '));
    b.push('Honor ' + d.honor + ', Glory ' + d.glory + ', Status ' + d.status);
    add('Standout quality', a.standout);
    add(C.mode === 'core' ? 'Giri (duty)' : 'Past', C.mode === 'core' ? a.giri : a.past);
    add('Ninjō (desire)', a.ninjo);
    add(C.mode === 'core' ? 'Clan relationship' : 'Known for', a.q7text);
    add('Paramount tenet', C.bushido && C.bushido.paramount);
    add('Lesser tenet', C.bushido && C.bushido.lesser);
    add('Greatest accomplishment', a.accomplishment);
    add('Greatest challenge', a.challenge);
    add('At peace when', a.peace);
    add('Troubled by', a.fear);
    G().peculiarityList(C, d).forEach((p) => add((p.kind ? p.kind.charAt(0).toUpperCase() + p.kind.slice(1) : 'Advantage') + ' (' + p.source.toLowerCase() + ')', G().withSubject(p.name, p.subject)));
    add('Mentor', [a.mentor, a.mentorText].filter(Boolean).join(' — '));
    add('First impression', a.impression);
    add('Accoutrement', [a.accName, a.acc].filter(Boolean).join('. '));
    add('Prized possession', [a.prized, a.prizedText].filter(Boolean).join(' — '));
    add('Stress reaction', a.stress);
    (C.people || []).forEach((p) => add('Relationship', [p.name, p.text].filter(Boolean).join(': ')));
    add('Starting item', C.item);
    add("Parent's opinion", a.parent);
    add('Shared history', a.group);
    add('Raised by', a.raised);
    if (v.Heritage) add('Heritage', v.Heritage);
    add('Vision of death', a.death);
    return b.join('\n');
  }
  // the latest earlier answer, named so the model does not continue it
  function previousAnswer(f) {
    const qn = questionOf(f);
    if (!qn) return null;
    const a = C.a || {};
    const core = C.mode === 'core';
    const rows = [[4, 'standout quality', a.standout], [5, core ? 'giri' : 'past', core ? a.giri : a.past], [6, 'ninjō', a.ninjo],
      [7, core ? 'clan relationship' : 'what they are known for', a.q7text], [9, 'greatest accomplishment', a.accomplishment], [10, 'greatest challenge', a.challenge],
      [11, 'what puts them at peace', a.peace], [12, 'what troubles them', a.fear], [13, 'mentor', a.mentorText], [14, core ? 'first impression' : 'prized possession', core ? a.impression : a.prizedText],
      [15, 'stress reaction', a.stress], [17, core ? "parent's opinion" : 'shared history with the group', core ? a.parent : a.group]];
    let best = null;
    rows.forEach((r) => { if (r[0] < qn && String(r[2] || '').trim() && (!best || r[0] > best[0])) best = r; });
    return best ? best[1] : null;
  }
  // the user turn, ordered by weight: facts, then the concept, then the question last
  function weightedContext(f, omit) {
    const facts = characterContext(omit);
    const qn = questionOf(f);
    const q = qn ? G().question(C.mode || 'core', qn) : null;
    const b = [];
    if (facts) b.push('WHAT THIS CHARACTER ALREADY IS. These are settled facts and the boundary your answer sits inside: do not contradict them. They are not the subject of the answer and not a prompt to continue any of them — several are answers to other questions, which have already been asked and are done.\n\n' + facts);
    if (C.concept) b.push('THE CONCEPT the player is holding for this character. This is where the answer\'s material comes from — the people, the places, the work, the trouble. Prefer it over anything you would otherwise invent:\n\n' + C.concept);
    const prev = previousAnswer(f);
    b.push('THE QUESTION YOU ARE ANSWERING' + (qn ? ', question ' + qn + ' of the twenty' : '') + '.' + (q ? '\n\n' + q.text : '') +
      '\n\nAnswer that question and only that question. In order of precedence: what this question asks governs what the sentence is about; the concept supplies the material it is made of; the settled facts constrain it and nothing more.' +
      (prev ? ' In particular, the character\'s ' + prev + ' above is the answer to the question before this one. It is context. Do not extend it, retell it, or make this answer a further episode of it — this question is about something else.' : ''));
    return b.join('\n\n---\n\n');
  }
  const SIMILE = /\b(as if|as though|like (?:she|he|they|it)\s+\w|the way (?:an?|the|she|he|they)\b)/i;

  function suggest(draft, field, sourceText, current, extra) {
    C = draft;
    const s = settings();
    if (!enabled()) return Promise.reject(new Error('AI suggestions are off. The GM enables them under Settings.'));
    let system = PROMPTS[promptKey(field)] || PROMPTS['default'];
    if (typeof system === 'function') system = system();
    if (extra) system = extra + '\n\n' + system;
    const seen = (C.ai_history && C.ai_history[field]) || [];
    const advice = questionGuidance(field);
    const preamble = advice ? 'The rulebook\'s own guidance for this question, for what it asks and what a good answer does. Use it to decide what the answer should be about; do not quote it, restate it, or answer in its voice:\n\n' + advice + '\n\n---\n\n' : '';
    let user;
    if (sourceText && sourceText.trim()) {
      user = preamble + 'Existing draft for context:\n' + characterContext() + (C.concept ? '\n\nThe concept the player is holding:\n' + C.concept : '') +
        '\n\nTHE PLAYER HAS WRITTEN THE ANSWER BELOW. This overrides every instruction about what to write about, including any advantage or disadvantage named above. Your job is only how it is written.\n\nTheir text:\n' + sourceText.trim() +
        '\n\nPut that into the register described in your instructions. Keep every specific they gave — names, places, objects, relationships, the actual claim. Do not add a fact they did not write, do not drop one they did, and do not change the subject. If it is already in the register, return it close to unchanged rather than finding something to alter.';
    } else {
      user = preamble + weightedContext(field, current) + '\n\nSuggest a single ' + promptKey(field).replace(/_/g, ' ') + ' for this character.' +
        '\n\nApproach it as: ' + ANGLES[Math.floor(Math.random() * ANGLES.length)] + '. Write that, rather than gesturing at it.' +
        (seen.length ? '\n\nYou have already offered these for this field and they were not taken:\n' + seen.map((t) => '> ' + t).join('\n') + '\nGive something different in substance. Whatever activity, object, place or person those used, do not use it again — a character has more than one part to their life, and the concept notes are a starting point rather than the only material. Rewording an answer above does not count as a new one.' : '');
    }
    const once = (note) => fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-api-key': s.key.trim(), 'anthropic-version': '2023-06-01', 'anthropic-dangerous-direct-browser-access': 'true' },
      body: JSON.stringify({ model: s.model || MODELS[0][0], max_tokens: 256, system: note ? system + '\n\n' + note : system, messages: [{ role: 'user', content: user }] }),
    }).then((r) => (r.ok ? r.json() : r.text().then((t) => { let m = t; try { m = (JSON.parse(t).error || {}).message || t; } catch (e) { /* plain */ } throw new Error('AI request failed (' + r.status + '): ' + String(m).slice(0, 200)); })))
      .then((d) => (d.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('').trim());
    // a simile that guesses at a feeling is asked for again, once
    return once(null).then((text) => {
      const m = SIMILE.exec(text || '');
      if (!m) return text;
      return once('Your previous attempt was rejected for writing "' + m[0] + '". Do not guess at what this character feels by comparing them to something. No "as if", no "as though", no "like she …", no "the way a … does". Write what happens and stop.').then((t) => t || text, () => text);
    }).then((text) => {
      if (!sourceText && text) {
        C.ai_history = C.ai_history || {};
        const list = (C.ai_history[field] = C.ai_history[field] || []);
        list.push(text);
        while (list.length > 4) list.shift();
      }
      return text;
    });
  }

  // ── the GM's Settings section (system/l5r5e/settings.js): the key, the model, the switch ──
  function renderSettings(box, redraw) {
    const { el, button } = window.VttRender;
    const s = settings();
    box.appendChild(el('div', { class: 'guidance-k' }, ['AI suggestions in the character creator']));
    box.appendChild(el('p', { class: 'muted small' }, ['Off unless switched on here. With a key and the switch on, the creator’s narrative answers (giri, ninjō, the accomplishment and the rest) offer a Suggest button: it drafts an answer in the third person from the character so far and the book’s walkthrough of the question, or rewrites what the player typed. The key is stored in this browser only and sent only to api.anthropic.com — so suggestions appear in the creator in this browser, not on a player’s device.']));
    box.appendChild(el('label', { class: 'set-row' }, [el('input', { type: 'checkbox', checked: s.enabled || null, onchange: (ev) => { saveSettings({ enabled: ev.target.checked }); redraw(); } }), ' Enable AI suggestions']));
    box.appendChild(el('div', { class: 'set-row' }, [el('span', { class: 'muted small' }, ['Anthropic API key']),
      el('input', { type: 'password', class: 'text wide', autocomplete: 'off', placeholder: 'sk-ant-…', value: s.key || '', onchange: (ev) => { saveSettings({ key: ev.target.value.trim() }); redraw(); } })]));
    const sel = el('select', { class: 'scope' }, MODELS.map(([id, label]) => el('option', { value: id, selected: id === s.model || null }, [label])));
    sel.addEventListener('change', () => saveSettings({ model: sel.value }));
    box.appendChild(el('div', { class: 'set-row' }, [el('span', { class: 'muted small' }, ['Model']), sel]));
    box.appendChild(el('div', { class: 'set-row' }, [
      el('span', { class: 'cond' + (enabled() ? ' ok' : '') }, [enabled() ? 'On' : s.enabled ? 'On, but no key' : 'Off']),
      s.key ? button('Forget the key', () => { saveSettings({ key: '', enabled: false }); redraw(); }, 'ghost tiny') : null,
    ]));
  }
  if (window.L5RSettings) window.L5RSettings.section({ id: 'ai', render: renderSettings });

  return { settings, saveSettings, enabled, suggest, FIELDS, MODELS };
})();
