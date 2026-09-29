// system/l5r5e/heritage-rules.js — what each heritage result obliges the player to settle.
//
// Ported from the pregens archive (sortilege-l5r5e-pregens, scripts/heritage_tables.py
// REQUIRES), where it was tested against every character the archive holds. The rules text
// stays the corpus's: this table names only the obligation an entry's EFFECT states in prose —
// "gain the Sixth Sense distinction", "reduce one ring by 1 to raise another", "add the
// heirloom to your starting items" — so the creator can ask for it and fold it into the sheet.
//
// Keyed by the heritage table's name and the entry's name, both as the corpus prints them.
// `sub` says how that entry's own SUB_TABLE ranges read; the default, "skill", is proved rather
// than assumed (every range has to name a core skill). build/check_chargen.py fails the build
// on an entry that neither parses nor appears here, and on a key here that names nothing.
//
// What a requirement means:
//   skill        +1 rank in `skill`, or one of `options`, or (from: school_starting_at_zero)
//                one of the school's starting skills the character has no ranks in
//   technique    learn one of `rank`, in `category` (or the rolled category, or an invocation
//                of the rolled ring)
//   peculiarity  gain `name`, or one of `options`; `subject` fills an open-ended entry
//   item         add `name`, or one of the rolled category; `held: false` for an heirloom
//                that exists but is lost
//   ring_swap    reduce one ring by 1 to raise another; never above `cap`
//   pick_one     exactly one of `options`, each a requirement in its own right
//   money        the entry pays instead of granting
// The file is one JSON literal after the `=`, so the build's check can read it as data.
window.L5RHeritageRules = {
  "CUSTOM_ITEMS": ["Omamori Boon of Fukurokujin"],
  "HEIRLOOM": [
    ["^a weapon", {"type": "weapon"}],
    ["^a set of armor", {"type": "armor"}],
    ["^a game set", {"type": "item"}],
    ["^a valued piece of art", {"type": "item"}],
    ["^(another item|some other item)", {"type": ""}],
    ["^a horse or (an)?other animal", {"free": "the animal"}],
    ["^a boat or estate", {"free": "the boat or estate"}],
    ["^the deed to", {"free": "the land"}]
  ],
  "REQUIRES": {
    "Samurai Heritage Table": {
      "Famous Deed": {"sub": "item_category", "requires": [
        {"kind": "item", "prompt": "Family heirloom", "category_from_sub": true, "qualities": {"player": 1, "gm": 1}}]},
      "Glorious Sacrifice": {"sub": "item_category", "requires": [
        {"kind": "item", "prompt": "Lost heirloom", "held": false, "category_from_sub": true, "qualities": {"player": 1, "gm": 1}}]},
      "Stolen Knowledge": {"sub": "technique_category", "requires": [
        {"kind": "technique", "prompt": "Additional technique", "rank": 1, "category_from_sub": true}]},
      "Imperial Heritage": {"requires": [
        {"kind": "peculiarity", "prompt": "Advantage", "name": "Blessed Lineage"}]},
      "Unusual Name Origin": {"requires": [
        {"kind": "pick_one", "prompt": "One of the two", "options": [
          {"kind": "ring_swap", "prompt": "Reduce one ring, raise another", "to": "any", "cap": 3},
          {"kind": "item", "prompt": "Item of rarity 6 or lower", "rarity_max": 6}]}]}
    },
    "New Samurai Heritages (Celestial Realms)": {
      "Associated with a Natural Disaster": {"requires": [
        {"kind": "peculiarity", "prompt": "Adversity", "name": "Whispers of Failure"},
        {"kind": "ring_swap", "optional": true, "cap": 3, "to": "any", "prompt": "Ring of the disaster"}]},
      "Mark of the Elements": {"requires": [
        {"kind": "ring_swap", "optional": true, "cap": 3, "to": "any", "prompt": "Ring of the element"}]},
      "Sacrifice": {"sub": "item_category", "requires": [
        {"kind": "item", "prompt": "The sacrifice", "category_from_sub": true, "qualities": {"player": 1, "gm": 1}}]},
      "Spirit of the Phoenix": {"sub": "peculiarity"},
      "Touched by the Fortunes": {"requires": [
        {"kind": "peculiarity", "prompt": "Distinction", "name": "Sixth Sense"}]}
    },
    "New Samurai Heritages Table": {
      "Ancestral Horse Line": {"sub": "item_name", "requires": [
        {"kind": "item", "prompt": "Warhorse", "name_from_sub": true, "name_suffix": " horse", "custom": true}]},
      "Heart of the Horse": {"requires": [
        {"kind": "item", "prompt": "Horse", "name": "Horse", "custom": true},
        {"kind": "peculiarity", "prompt": "Distinction", "name": "Karmic Tie"}]},
      "Knowledge Exchange": {"sub": "technique_category", "requires": [
        {"kind": "technique", "prompt": "Additional technique", "rank": 1, "category_from_sub": true}]},
      "Lost Banner": {"requires": [
        {"kind": "peculiarity", "prompt": "Distinction", "name": "Indomitable Will"}]},
      "Sacred Wilderness": {"requires": [
        {"kind": "item", "prompt": "Estate", "name": "Estate", "custom": true, "define": "free food, shelter, and medical care"}]},
      "Spirit Companion": {"sub": "ring", "requires": [
        {"kind": "item", "prompt": "Talisman", "custom": true, "name": "Meishōdō talisman", "define": "which talisman, agreed with the GM"},
        {"kind": "technique", "prompt": "Invocation of that ring", "rank": 1, "category": "invocation", "ring_from_sub": true}]},
      "Spiritual Debt": {"sub": "ring", "requires": [
        {"kind": "ring_swap", "optional": true, "cap": 3, "to": "from_sub", "prompt": "The spirit's ring"}]}
    },
    "Courts of Stone Heritages": {
      "Triumph over the Lion": {"sub": "item_category", "requires": [
        {"kind": "item", "prompt": "Family heirloom", "category_from_sub": true, "qualities": {"player": 1, "gm": 1}}]},
      "Unforgivable Performance": {"sub": "skill", "requires": [
        {"kind": "peculiarity", "prompt": "Disadvantage", "name": "Benten's Curse"}]},
      "Triumph During Gempuku": {"requires": [
        {"kind": "peculiarity", "prompt": "Distinction", "name": "Support of [One Group]", "subject": "the Kakita Dueling Academy"}]},
      "Elegant Craftsman": {"requires": [
        {"kind": "peculiarity", "prompt": "Anxiety", "name": "Isolation"},
        {"kind": "ring_swap", "optional": true, "cap": 3, "to": ["Fire", "Air"], "prompt": "Raise Fire or Air"}]}
    },
    "Fields of Victory Heritages": {
      "Born on the Battlefield": {"requires": [
        {"kind": "peculiarity", "prompt": "Distinction", "name": "Guiding Ancestor"}]},
      "Victory against the Crane": {"sub": "item_category", "requires": [
        {"kind": "item", "prompt": "Family heirloom", "category_from_sub": true, "heirloom": "battlefield"}]},
      "Shamed by Defeat": {"requires": [
        {"kind": "skill", "prompt": "Starting skill at 0 ranks", "from": "school_starting_at_zero"}]},
      "Blade of 10,000 Battles": {"requires": [
        {"kind": "item", "prompt": "Storied weapon", "category": "weapon", "heirloom": "battlefield"}]},
      "Lost Heirloom": {"requires": [
        {"kind": "item", "prompt": "The lost weapon", "category": "weapon", "held": false, "heirloom": "battlefield"}]},
      "Selfless Sentinel": {"requires": [
        {"kind": "peculiarity", "prompt": "Distinction", "name": "Traditional Adherent"}]},
      "Mighty Conqueror": {"requires": [
        {"kind": "pick_one", "prompt": "One of the three", "options": [
          {"kind": "money", "prompt": "Double starting koku", "koku": "double"},
          {"kind": "item", "prompt": "Item of rarity 6 or lower", "rarity_max": 6, "heirloom": "battlefield"},
          {"kind": "peculiarity", "prompt": "Passion", "name": "Glorious Deeds"}]}]},
      "Right Hand of the Emperor": {"requires": [
        {"kind": "peculiarity", "prompt": "Distinction", "name": "Support of [One Group]",
         "subject_options": ["the Seppun family", "the Otomo family", "the Miya family", "the Imperial Legions"]}]}
    },
    "Shadowlands Heritages": {
      "Blood and Mortar": {"requires": [
        {"kind": "peculiarity", "prompt": "Advantage", "name": "Blessed Lineage"}]},
      "Lost in the Darkness": {"sub": "skill"},
      "Vengeance for the Fallen": {"sub": "skill", "requires": [
        {"kind": "peculiarity", "prompt": "Adversity", "name": "Haunting"}]},
      "Tainted Blood": {"requires": [
        {"kind": "peculiarity", "prompt": "Anxiety", "name": "Fallen Ancestor"},
        {"kind": "ring_swap", "optional": true, "cap": 3, "to": ["Void"], "prompt": "Raise Void"}]}
    },
    "New Samurai Heritages (Dragon)": {
      "At One with Nature": {"sub": "item"},
      "Medical Innovator": {"requires": [
        {"kind": "peculiarity", "prompt": "Distinction", "name": "Knowledgeable Wilderness Guide"}]},
      "Gaijin Consort": {"requires": [
        {"kind": "peculiarity", "prompt": "Distinction", "name": "Ally [Name]", "subject_free": "the gaijin group (the book: Ally [Gaijin Group])"}]},
      "Revered Parent": {"requires": [
        {"kind": "peculiarity", "prompt": "One distinction", "options": ["Kisshoten’s Blessing", "Famously Lucky"]}]},
      "Path to Enlightenment": {"requires": [
        {"kind": "peculiarity", "prompt": "Passion", "name": "Enlightenment"}]}
    }
  }
};
