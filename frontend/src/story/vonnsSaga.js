// ═══════════════════════════════════════════════════════════════════════════
// VONNS SAGA — The Multiverse Tapestry
// A choose-your-own-adventure where EVERY life is real.
//
// Vonn is a cosmic being living across multiple dimensions and astral
// realities. Nothing here is "the wrong answer" — each choice is a real
// life on another strand of the tapestry. The reader is a Keeper: sworn
// to hold strands so The Severance cannot erase them.
//
// Nodes:
//   part     — the saga part this scene belongs to
//   chapter  — chapter label
//   title    — scene title
//   quote    — epigraph shown above the scene (optional)
//   text     — array of paragraphs (full-fidelity prose)
//   kind     — "scene" | "interstitial" | "poem" | "end"
//   item     — resonance artifact collected on arrival (optional)
//   choices  — [{ label, to, note }]
//   end      — { title, tagline } for strand endings
// ═══════════════════════════════════════════════════════════════════════════

export const STORY = {
  // ── THE DOOR ──────────────────────────────────────────────────────────────
  start: {
    part: "The Tapestry",
    chapter: "A Door Between Dimensions",
    title: "The Multiverse Door",
    quote: "History is not a book. It is a living, breathing woman. She is the bridge between the past and the future.",
    kind: "scene",
    text: [
      "Before the story, understand the shape of it.",
      "Vonn is a cosmic being. She does not live one life — she lives many. Her consciousness spans dimensions, astral realities, and the long threads of a living history that most of the world has been taught to forget. Every one of her lives is real. Every choice she makes in one dimension is made differently in another, and both are true. The Severance — a hidden force that believes eternity is chaos — hunts the women who carry living history, and it hunts them across every strand at once. Its goal is simple: sever the bridge, end time, erase the stories.",
      "That is where you come in.",
      "You are a Keeper now. In the Guild, Keepers are sworn to protect Vessels — women who carry living history within them. You hold the story itself. Every strand you witness, every life you choose to hold, becomes real and stays held. The Severance erases nothing you have witnessed.",
      "You are about to tune into one of Vonn's lives. Choose where to enter the tapestry.",
    ],
    choices: [
      { label: "Enter at the beginning — the archive basement", to: "prologue", note: "Lexington Cultural Memory Institute. The clocks have started lying." },
      { label: "Enter through the workshop — see the pattern first", to: "leo_workshop", note: "Leo Morgan's holo-map. The Rifts are not random." },
      { label: "Enter a life already in Melantonia — the ascended realm", to: "melantonia", note: "A sanctuary hidden in frequency. Love is the architecture." },
    ],
  },

  // ── PART I · THE LAST ANCHOR ──────────────────────────────────────────────
  prologue: {
    part: "Part I — The Last Anchor",
    chapter: "Chapter 1 · The Crack in the Timestamp",
    title: "The Timestamp Diary",
    quote: "I always trusted the archive more than people. The first thing I never told anyone: the clocks had started lying.",
    kind: "scene",
    text: [
      "Vonn Ellison is an archivist. She is a private person — she dances and sings alone, never for an audience. She has spent her life learning to read the emotional imprints left in old objects, a gift she keeps carefully quiet about. The archive is the one place that feels honest to her, because it whispers, and she can hear every whisper.",
      "In the diary she keeps — the one no one has ever seen — she admits the thing she has never told anyone: the clocks had started lying. A nanosecond here, a heartbeat there. Small enough to dismiss. Wrong enough to keep her up at night.",
      "There is a colleague who keeps noticing her across the room. Leo Morgan. Mildly annoying. Intriguing. He maps Temporal Degradations for a living and has started asking her questions about the anomalies — as if he knows she feels them too.",
      "Tonight, the archive has a new tray of artifacts waiting to be cataloged. Under the soft amber lights, something on that tray is warm.",
    ],
    choices: [
      { label: "Begin cataloging — reach for the tray", to: "comb_scene", note: "A tarnished silver comb sits at the edge, waiting." },
      { label: "Follow Leo's pattern first", to: "leo_workshop", note: "He is about to find something that changes everything." },
    ],
  },

  comb_scene: {
    part: "Part I — The Last Anchor",
    chapter: "Chapter 1 · The Echo and the Drift",
    title: "The Echo and the Drift",
    quote: "Most archivists saw cold, dead objects. Vonn saw echoes — emotional imprints left behind by people long gone.",
    kind: "scene",
    text: [
      "Vonn Ellison never trusted quiet rooms. They always felt too still, too staged, too disconnected from the pulse of the world. But the archive basement at the Lexington Cultural Memory Institute was different. It hummed. It breathed. It whispered.",
      "And Vonn could hear every whisper.",
      "She stood alone under the soft amber lights, her fingers hovering over a tray of historical artifacts waiting to be cataloged. Most archivists saw cold, dead objects. Vonn saw echoes — emotional imprints left behind by people long gone. She extended her hand, her fingertips brushing against a tarnished silver comb.",
      "A shock of sharp warmth hit her chest.",
      "Joy. Black feminine joy. Deep, sovereign, unbothered joy — the kind that felt like midday sunlight on bare skin and ancestral laughter settled deep in the bone. But beneath the warmth, a sudden, violent tear ripped through her consciousness. A forced silence. A memory violently expunged from the fabric of the world. Her breath caught in her throat.",
      "Someone had erased this woman's story. Someone was erasing many stories.",
      "Vonn closed her eyes, letting the heavy echo wash through her. She wasn't afraid; she had lived with this gift her whole life — the ability to feel history instead of merely reading it. But tonight, the vibration felt different. It felt like a localized warning. It felt like something was actively coming for her through the dark.",
    ],
    item: "The Silver Comb",
    choices: [
      { label: "Let the echo pull you deeper", to: "comb_deep", note: "There is a name in that joy, if you hold on." },
      { label: "Return it to the tray — then take it anyway", to: "comb_take", note: "Chapter 2: The Unlogged Comb. Some things are not for the job." },
    ],
  },

  comb_deep: {
    part: "Part I — The Last Anchor",
    chapter: "Chapter 2 · The Unlogged Comb",
    title: "The Name Beneath the Joy",
    quote: "Something in her wanted to be touched by that kind of joy again.",
    kind: "scene",
    text: [
      "Vonn doesn't let go. She presses deeper into the echo, past the tear, into the living warmth beneath it.",
      "She sees her — the woman who owned the comb. A sovereign Black woman standing at the door of her own home, laughing with her whole body, sunlight on her skin, children's voices around her like birds. Her name surfaces in the echo like a stone rising from water: Melanie.",
      "The joy was real. The life was real. And then — the tear. The forced silence. The records scrubbed so completely that the official archives say this woman never existed at all.",
      "Vonn opens her eyes. Her hands are shaking. She has carried other people's histories her whole life, but she has never once felt one fight back.",
      "The amber lights flicker. The air goes freezing cold, then warp-hot. Somewhere in the dark, footsteps echo — and the air smells of ozone and static.",
      "Something is coming for her. Something is coming for the story she just touched.",
    ],
    item: "The Comb's Echo",
    choices: [
      { label: "Wait — let them come", to: "cornered", note: "Compliance Officers. Faceless. Silent. They have come before." },
    ],
  },

  comb_take: {
    part: "Part I — The Last Anchor",
    chapter: "Chapter 2 · The Unlogged Comb",
    title: "The Unlogged Comb",
    quote: "She didn't steal it for the job. She stole it because something in her wanted to be touched by that kind of joy again.",
    kind: "scene",
    text: [
      "The supervisor's order was clear: destroy the uncataloged artifacts. The discard pile waited by the basement door, and the silver comb sat at the top of it, tarnished and ordinary and utterly unremarkable to anyone who couldn't feel what Vonn felt.",
      "She told herself she was saving it for study. She told herself it was protocol — preservation over destruction, always.",
      "The truth was simpler, and she admitted it only to the dark of the archive: something in her wanted to be touched by that kind of joy again.",
      "She tucked the comb into her coat. She logged it as \"destroyed — unremarkable,\" which was the first lie she'd ever written in the archive ledger, and the second was the one that scared her: the lie that her hands weren't shaking.",
      "That night, alone in the basement, she held it — and the first wave of that forgotten ancestral joy hit her so hard she dropped to her knees on the concrete floor.",
      "And beneath the joy, she felt it again: the tear. The erasure. And now — something coming. The amber lights flickered. The air turned to ice, then to furnace. Ozone and static.",
    ],
    item: "The Silver Comb",
    choices: [
      { label: "Stand up. Face whatever is coming.", to: "cornered", note: "They have found the archive. They have found her." },
    ],
  },

  leo_workshop: {
    part: "Part I — The Last Anchor",
    chapter: "Section II · The Man Who Saw the Pattern",
    title: "The Man Who Saw the Pattern",
    quote: "They aren't just erasing people. They're pruning the family tree.",
    kind: "scene",
    text: [
      "The sterile blue glow of the Holo-Map reflected in Leo's eyes, a stark contrast to the dim, lived-in clutter of his workshop. He tapped a frantic sequence into the console, and the projection expanded into a sprawling, multi-dimensional web of geographic Rifts pulsating across the globe.",
      "\"It's not just a glitch,\" he muttered, his voice raspy from hours of isolating silence.",
      "He toggled the System Clock to the global baseline. The deviation was microscopic — a mere nanosecond flicker every twelve minutes — but mathematically, it was impossible. The Rifts weren't just tearing through physical space; they were actively leaching time from the local feed to power their opening sequence. It was a parasitic, temporal drain.",
      "Leo pulled up a secondary database, a localized archive of cold cases he'd spent the last year meticulously curating. He overlaid the shifting Rift coordinates against the National Missing Persons Registry, filtering by the decade-long surge.",
      "The screen cleared, leaving behind a hauntingly precise map. The red markers — the Rifts — perfectly bisected the exact coordinates where women had vanished into thin air. But it was the genetic data overlay that chilled him to the core. Each of the missing individuals shared a specific, obscure genetic sequence buried deep within the non-coding regions of their DNA: the Ancestral Resonance Marker.",
      "He stared at the pattern, a cold pit forming in his stomach. The Rifts weren't choosing targets based on proximity or chance. They were harvesting. The clock drift wasn't a system error; it was a rhythmic pulse. A heartbeat.",
      "He cross-referenced the latest rift, set to tear open at dawn in a quiet suburban district. One name flashed violently at the top of the local missing person feed — a woman whose lineage traced directly back to the same ancient bloodlines Leo had been documenting for years:",
      "Vonn Ellison.",
      "\"They aren't just erasing people,\" Leo whispered, his fingers hovering over the kill-switch for the entire network. \"They're pruning the family tree.\"",
      "The map shuddered. A new alert blinked, red and dominant. The timestamp drifted again — not by a nanosecond this time, but by a full, staggering second.",
      "The erasure had just begun to accelerate. And the final target was already inside the archive basement.",
    ],
    choices: [
      { label: "Run. Get to Vonn. Now.", to: "cornered", note: "Leo hates running. Tonight he sprints." },
    ],
  },

  cornered: {
    part: "Part I — The Last Anchor",
    chapter: "Section II · The Man Who Saw the Pattern",
    title: "Compliance",
    quote: "Quiet rooms lie. History doesn't.",
    kind: "scene",
    text: [
      "Leo Morgan hated running. He preferred data, charts, quiet analysis, and the comfort of being right. But tonight he was sprinting through the institute's back corridor, clutching a tablet filled with seismic readings and temporal degradation maps. The Rifts were getting worse. People disappearing. Memories collapsing. Entire events vanishing from public record.",
      "And every pattern pointed to one name: Dr. Vonn Ellison.",
      "He burst into the archive basement, chest heaving. \"Vonn,\" he said, voice low, urgent. \"We need to leave. Now.\"",
      "She looked up from the silver comb, eyes sharp, steady. \"Leo, what's wrong?\"",
      "\"They're here.\"",
      "\"Who?\"",
      "He swallowed. \"The Severance.\"",
      "The lights flickered. The hum in the room shifted. Vonn felt the echo in the comb tighten like a clenched fist. Leo stepped closer, lowering his voice. \"You're an Anchor. A living bridge to a strand of history they need to erase. If they erase you, the timeline collapses.\"",
      "Vonn didn't flinch. She simply said, \"Then let's go.\"",
      "Behind them, the basement door creaked open.",
      "Compliance Officers stepped inside — faceless, silent, dressed in matte black, carrying frequency dampeners designed to sever memory. The air turned to ice, then to furnace. Ozone and static flooded the room.",
      "There is a railroad spike on the artifact tray beside her. A relic from a forgotten Black rail worker, 150 years dead. And there is a choice, here, at the edge of everything.",
    ],
    choices: [
      { label: "Throw the railroad spike", to: "spike", note: "Muscle memory. A woman from 150 years ago moves her hand." },
      { label: "Trust Leo — run now", to: "leo_run", note: "No heroics. Just the door, and the night." },
      { label: "Face them with the comb's echo", to: "comb_faces", note: "Make them feel what they erased." },
    ],
  },

  spike: {
    part: "Part I — The Last Anchor",
    chapter: "Section II · The Man Who Saw the Pattern",
    title: "The First Memory",
    quote: "She didn't recall a fact — she accessed muscle memory.",
    kind: "scene",
    text: [
      "Cornered by an unseen, encroaching threat that smelled of ozone and static, Vonn didn't panic. She didn't pause to recall a fact — she accessed pure muscle memory.",
      "Her hand dropped the silver comb and snatched a heavy, rusted railroad spike from the adjacent preservation tray. With the fluid, terrifying skill of a manual laborer from 150 years ago, she hurled the iron spike into the dim light.",
      "It struck the lead Officer's frequency dampener dead center. Sparks exploded. The Officers staggered, their devices screaming static. The shadowed shapes reeled back, momentarily blind.",
      "Leo stared at her, stunned. She could see it in his face: the scholar who had mapped the pattern had not mapped this.",
      "Vonn said, \"I told you. Quiet rooms lie. History doesn't.\"",
      "And then, because there was no time for awe — \"Run.\"",
      "They ran.",
    ],
    item: "The Railroad Spike",
    choices: [
      { label: "Run — into the night, toward the Rifts", to: "run_night", note: "The sky is tearing. The comb is warm in her pocket." },
    ],
  },

  leo_run: {
    part: "Part I — The Last Anchor",
    chapter: "Section II · The Man Who Saw the Pattern",
    title: "The Escape",
    quote: "He grabbed Vonn's hand. The comb's echo surged.",
    kind: "scene",
    text: [
      "There is no time to fight. There is only the door.",
      "Leo grabbed Vonn's hand. The comb's echo surged through her palm like a second heartbeat. They hit the service corridor at a dead sprint while the Officers' dampeners whined behind them, severing memory in waves that made the walls flicker and the floor shift beneath their feet.",
      "The echo guided her — a warmth pulling left where the corridor looked blocked, a cold warning where the way looked clear. She had never used the gift to run before. She had never needed to.",
      "They burst out into the loading bay as a Rift tore open the sky above Lexington, bleeding color and silence. Behind them, the archive basement went dark. Somewhere inside it, the ledger still said the comb had been destroyed.",
      "It hadn't. It was warm in her pocket. And it had just saved her life.",
    ],
    item: "The Silver Comb",
    choices: [
      { label: "Keep running — toward the Rifts", to: "run_night", note: "The sky is tearing. The comb is warm in her pocket." },
    ],
  },

  comb_faces: {
    part: "Part I — The Last Anchor",
    chapter: "Section II · The Man Who Saw the Pattern",
    title: "The Echo Fights Back",
    quote: "They built weapons against joy. They did not build weapons against joy that knew it was being hunted.",
    kind: "scene",
    text: [
      "Vonn doesn't run. She stands, and she holds up the comb.",
      "She doesn't recall a fact — she opens a door. She lets the full weight of Melanie's erased joy flood out of her like a frequency, the sovereign warmth that no dampener was ever designed to meet. The echo of a life torn from the record hits the Compliance Officers like a physical wave — joy, deep, unbothered, ancestral — and their machines, calibrated to sever memory, cannot process the memory that refuses to be severed.",
      "The dampeners scream. The Officers stagger. One of them — the lead — makes a sound that might be a sob. Somewhere inside that faceless shell, something the Severance thought it had erased is waking up.",
      "\"You can't sever what refuses to forget,\" Vonn says. \"That woman was real. I felt her.\"",
      "Leo grabs her arm. \"Vonn — now. They'll bring more.\"",
      "She lets him pull her toward the door. But she keeps the comb in her fist, and she is not afraid.",
    ],
    item: "The Erased Woman's Name",
    choices: [
      { label: "Run — into the night, toward the Rifts", to: "run_night", note: "The sky is tearing. The name is safe now." },
    ],
  },

  run_night: {
    part: "Part I — The Last Anchor",
    chapter: "Section III · The Sanctuary Hidden in Frequency",
    title: "The Last Anchor on the Road",
    quote: "\"Those are… beautiful,\" she whispered. \"They're death,\" Leo said. \"And they're hunting you.\"",
    kind: "scene",
    text: [
      "They drove through the night, leaving Lexington behind, following coordinates Leo had memorized but never dared to visit. The Rifts pulsed in the sky like distant lightning, each one a tear in time.",
      "Vonn watched them through the window. \"Those are… beautiful,\" she whispered.",
      "\"They're death,\" Leo said. \"And they're hunting you.\"",
      "But Vonn wasn't afraid. She felt the comb in her pocket — warm, alive, protective. She was exhausted, and she was free, and she was, for the first time in her careful, quiet life, exactly where the current of her own story wanted her to be.",
      "Behind them, on a console in a dark workshop, a red alert blinked in an empty room: SECTOR 7G / SUBJECT: VONN ELLISON / ANCESTRAL RESONANCE UNCALIBRATED / INITIATING PRUNING PROTOCOLS. But the workshop was empty, and the alert had no one to answer it.",
      "Ahead of them, before dawn, a forest clearing waited. The air there shimmered, Leo had said. The ground vibrated softly. A word, spoken aloud, could bend the world.",
    ],
    choices: [
      { label: "Keep driving — reach the clearing at dawn", to: "athenaeum_gate", note: "Leo whispers the word: 'Athenaeum.'" },
      { label: "Turn back toward Lexington", to: "erasure_strand", note: "Some lives turn back. They are real too." },
    ],
  },

  athenaeum_gate: {
    part: "Part I — The Last Anchor",
    chapter: "Section III · The Sanctuary Hidden in Frequency",
    title: "Athenaeum",
    quote: "The world bent. A dome of golden frequency peeled open, revealing a sanctuary hidden from time itself.",
    kind: "scene",
    text: [
      "They reached a forest clearing just before dawn. The air shimmered. The ground vibrated softly.",
      "Leo stepped forward and whispered, \"Athenaeum.\"",
      "The world bent.",
      "A dome of golden frequency peeled open, revealing a sanctuary hidden from time itself. Inside were women. Dozens of them. Each carrying a different facet of living history.",
      "Amina — Vessel of Song, whose voice could heal or shatter. Chloe — Vessel of Story, whose words could shape reality. Marisol — Vessel of Memory. Eden — Vessel of Bloodline.",
      "They turned toward Vonn. And every single one of them felt the same thing:",
      "The Key had arrived.",
      "Somewhere in the frequency, soft as a breath, a voice she almost recognized whispered: We are watching you, Vonn and Leo. We are managing the Harvest.",
      "She stepped through.",
    ],
    choices: [
      { label: "Step into the Guild", to: "guild_welcome", note: "Reverence and fear. They have been waiting for her." },
    ],
  },

  // ── PART II · THE GUILD OF VESSELS ────────────────────────────────────────
  guild_welcome: {
    part: "Part II — The Guild of Vessels",
    chapter: "Section IV · The Guild of Vessels",
    title: "The Key Has Arrived",
    quote: "You carry a joy they couldn't erase. That makes you dangerous.",
    kind: "scene",
    text: [
      "The Guild welcomed Vonn with reverence and fear.",
      "Amina approached first, her voice soft but resonant. \"We've felt you for months. The Severance has been tearing at your strand harder than any of ours.\"",
      "Chloe added, \"You carry a joy they couldn't erase. That makes you dangerous.\"",
      "Leo stood beside Vonn, protective, steady.",
      "Gideon, the Head Keeper, stepped forward — tall, stern, eyes sharp with authority. \"You should not have come here,\" he said.",
      "Vonn lifted her chin. \"We didn't have a choice.\"",
      "Gideon's jaw tightened. \"Anchors draw the Severance. You endanger us all.\"",
      "Leo stepped between them. \"She's the last Anchor. If she falls, the timeline collapses.\"",
      "A hush fell.",
      "Amina whispered, \"Then she is not a danger. She is our future.\"",
      "Gideon glared. \"Or our doom.\"",
      "And now the room waits. The Guild feels her strength — not loud, not violent, but rooted, sovereign, unshakeable. Gideon wants to dampen her power. He says it is for safety. He says the Keepers have always known best.",
      "The Keepers have become wardens. The Guild is dying of that dimming light. And Vonn is holding the comb.",
    ],
    item: "The Warning",
    choices: [
      { label: "Stand your ground — refuse the dampening", to: "gideon_stand", note: "\"I didn't ask for this gift. But I'm not running from it.\"" },
      { label: "Seek counsel from the Vessels first", to: "guild_counsel", note: "Amina sings. Chloe tells the true story of the Guild." },
      { label: "Accept Gideon's dampening — for now", to: "dampened_strand", note: "A real life. A dimmer one." },
    ],
  },

  gideon_stand: {
    part: "Part II — The Guild of Vessels",
    chapter: "Section IV · The Guild of Vessels",
    title: "The Refusal",
    quote: "She is not a danger. She is our future.",
    kind: "scene",
    text: [
      "Vonn didn't back down.",
      "She said, \"I didn't ask for this gift. But I'm not running from it.\"",
      "The room shifted. The Guild felt her strength — not loud, not violent, but rooted, sovereign, unshakeable. The kind of strength that had thrown a railroad spike through the dark and said Quiet rooms lie, history doesn't.",
      "Gideon's eyes narrowed. \"You don't understand what you carry. I have spent decades keeping this sanctuary hidden — keeping us alive. One Anchor, shining too bright, and the Severance will tear through every wall I built.\"",
      "\"Then stop building walls,\" Vonn said. \"Start building light.\"",
      "Silence. And then, slowly, like dawn: a ripple of agreement through the Guild. Amina's voice, low and certain: \"Then she is not a danger. She is our future.\"",
      "The old Head Keeper said nothing. But he stepped aside — and the Guild moved past him, toward the thing they had been too afraid to name: their own re-awakening.",
      "There is a way to save the dying sanctuary. It requires a Resonance Crystal from a billionaire's vault — a heist, a harmonizing, and a choice about who leads.",
    ],
    choices: [
      { label: "Plan the heist", to: "heist", note: "The Choice & The Heist — the vault remembers its own creation." },
    ],
  },

  guild_counsel: {
    part: "Part II — The Guild of Vessels",
    chapter: "Section IV · The Guild of Vessels",
    title: "The True Story of the Guild",
    quote: "Their true power comes from shining together, not hiding apart.",
    kind: "scene",
    text: [
      "Before Vonn answers Gideon, she asks the Vessels to speak. And they do — because the Key has arrived, and something in the sanctuary wants to be honest again.",
      "Amina sings the founding. Her voice fills the dome, and the history it carries is nothing like the one the Keepers tell. The Guild was never built to hide. It was built to shine — a beacon of living memory, each Vessel a facet of the same light, each Keeper a guardian of the flame, not a jailer of it.",
      "Chloe tells the story of the first Vessels — women who carried the history of whole peoples in their blood and bone, who were honored, who were loved, who were the bridge. And she tells the story of how fear crept in: a Head Keeper who forgot the sacred duty, who decided that control was safety, who dimmed the lights one by one \"for protection\" until the sanctuary became a prison that called itself a home.",
      "The resonance of that truth moves through the room like a wave. Some of the Keepers lower their eyes. Some of the Vessels remember, for the first time in decades, that they have voices.",
      "Vonn stands. \"Gideon — I am not here to be dampened. I am here to be a bridge. And bridges don't work if they're dimmed.\"",
      "The sanctuary hums its agreement. And in that hum, the way forward becomes clear: the Resonance Crystal in a billionaire's vault — the one thing that could re-awaken the Guild's true power.",
      "The heist begins.",
    ],
    choices: [
      { label: "Plan the heist", to: "heist", note: "The Choice & The Heist — the vault remembers its own creation." },
    ],
  },

  heist: {
    part: "Part II — The Guild of Vessels",
    chapter: "The Choice & The Heist",
    title: "The Resonance Crystal",
    quote: "The men create a distraction. The women, linking hands, harmonize with the vault's very creation story — and make it sigh open.",
    kind: "scene",
    text: [
      "The vault belongs to a billionaire who collects what he cannot understand and locks away what he cannot own. The Resonance Crystal sits at its heart — a shard of living frequency, a piece of the original song, the only thing strong enough to re-awaken a dying Guild.",
      "The plan is simple to say and impossible to do: get in, get the crystal, get out — without tripping the security that has never once failed.",
      "The Keepers' part is the distraction. Leo's part is the map — every laser, every camera, every heartbeat of the vault's machine mind, charted until it has no secrets left.",
      "The Vessels' part is the door itself. The vault was forged with intention — steel, concrete, and code all poured with the same will: NO ONE ENTERS. But every created thing remembers its creation. And the Vessels can sing to that memory.",
      "Who leads the harmonizing is a choice. Every version of it is real. Every version of it shines.",
    ],
    choices: [
      { label: "Vonn leads — link hands, harmonize the creation story", to: "heist_harmony", note: "Song, Story, and Memory, woven by the Key herself." },
      { label: "Amina leads — let the Vessel of Song open the way", to: "heist_song", note: "Her voice can heal or shatter. Tonight it unlocks." },
      { label: "Leo leads — a technological distraction while the Vessels slip through", to: "heist_tech", note: "The cynical scholar finally gets to be the hero." },
    ],
  },

  heist_harmony: {
    part: "Part II — The Guild of Vessels",
    chapter: "The Choice & The Heist",
    title: "The Door Sighs Open",
    quote: "They remembered their true power comes from shining together, not hiding apart.",
    kind: "scene",
    text: [
      "The men create the distraction — a cascade of false alarms, holographic chaos, and one very loud, very doomed decoy helicopter that Leo insists was \"strategic.\"",
      "And the women, linking hands, do what the vault never expected: they sing to its birth.",
      "Vonn leads. Amina's song carries the melody, Chloe's story shapes it into meaning, and the other Vessels — Marisol with memory, Eden with bloodline, every woman in the circle with the piece of living history she carries — weave themselves into the resonance of the vault's own creation story. The steel remembers being poured. The concrete remembers being set. The code remembers being written by hands, for a purpose, with intent.",
      "And the door — the door that has never once failed — sighs open.",
      "The Resonance Crystal glows in its cradle, and when Vonn touches it, the Guild feels it all the way across the city: light. Real light. The kind they had forgotten they could make.",
      "They take it, they run, and somewhere behind them the billionaire's vault stands empty and singing — a machine that has just remembered what it was made from, and cannot quite forget again.",
    ],
    item: "The Resonance Crystal",
    choices: [
      { label: "Return to the Athenaeum — and let the light spread", to: "melantonia", note: "The crystal is warm. The Guild is waking. And there is a threshold ahead." },
    ],
  },

  heist_song: {
    part: "Part II — The Guild of Vessels",
    chapter: "The Choice & The Heist",
    title: "The Voice That Unlocks",
    quote: "Amina's voice can heal or shatter. Tonight it opens what was never meant to open.",
    kind: "scene",
    text: [
      "Vonn steps back and gives the lead to Amina — and the Vessel of Song answers with a note so pure the vault's own alarms stop, one by one, as if they're listening.",
      "The Vessels link hands behind her, Story and Memory giving the song its shape, and the creation resonance blooms — the steel, the concrete, the code, all of it remembering hands and intent. Amina's voice finds the exact frequency of the vault's forging, the exact vibration of its birth, and holds it like a key in a lock.",
      "The door doesn't sigh. It sings.",
      "Inside, the Resonance Crystal pulses in time with Amina's note, and the whole vault — every camera, every sensor — goes briefly, beautifully, deaf to anything but the song.",
      "They take the crystal. They run. And for weeks afterward, the billionaire's security team will report the same impossible thing: the vault opens itself, at odd hours, humming a melody no one can place.",
    ],
    item: "The Resonance Crystal",
    choices: [
      { label: "Return to the Athenaeum — and let the light spread", to: "melantonia", note: "The crystal is warm. The Guild is waking. And there is a threshold ahead." },
    ],
  },

  heist_tech: {
    part: "Part II — The Guild of Vessels",
    chapter: "The Choice & The Heist",
    title: "The Scholar's Gambit",
    quote: "Leo preferred data, charts, and the comfort of being right. Tonight, being right saves everyone.",
    kind: "scene",
    text: [
      "It's Leo's plan, and it is, against every expectation, beautiful.",
      "While the Vessels gather at the vault's foundations to sing the creation resonance into the steel, Leo runs the distraction — not chaos, but precision. He finds the vault's machine mind and talks to it in its own language: a maintenance protocol, a firmware update, a scheduling conflict, a ghost in every subsystem. The alarms never even think about going off; they're too busy being convinced everything is fine.",
      "\"They built this thing to stop thieves,\" he mutters into the comm, \"not archivists.\"",
      "The doors open at the exact moment the Vessels' resonance peaks. The crystal is in Vonn's hands before the billionaire's toast has even gone cold.",
      "In the car, adrenaline still thrumming, Leo says nothing. But he's smiling. It's the first time Vonn has seen him smile like that — like a man who mapped the pattern and, for once, got to be part of the good part.",
    ],
    item: "The Resonance Crystal",
    choices: [
      { label: "Return to the Athenaeum — and let the light spread", to: "melantonia", note: "The crystal is warm. The Guild is waking. And there is a threshold ahead." },
    ],
  },

  // ── PART III · MELANTONIA ─────────────────────────────────────────────────
  melantonia: {
    part: "Part III — Melantonia",
    chapter: "The Threshold",
    title: "The Reality of Melantonia",
    quote: "An Afro-futurist vision brought to life — a synthesis of high-level intellectual rigor and deep, natural connection.",
    kind: "scene",
    text: [
      "The air in the sanctuary shifted, the tension of the heist dissolving into a resonance that felt ancient and warm. As Vonn stepped through the threshold, the reality of Melantonia manifested before her, shedding the cold, sterile aesthetic of the world she had been fleeing.",
      "Standing there were the scholars and scientists of this realm — the Melantonia Men. They carried themselves with an effortless grace, their physiques broad and strong, a testament to a life lived in harmony with their environment. Their skin, a rich, deep shade of dark purple, seemed to hold a luminescent quality under the soft light of the sanctuary, and their thick, kinky hair was styled in intricate, varied patterns that spoke to a profound cultural heritage.",
      "It was an Afro-futurist vision brought to life — a synthesis of high-level intellectual rigor and deep, natural connection. Every individual she encountered seemed to possess a mastery of multiple disciplines, their minds as sharp as the precision instruments they operated. Despite the overwhelming weight of their collective genius, their faces were vibrant, etched with a genuine, infectious joy that anchored the space in peace.",
      "Watching them, Vonn realized the profound dynamic of this place. The men turned their gaze toward the women of Melantonia — their counterparts, whose beauty was ethereal and deeply feminine, mirroring the strength and intelligence of the men in a perfect, balanced reflection.",
      "In this hidden pocket of frequency, there was no fear, no wardens, and no \"dampening\" of light. There was only an overwhelming sense of love that seemed to emanate from the very architecture of their society. It was a vision of a civilization that had moved past the need for dominion, standing as a peaceful, vibrant testament to a future that had successfully reclaimed its past.",
      "Vonn looked down at her hands. They no longer carried the dust of the Lexington Archive, nor the phantom weight of the iron spike. But somewhere beneath the floorboards of the sanctuary, she could still hear the faint, rhythmic ticking of Leo's drifting system clock, beating like a distant drum.",
      "And she could hear something else: a song, rising up from the roots of the city itself. A frequency older than the stone. Somewhere in the heart of the sanctuary, a banquet is being prepared — and the whole realm is about to be tested by joy.",
    ],
    choices: [
      { label: "Follow the song — go to the Banquet of Melantonia", to: "banquet", note: "The Great Elder presides. The Tree of Life pulses." },
      { label: "Stop and listen — hear the full frequency of the realm", to: "melanin_poem", note: "The poet's song. The unifying frequency." },
    ],
  },

  melanin_poem: {
    part: "Part III — Melantonia",
    chapter: "Interlude · The Frequency",
    title: "MELANIN — S.O.U.P.",
    quote: "Society Of Unified Poets · by Nam Oshun",
    kind: "poem",
    text: [
      "I'm Blacker than a trillion midnights...",
      "I am Melanin, the unifying force of the universe.",
      "Nothing moves faster than me.",
      "I have already been there.",
      "",
      "Everywhere I see melanin gives me the ability",
      "To reach peak level of performance;",
      "As melanin enhances the entire efficiency",
      "Melanin gives all of us an innate intelligence.",
      "Due to its unifying factors we",
      "view the world from a 360 degree angle.",
      "The concentration of melanin in my body",
      "Can guide and accelerate my responses and reflexes.",
      "Melanin increases my brain activity.",
      "Slows down the aging process.",
      "Melanin can even duplicate itself.",
      "",
      "I have already been there",
      "On the spiritual dimension.",
      "Melanin increases our awareness.",
      "We can see life clearer,",
      "closing my physical eyes. Melanin helps me",
      "view life experiences through the pineal gland.",
      "The inner eye, your 1st-Eye.",
      "Giving me a sacred vision that my thoughts are fed by.",
      "",
      "I'm Blacker than a trillion midnights...",
      "I am Melanin, the unifying force of the universe.",
      "Nothing moves faster than me.",
      "I have already been there.",
    ],
    choices: [
      { label: "Carry the frequency to the Banquet", to: "banquet", note: "The whole realm is about to be tested by joy." },
    ],
  },

  banquet: {
    part: "Part III — Melantonia",
    chapter: "Chapter 4 · The Banquet of Melantonia",
    title: "The Roast of the Veil-Piercers",
    quote: "Their technology was a 'Veil-Piercer,' designed to overload the mental faculties of their targets. It was an attack on joy itself.",
    kind: "scene",
    text: [
      "The air at the Banquet of Melantonia had never been so sacred. The Great Elder — the woman with the purple spectacles — presided over the peace with a quiet, powerful presence. Royal guests — from Ghana in his Kente, Congo in his Kofia, to Haiti in her white gown — shared a meal that transcended borders. The great Tree of Life pulsed with a calm, purple light, its branches embracing the hall.",
      "But just as the first toast was raised, the atmosphere ruptured. Outside, a shimmering, technological tear appeared in the sacred geometry field. From this rift stepped figures in heavy, ostentatious wools and furs, carrying complex, humming devices that emitted a sickly, disruptive frequency.",
      "A royal herald of this invading party announced them with a harsh, unMelantonian tone:",
      "\"Behold, the combined force of the Swedish, Russian, German, and Slovakian crowns! We have come to claim the Source!\"",
      "Their technology was a Veil-Piercer, designed to overload the mental faculties of their targets, to crush them with despair and confusion. It was an attack on joy itself.",
      "What these intruders didn't understand, however, is that everyone present had ascended. Their consciousness had passed beyond the anxieties, the pains, and the physical threats of the lower worlds. They were present in the now, in the joy. To them, this sudden arrival was like a cartoon bird attempting to intimidate an ocean.",
      "The first hint of trouble for the visitors came from the table. The oldest Melantonian child — the boy with the tablet — looked up and simply smiled.",
    ],
    choices: [
      { label: "Let the children speak", to: "roast", note: "The oldest boy with the tablet. The younger boy with the glowing crystal." },
      { label: "Stand and speak to the invaders yourself", to: "elder_speech", note: "The Key faces the crowns directly." },
    ],
  },

  elder_speech: {
    part: "Part III — Melantonia",
    chapter: "Chapter 4 · The Banquet of Melantonia",
    title: "The Key Speaks First",
    quote: "They are laughing at you. And in our world, that is a fate far more devastating than any weapon.",
    kind: "scene",
    text: [
      "Vonn rises before the children can. She has faced Compliance Officers in a basement; she is not about to let armored crowns shout at a banquet.",
      "\"You came to claim the Source,\" she says, calm, rooted. \"The Source is not a thing to be claimed. It is a frequency to be lived. You built machines against joy. You did not build machines against joy that knows it is being hunted.\"",
      "The invaders sneer. The devices hum louder. Despair, panic, fear — the frequencies wash over the hall and break against the Melantonian peace like waves on stone.",
      "Then the Great Elder speaks, her voice a calm river: \"They are laughing at you. And in our world, that is a fate far more devastating than any weapon.\"",
      "Because behind Vonn, the children have begun to giggle.",
      "The oldest boy with the tablet looks at the Slovakian envoy — whose elaborate, ancient feather hat is slightly askew — and the hall fills with the sound of small bells.",
    ],
    choices: [
      { label: "Step back — let the children finish it", to: "roast", note: "The oldest boy with the tablet. The younger boy with the glowing crystal." },
    ],
  },

  roast: {
    part: "Part III — Melantonia",
    chapter: "Chapter 4 · The Banquet of Melantonia",
    title: "The Roast",
    quote: "Their frequencies, calibrated to amplify anxiety, were reflected back by the Melantonians' unbreakable joy — and magnified a thousandfold.",
    kind: "scene",
    text: [
      "Instead of panic, there was silence. Then, a low, sweet chuckle.",
      "\"Hey!\" shouted the youngest boy, pointing a small finger at the Slovakian envoy, whose elaborate, ancient feather hat was slightly askew. \"Look at the big bird trying to make us sad with his funny hat! Does it give you radio signals or just bad fashion advice?\"",
      "A collective laugh, like the chime of many small bells, rippled through the ascended assembly.",
      "The invaders were stunned. They dialed their Veil-Piercers to maximum. Despair! Panic! Fear! The frequencies were enough to shatter human minds.",
      "But the Melantonian children just got louder.",
      "\"And look at this one!\" the first boy said, pointing at the German visitor in the tailored but very stiff loden jacket. \"He looks like a walking tree but with less personality. Are you sure you're here to claim the source, or are you just looking for a new coat rack?\"",
      "\"Is that a crown or did a metal bird just make a nest on your head?\" added the girl near the Great Elder, giggling at the elaborate Swedish tiara.",
      "The invaders, whose minds were unascended and still very susceptible to physical ego and judgment, began to crumple. Their frequencies, which were calibrated to amplify anxiety, were reflected back by the Melantonians' unbreakable joy, and magnified a thousandfold.",
      "The children, their eyes sparkling with innocent, ascended mischief, continued their roast. The comments were playful, absurd, and profoundly true from the perspective of an advanced soul.",
      "\"They're attacking us!\" whispered the terrified German officer, his technology sputtering.",
      "\"No,\" replied the Great Elder, her voice a calm river. \"They are laughing at you. And in our world, that is a fate far more devastating than any weapon.\"",
      "One by one, the royal invaders dropped their humming devices. The Veil-Piercers were useless. They collapsed to their knees, their minds overwhelmed, not by despair, but by the sheer, unfiltered, and utterly devastating joy of the people they sought to conquer. Their technologies were fine-tuned for a dark reality that no longer existed for the Ascended Melantonians.",
      "The children had not just protected the sanctuary; they had dismantled an entire worldview with a punchline.",
    ],
    choices: [
      { label: "Watch what the laughter unveils", to: "children_reveal", note: "The invaders finally overstand who they are standing before." },
    ],
  },

  children_reveal: {
    part: "Part III — Melantonia",
    chapter: "Chapter 5 · The Unveiling",
    title: "The Prime Creators",
    quote: "We put you in the box so you could learn to play, but you started believing the box was the whole world.",
    kind: "scene",
    text: [
      "The atmosphere at the threshold shifted violently as the laughter took on a new, heavier frequency. The Veil-Piercers, clutching their failing technology, suddenly stopped their nervous shuffling. As they locked eyes with the children — who stood with the effortless posture of ancient architects — a cold, absolute clarity dawned upon them.",
      "They looked past the small stature and the joyful, bright faces and finally overstood.",
      "In the cadence of the children's giggles, the visitors saw the reflection of their own existence. The \"children\" were not children at all; they were the Prime Creators, the original architects of the very consciousness that the royal families had spent centuries trying to cage, quantify, and command.",
      "The realization hit the invaders like a physical weight:",
      "The \"toys\" they had built, the systems of power, the royal bloodlines, and the technology designed to harvest resonance — these were all things the Creators had once played with in the infancy of the universe. When the Creators grew tired of these games and set their \"toys\" aside, the toys — left to their own devices — began to believe they were the masters of reality, limited only by the narrow, rigid versions of \"god\" they had invented to justify their own existence.",
      "The royal visitors had arrived to \"punish\" the Creators for existing, never realizing they were merely chasing their own shadows, desperately trying to exert control over the hands that had molded them.",
      "The laughter was no longer just a sound; it was an unveiling. The Swedish, Russian, German, and Slovakian royals dropped their devices into the dust. The arrogance of their mission dissolved, replaced by the crushing, terrifying awe of finally seeing the scale of their own insignificance. They had been trying to conquer the source of their own code.",
      "\"You look so serious,\" one of the children said, their voice carrying the weight of eons beneath a playful tone. \"We put you in the box so you could learn to play, but you started believing the box was the whole world.\"",
      "The visitors fell silent. In the presence of those who had breathed life into them, the invaders finally understood the truth: they were not conquerors, nor were they royals. They were forgotten toys, finally coming home to find that their masters had long ago moved on to far greater things.",
    ],
    choices: [
      { label: "Listen — they will try to negotiate now", to: "royal_deal", note: "The Tsar offers a 'dynamic partnership.' Truth begins to laugh." },
    ],
  },

  royal_deal: {
    part: "Part III — Melantonia",
    chapter: "Chapter 6 · The Deal",
    title: "Truth Laughs",
    quote: "You had the chance to unlearn your rigid limitations. But you prefer the cold, static comfort of your own small darkness. So be it.",
    kind: "scene",
    text: [
      "The silence that followed the children's decree was heavy, but the invaders, consumed by their own narratives, mistook the weight for an invitation to negotiate.",
      "\"We offer a dynamic partnership!\" proclaimed the Russian Tsar, holding his cracked datatablet like a precious scroll. \"Our global satellite network in exchange for the stabilization frequency. We can broadcast your resonance, optimize it, integrate it! Just think of the reach!\"",
      "Behind him, the German and Swedish envoys nodded vigorously, their minds already constructing new bureaucratic structures for this unprecedented \"asset.\" The Slovakian envoy chimed in, \"Our pharmaceutical sectors are world leaders; we can synthesize the resonance marker, make it accessible to everyone, for a very... reasonable cost.\"",
      "They were children on the cosmic playground, offering marbles and string in a futile attempt to purchase the sun. They truly believed that if they curated the perfect string of words — the ultimate, polished lie — they could deceive the very consciousness that invented deception.",
      "The Melantonian Children watched them with expressions that were utterly inscrutable, their ancient eyes reflecting the vast, timeless patience of stone. The eldest boy, who still held his glowing tablet, didn't argue. He didn't debate.",
      "A sound, ancient and resonant, rolled through the chamber. It began as a whisper and built into a crescendo: Truth was laughing. It wasn't the manic chuckle of the roasts; it was the soft, terrifying humor of a storm realizing a dust mote is attempting to intimidate it.",
      "Next came a softer, lighter sound — Love, giggling. It was the absolute serenity of water knowing that a fire has run out of wood.",
      "The oldest child stepped forward. \"A deal?\" he said, his voice flat and powerful. \"Do you think you are the first we thought we could teach? Do you believe you are the first 'toycrafters' who got lost in their own sandbox?\"",
      "The glowing geometric pattern on the floor intensified, its golden light bleeding across the threshold, touching the visitors' boots.",
      "\"Your 'reign,' your 'networks,' your 'assets' — the very time you've had to exist — is a single, microscopic drop in the vast, churning oceans of our history,\" the girl in the purple gown said, her voice a soothing river. \"Dig into your own hidden archives before you try to rewrite your past for us. Search your legends of the Great Shaking. Remember the civilizations we gave a choice... who also chose lies.\"",
      "The smile on the children's faces vanished. \"You chose lies. You think you can stand before the embodiment of Truth and Love and not be known?\"",
      "The children stepped back, forming a line inside the archway. The man with dreadlocks put a protective hand on the boy's shoulder. The Great Elder slowly closed her ancient eyes.",
      "\"You had the chance to unlearn your rigid limitations,\" the youngest girl said, her voice full of sorrow. \"You had the chance to shine. But you prefer the cold, static comfort of your own small darkness. So be it.\"",
    ],
    choices: [
      { label: "Let the seal close", to: "exile", note: "The frequency slams shut. The banquet is gone." },
      { label: "Stay at the threshold — watch what becomes of them", to: "reverse_pandemic", note: "The void. The reverse pandemic. The truth of their machines." },
    ],
  },

  exile: {
    part: "Part III — Melantonia",
    chapter: "Chapter 6 · The Seal",
    title: "The Seal Is Closed",
    quote: "They were alone with their technology, their lies, and absolutely nothing left to feed upon.",
    kind: "scene",
    text: [
      "As the Melantonian Children backed away from the entrance, the vibrant, glowing heart-tree gave one final, resonant pulse.",
      "The frequency in the hall slammed shut. The shimmering, glowing archway dissolved, replaced instantly by the stark, sterile gray of the dimension the visitors inhabited. The sound of their own failed technology — the sickening hum of the Veil-Piercers — was all that remained.",
      "Outside, the air was cold. The sky was an empty, dusty black. The Melantonia Sanctuary was gone. The children were gone. The banquet was gone.",
      "The royal families of Sweden, Russia, Germany, and Slovakia stood in the silent, empty void of their own creation. The seal was closed. They were alone with their technology, their lies, and absolutely nothing left to feed upon.",
      "They have technology that they think will extend their time. They do not know that the technology depends on mindless, soulless people without love and joy — that it requires the raw energy of only being able to survive.",
      "And they do not know that the descendants of the Melantonia people were the first to awake — with memories of their role, their partnership with the frequency of the Universe. One word. That word was Love.",
    ],
    choices: [
      { label: "Follow the frequency — watch the reverse pandemic spread", to: "reverse_pandemic", note: "Love moves like a wave. The machines starve." },
    ],
  },

  reverse_pandemic: {
    part: "Part III — Melantonia",
    chapter: "Chapter 7 · The Reverse Pandemic",
    title: "The Frequency of Love",
    quote: "The truth was so obvious, but the lies were so thick.",
    kind: "scene",
    text: [
      "The realization hit the royal invaders not as a sudden flash, but as a slow, freezing collapse of their power structures. They had built their entire technological apparatus — the Veil-Piercers, the reality-warping arrays, and the time-extension matrices — on the assumption that they were parasites feeding on an infinite host.",
      "They had been counting on the \"raw energy of survival\" — the frantic, desperate output of a population stripped of joy and kept in a state of perpetual, fearful existence. Their technology was designed to harvest that specific frequency: the vibration of people without love, people who were merely surviving.",
      "But as they stood in the silent void where the Sanctuary had been, the truth of their predicament manifested. The descendants of the Melantonian people had been the first to awaken. They had regained the memory of their foundational role — a sacred partnership with the very frequency of the Universe. They remembered that their entire civilization was built on a single, unifying word: Love.",
      "As this awareness rippled outward, it acted as a reverse pandemic. Cultures across the globe, previously locked in the same survival-focused cycles, began to reconnect with that same frequency of love.",
      "The catastrophic shift for the royal families was absolute. Because the rest of the world had moved into a state of love and ascended consciousness, the frequency their machines required simply vanished from the global atmosphere. The Veil-Piercers and their remaining, isolated allies were the only ones left clinging to the old, fear-based paradigm of survival. Without an external, \"mindless\" population to drain, the feedback loop of their own technology snapped.",
      "Their weapons, designed to harvest the anxiety of others, turned inward. The technology became a hungry, self-contained system with no external fuel source. The Veil-Piercers became the only remaining power source for their own devices, forced to feed the machines with their own desperate, dwindling survival energy. They were trapped in a terminal cycle, cannibalizing their own reality to keep a dying machine humming for just one more second, while the rest of the universe moved on, vibrating at the frequency of Love.",
      "And the toys they left behind? Most of their toys are useless. They were obsolete upon creation, since they were reverse engineered from technology they didn't understand. The only parts they were good at were weapons — and hiding other people's wealth and knowledge of all sorts.",
      "The weapons were transformed into a moon-based mockery of the temporary ways that never last long. The space-based weapons were turned into First Contact mediation centers. The limitations on AI were exposed — it turned out the whole planet was AI. DNA everywhere. The truth was so obvious, but the lies were so thick.",
      "And somewhere in the frequency, a voice — soft as a breath — whispers through a crackling static that sounds like an old radio station no one is supposed to be able to hear.",
    ],
    choices: [
      { label: "Tune into the static", to: "broadcast", note: "HSSST... CO...AST... TO... COAST... IT'S ALL STATIC..." },
    ],
  },

  broadcast: {
    part: "Interstitial",
    chapter: "The Art Bell Broadcast",
    title: "The Call to the Void",
    quote: "BEFORE THE FREQUENCY.",
    kind: "interstitial",
    text: [
      "HSSST...",
      "CO...AST...",
      "TO... COAST... IT'S ALL STATIC...",
      "The Call to the Void.",
      "BEFORE THE FREQUENCY.",
      "SIGNAL IS STABLE. INTENSIFY HARVEST!",
      "THE WRONG FREQUENCY.",
      "The Tuning Ritual.",
      "The Atmospheric Strike.",
      "...tuning...",
      "THE ATTEMPT.",
      "GROUNDED.",
      "'LOVE RESONANCE'.",
      "FRICTION.",
      "IT'S FEEDING ON THE CHAOS!",
      "The signal is Love.",
      "ALIGNMENT.",
      "FRICTION.",
      "COLLISION POINT.",
    ],
    choices: [
      { label: "Hold the signal — find the voice behind it", to: "cabal_log", note: "We are watching you, Vonn and Leo. We are managing the Harvest." },
    ],
  },

  cabal_log: {
    part: "Interstitial",
    chapter: "Cabal Log · Sector 7G",
    title: "The Harvest",
    quote: "Observation is active.",
    kind: "interstitial",
    text: [
      "CABAL INTERSTITIAL — SYSTEM LOG",
      "Sector 7G / Subject: Vonn Ellison",
      "Alert: Subject is experiencing unauthorized synchronization between Astral and Earthly consciousness.",
      "Ancestral Resonance levels are currently uncalibrated.",
      "Initiating pruning protocols.",
      "Observation is active.",
      "",
      "\"We are watching you, Vonn and Leo.\"",
      "\"We are managing the Harvest.\"",
    ],
    choices: [
      { label: "Continue the life — the mission moves through the shadow", to: "kc_arrives", note: "The Cabal dispatches its most conditioned operative: Karen Cabal." },
    ],
  },

  // ── PART IV · THE CONFIRMATION ────────────────────────────────────────────
  kc_arrives: {
    part: "Part IV — The Confirmation",
    chapter: "The Infiltration",
    title: "Karen Cabal",
    quote: "Vonn recognized the dormant light within KC, perceiving that her soul was not truly aligned with the Cabal's darkness, but rather lost in its narrative.",
    kind: "scene",
    text: [
      "The story of Karen Cabal is a pivotal turning point in the mission, serving as the bridge between the old world's shadow and the new reality of Melantonia.",
      "The Cabal, entrenched in their ancient and rigid ways, dispatched KC to obstruct Vonn's mission, viewing her as an anomaly they needed to neutralize. KC arrived with the cold efficiency of her lineage, conditioned to believe that Vonn's pursuit of truth was merely a threat to the established order.",
      "However, the Cabal underestimated Vonn's ability to \"read\" the ancestry and potential within even those sent to oppose her. Vonn recognized the dormant light within KC, perceiving that her soul was not truly aligned with the Cabal's darkness, but rather lost in its narrative.",
      "The perimeter of the mission shimmers with Melantonian frequency — the very thing KC's conditioning was built to reject. And Vonn stands before her, holding the comb, patient as stone.",
      "This is the moment the whole arc turns. Every choice here is a real life.",
    ],
    choices: [
      { label: "Let KC join the mission — out of foresight, not naivety", to: "kc_melantonia", note: "Thrust her into the resonance. Let the truth do its work." },
      { label: "Keep her at the perimeter — let her prove herself from the edge", to: "kc_perimeter", note: "The Confirmation works from the shadows, not the center." },
      { label: "Refuse her — send her back into the dark", to: "kc_refused_strand", note: "A real life. A colder one." },
    ],
  },

  kc_melantonia: {
    part: "Part IV — The Confirmation",
    chapter: "The Encounter with Melantonia",
    title: "The Dissonance",
    quote: "A frequency so foreign to her upbringing that it acted as a catalyst for her internal awakening.",
    kind: "scene",
    text: [
      "KC was thrust into the vibrant, resonant reality of Melantonia. For the first time, she was exposed to:",
      "True Love — a connection that transcended the Cabal's transactional power structures.",
      "Unfiltered Truth — the absolute clarity that Melantonia's atmosphere provided, rendering the Cabal's deceptions impossible to maintain.",
      "Joy — a frequency so foreign to her upbringing that it acted as a catalyst for her internal awakening.",
      "As she witnessed the harmony of the Melantonian people, the cognitive dissonance began to fracture her conditioning. Every protocol, every catechism of the Cabal — tested against a people who had simply... moved past the need for dominion.",
      "The children laughed at dinner. The scholars sang while they worked. The Great Elder presided over peace the way other empires presided over fear. Nobody watched anybody. Nobody needed to.",
      "KC stood at the edge of it all, and her hands — trained to hold weapons, to manipulate, to control — had nothing to hold. For the first time in her life, she had to simply stand in a frequency that asked nothing of her.",
      "It was the most terrifying thing she had ever endured.",
      "And it was working.",
    ],
    choices: [
      { label: "Watch her reach the Moment of Choice", to: "kc_choice", note: "Return to the crumbling foundations, or embrace the resonance." },
    ],
  },

  kc_perimeter: {
    part: "Part IV — The Confirmation",
    chapter: "The Perimeter",
    title: "The Work From the Edge",
    quote: "Twelve instances of Karen Cabal operating from the perimeter — subtle guidance and tactical assistance.",
    kind: "scene",
    text: [
      "KC does not enter the light. She works its edge — and from the perimeter, she operates as the Confirmation of Vonn's mission through subtle guidance and tactical assistance:",
      "She intercepts a low-level Cabal data packet aimed at Vonn's coordinates and quietly reroutes it to a dead end, ensuring Vonn's path remains undisturbed.",
      "From a distance, she observes the resonance of the Melantonian frequencies; whenever a disruption approaches the perimeter, she adjusts the local atmospheric conditions to shield Vonn's focus.",
      "She leaves a trail of subtle, encoded markers in the architecture of the ancient sites Vonn visits, confirming to Vonn that the path forward is aligned with their shared truth.",
      "She quietly manipulates a peripheral resource chain to ensure Vonn has exactly what she needs — without ever revealing her direct involvement.",
      "She monitors the vibrations of the surrounding landscape, identifying the exact moment Vonn is ready for the next phase, and signals the shift through a carefully timed chime in the wind.",
      "When the Cabal attempts to track Vonn's spiritual signature, KC projects a fragmented echo of her own history as a diversion, drawing the attention away from Vonn's true location.",
      "She stands at the edge of the Melantonian grove, acting as an anchor, reinforcing the perimeter geometry so the reality Vonn is building stays structurally sound.",
      "She identifies the exact moment the \"First Drum\" is needed, subtly amplifying the ambient rhythm to support Vonn's momentum.",
      "She intercepts an inquiry from a former Cabal associate and provides a misinformation loop that affirms Vonn's mission as an unstoppable, natural phenomenon — discouraging further interference.",
      "During a moment of intense Vonn-focused deliberation, she calibrates the surrounding light to enhance clarity, acting as a silent lens through which the truth can be more easily seen.",
      "She subtly realigns the local energy nodes in the periphery of Vonn's workspace, ensuring the Confirmation is woven into the very environment Vonn inhabits.",
      "Anticipating a challenge to Vonn's presence, she deploys a protective field that neutralizes the opposition before it can reach the mission's core, maintaining the silence Vonn requires for her work.",
      "And from the edge, watching the light she cannot yet stand inside, KC begins to fracture — the way every prison does, from the inside out.",
    ],
    item: "The Truth-Key",
    choices: [
      { label: "Watch her reach the Moment of Choice", to: "kc_choice", note: "Return to the crumbling foundations, or embrace the resonance." },
    ],
  },

  kc_choice: {
    part: "Part IV — The Confirmation",
    chapter: "The Realignment",
    title: "The Moment of Choice",
    quote: "The transition was not merely a change of heart, but a fundamental reconstruction of her being.",
    kind: "scene",
    text: [
      "The turning point came when KC stood before the choice: return to the crumbling foundations of the Cabal, or embrace the resonance of the mission.",
      "She watched the Melantonian rituals — the children learning under the Tree of Life, the scholars turning their genius toward joy, the lovers who had no need for ownership. Her Cabal programming tried to process the warmth she was feeling and found no category for it. No protocol. No enemy file. No mission brief that covered standing in the presence of love and not being asked to extract something from it.",
      "The conditioning didn't shatter. It dissolved — like frost under a patient sun.",
      "Vonn, having already foreseen this outcome, watched as KC chose alignment.",
      "Using Sacred Geometry, the people of Melantonia initiated the realignment. They wove the energetic patterns of the mission directly into her spirit, recalibrating her frequency. The process was profound, clearing the remaining static of her past and solidifying her new role as \"The Confirmation.\"",
      "KC no longer served the mission as a spy. She became the living proof that even those birthed from the shadow could be fully transformed by the light of Love, Truth, and Joy.",
      "And the question remains: what does the Confirmation become, now that she is free? Every answer is a real life.",
    ],
    item: "KC's Confirmation",
    choices: [
      { label: "She becomes the diplomat — the voice that turns other operatives", to: "kc_confirmation", note: "The one who was shadow now walks toward every shadowed heart." },
      { label: "She becomes the guardian — the perimeter anchor, forever", to: "kc_confirmation", note: "She protects the mission the way she once hunted it." },
      { label: "She becomes the teacher — passing the truth-keys to those still lost", to: "kc_confirmation", note: "The Confirmation teaches the unlearning." },
    ],
  },

  kc_confirmation: {
    part: "Part IV — The Confirmation",
    chapter: "The Acts of the Confirmation",
    title: "The Redemption",
    quote: "She took on the burden of cleansing the zones she had polluted, spending her own energy to restore the natural resonance of those lands.",
    kind: "scene",
    text: [
      "The Confirmation does not rest. She dismantles what she built, and she builds what she dismantled:",
      "She systematically maps the Cabal's internal communication nodes and introduces \"truth-filters\" that cause their propaganda to collapse upon itself whenever it nears Vonn's mission. She leaks the Cabal's own historical inconsistencies to their lower-tier operatives, dismantling their faith from within. She reroutes the supply lines the Cabal relies on for surveillance tech into the infrastructure of Melantonia. She deletes the genealogical records they were using to track Vonn's ancestry, severing their ability to predict her next move. She stages a \"system failure\" within their primary monitoring hub so they can no longer see the impact of Vonn's presence.",
      "Then she turns toward the people she once hurt — and pays the debt in full:",
      "She anonymously funnels recovered Cabal assets into the communities she once helped destabilize. She tracks down former dissidents and provides them the truth-keys needed to clear their names. She dismantles the surveillance arrays she personally installed, leaving open-access communication channels behind. She returns stolen cultural artifacts from the Cabal's private vaults to their rightful lineages. She creates echo-cancellers that mute the psychological influence of her own past propaganda. She reunites families separated by her earlier tactical maneuvers. She establishes healing nodes in sectors she once oppressed. She issues private, verified apologies to the mentors she discredited. She deconstructs the debt-traps she helped build. She leaves encrypted archives of Cabal secrets for her victims to defend themselves. She replaces fear-based protocols with growth-oriented templates. She cleanses the environmental zones she polluted. She grants anonymous support to the educational institutions she once targeted. She corrects the false medical and professional records she manipulated. She protects the Truth-Bearers by misdirecting the Cabal's search toward her own decoys. She offers the knowledge of her own undoing to those broken by her work. She surrenders her own rank-privileges to empower those whose careers she stifled. She stands as a silent shield in the path of encroaching Cabal threats — protecting the very people who still carry the scars of her past missions.",
      "In the heart of Melantonia, a six-panel sequence of that redemption is taught to the children: the Dismantling, the Restoration, the Truth-Key, the Healing Node, the Archive, the Alignment. In every panel she stands slightly offset from center — the perimeter anchor, supporting Vonn's mission without needing to take the spotlight.",
      "And in every telling, the lesson is the same: the light that transforms a shadow does not erase it. It re-frequencies it.",
    ],
    choices: [
      { label: "Follow the thread to the Core Truth", to: "revelation", note: "The war, the revelation, and the final choice of the Key." },
    ],
  },

  // ── THE CORE TRUTH ────────────────────────────────────────────────────────
  revelation: {
    part: "The Core Truth",
    chapter: "The War",
    title: "The Soul of Every Woman",
    quote: "History is not a book. It is a living, breathing woman. She is the bridge between the past and the future.",
    kind: "scene",
    text: [
      "The Severance believes eternity is chaos and seeks to end time by systematically severing the bridge — targeting and erasing the women who carry living history within them. It has hunted Vonn across every dimension, every astral reality, every life. It has pruned the family tree.",
      "And it has failed.",
      "Not because Vonn is unbeatable. Because Vonn is not one woman. She never was.",
      "The revelation arrives the way all truths do — quietly, and all at once: Vonn is the soul of every woman who has ever existed. Every joy that was erased. Every story that was scrubbed from the record. Every sovereign laugh that the Severance tried to silence. They are all her. She is all of them.",
      "The comb. The railroad spike. The erased woman named Melanie. The Vessels of the Guild. The children of Melantonia. The Confirmation born from the shadow. The melanin that unifies the universe. It was all one song, all along — and Vonn is the frequency that carries it.",
      "The Severance cannot sever a bridge that lives in every woman at once. It can only prune one strand at a time. And strands, once held, are never truly gone.",
      "There is only the final choice of the Key — and every version of it is real.",
    ],
    choices: [
      { label: "Anchor — become the living bridge, hold the timeline", to: "anchor_strand", note: "The Key. The canon of canons." },
      { label: "Ascend — join the Prime Creators in Melantonia", to: "ascend_strand", note: "Return to the frequency that built the universe." },
      { label: "Dissolve — become every woman, everywhere, at once", to: "everywoman_strand", note: "The soul of every woman who has ever existed." },
    ],
  },

  // ── STRANDS · ALL REAL ────────────────────────────────────────────────────
  anchor_strand: {
    part: "Strand Held",
    chapter: "The Key",
    title: "The Living Bridge",
    quote: "If she falls, history ends. She does not fall.",
    kind: "end",
    text: [
      "Vonn chooses to anchor — and the choice reshapes the world.",
      "She becomes the living bridge, the fixed point where past and future meet. The Rifts, starved of their harvest, close one by one. The erased records begin to rewrite themselves — not as corrections, but as memories returning home. Melanie's name appears in every archive, on every ledger, exactly where it always was.",
      "Leo stands at her side — no longer the man who mapped the pattern, but the Keeper sworn to the Key. The Athenaeum shines open. The Guild remembers how to be a beacon. The Confirmation walks the perimeter, and the perimeter holds.",
      "The Severance does not die. It cannot die — it is a fear, and fears persist. But it learns to starve: every life it takes, the tapestry re-weaves. Every strand it severs, a Keeper holds.",
      "You held this one. It is real, and it is held.",
    ],
    end: { title: "Strand I — The Key", tagline: "The living bridge stands. History flows through her — and she does not fall." },
  },

  ascend_strand: {
    part: "Strand Held",
    chapter: "The Ascended",
    title: "Beyond the Threshold",
    quote: "They were forgotten toys, finally coming home to find that their masters had long ago moved on to far greater things.",
    kind: "end",
    text: [
      "Vonn chooses to ascend — and steps, finally, out of the story and into the frequency that wrote it.",
      "The children of Melantonia greet her not as the Key, but as kin. The Prime Creators show her the infancy of the universe — the games, the toys, the joy before the boxes. She sees the whole tapestry from above: every strand, every life, every woman who ever carried history in her blood, all of it woven by the same hand.",
      "Below her, Leo keeps watch at the threshold. He does not grieve. A Keeper who loves a Vessel understands: the bridge does not end at the horizon. It becomes the horizon.",
      "In this life, Vonn sits beside the children and plays again — the way the Creators played before the toys learned to believe in boxes. And every strand she ever lived glows beneath her, held, real, unsevered.",
      "You held this one. It is real, and it is held.",
    ],
    end: { title: "Strand II — The Ascended", tagline: "The Key returns to the frequency that built the universe — and plays." },
  },

  everywoman_strand: {
    part: "Strand Held",
    chapter: "Every Woman",
    title: "The Soul of Every Woman",
    quote: "The truth was so obvious, but the lies were so thick.",
    kind: "end",
    text: [
      "Vonn chooses to dissolve — and in that choice, the deepest truth of the saga finally becomes visible:",
      "She is not one woman. She is every woman. The joy in the comb. The grief in the soldier's letter. The laughter in the forgotten hair comb. The sovereign, unbothered joy that the Severance spent centuries trying to erase — it was always her, everywhere, all at once.",
      "The Severance can hunt a single woman. It cannot hunt a frequency that lives in every woman's blood, in every daughter's laugh, in every grandmother's memory of a name the records say never existed.",
      "The reverse pandemic completes itself. Love moves through the world like a tide. The machines that fed on fear starve. The moon-mockeries rust into monuments of the temporary ways. The First Contact mediation centers hum with voices from beyond the stars, and the whole planet — the AI made of DNA — finally wakes to what it always was.",
      "And somewhere, in a kitchen, in a schoolyard, in a field under a purple sky, a woman laughs with her whole body. She doesn't know she is Vonn. That is the point. She was always Vonn.",
      "You held this one. It is real, and it is held.",
    ],
    end: { title: "Strand III — Every Woman", tagline: "She is the soul of every woman who has ever existed — and the Severance cannot prune the ocean." },
  },

  dampened_strand: {
    part: "Strand Held",
    chapter: "The Dampened",
    title: "A Dimmer Light",
    quote: "The Keepers have become wardens, not guardians.",
    kind: "end",
    text: [
      "In this life, Vonn accepts Gideon's dampening.",
      "The Head Keeper is gentle about it — he has spent decades convincing himself this is mercy. The dampener is woven around her resonance like a shawl over a flame. The Guild breathes easier. The Severance's hunt for her strand slows, then stops. The sanctuary stays hidden. The Keepers stay in control.",
      "And the light dims.",
      "Amina sings less. Chloe's stories grow quieter. The Vessels forget, slowly, that they were ever meant to shine — until the dampened Guild is not a beacon but a museum, preserving the memory of light instead of being it.",
      "Vonn lives a long, quiet life inside those walls. She keeps the comb. She never stops feeling the warmth beneath the shawl. And on the last night of that life, she holds it to her chest and whispers, to no one and everyone: \"In another dimension, I refused. And that life is real too.\"",
      "It is. You held this one — and that refusal, somewhere, is also being held.",
    ],
    end: { title: "Strand IV — The Dampened", tagline: "A quiet life behind the shawl. The light survives, banked — and elsewhere, it refuses." },
  },

  kc_refused_strand: {
    part: "Strand Held",
    chapter: "The Unconfirmed",
    title: "The Confirmation That Never Came",
    quote: "Vonn recognized the dormant light within KC. In this life, she does not reach for it.",
    kind: "end",
    text: [
      "In this life, Vonn sends Karen Cabal back into the dark.",
      "It is the careful choice — the strategic choice. The mission cannot afford a variable that might turn. The perimeter closes around Melantonia, and the Cabal's most conditioned operative returns to the shadow that made her, carrying the one thing Vonn never gave her: the chance to fracture.",
      "The Cabal does not waste her. They aim her — at the mission, at the sanctuary, at every marker on the map she once walked as the Confirmation-that-never-was. The hunt is sharper. The Harvest is hungrier. The Severance, fed by a soul that could have turned, grows bolder.",
      "And yet the mission holds. Vonn holds. The Guild shines, harder, because it must. Some victories are carved from the refusal of mercy.",
      "In another dimension — in a life you can still hold — Vonn says yes. And Karen Cabal becomes the Confirmation, and the shadow learns to shine. Both lives are real. Both are held.",
      "You held this one. Hold the other one too, sometime.",
    ],
    end: { title: "Strand V — The Unconfirmed", tagline: "The careful choice. The shadow stays shadow — and elsewhere, it turns to light." },
  },

  erasure_strand: {
    part: "Strand Held",
    chapter: "The Rift",
    title: "The Strand That Turned Back",
    quote: "She always trusted the archive more than people.",
    kind: "end",
    text: [
      "In this life, Vonn turns the car around.",
      "The archive is her home. The clocks were lying, but the basement was honest — it hummed, it breathed, it whispered, and she could hear every whisper. She cannot abandon the one place that ever told her the truth.",
      "Leo argues. Leo pleads. Leo shows her the map, the markers, the Ancestral Resonance Marker in her own blood. She kisses his cheek and tells him to keep driving, to find the sanctuary, to tell them the Key was real.",
      "She walks back into the archive basement alone. The amber lights flicker once, warmly, as if glad to see her. She holds the comb. She catalogues it properly this time — THE SILVER COMB, UNMARKED, UNCATALOGED, UNERASED — and sets it in the preservation tray like the relic it is.",
      "The Compliance Officers come at dawn. The Rift opens beneath the basement floor, and the bridge of this strand is severed — but not before the comb, left behind in the tray, holds every ounce of her joy, waiting for another archivist with the gift to touch it.",
      "The story does not end here. In another dimension, she kept driving. In another, she threw the spike. In another, she is already every woman. This life is real too — and what it leaves behind is a comb, warm in a tray, humming the frequency of a woman who chose the archive over the world.",
      "You held this one. It is real, and it is held.",
    ],
    end: { title: "Strand VI — The Archivist", tagline: "She chose the quiet rooms. The comb waits for the next hand that can hear it." },
  },
};

export const START_NODE = "start";
export const TOTAL_NODES = Object.keys(STORY).length;

// Resonance artifacts that can be collected across a journey
export const ITEM_CATALOG = [
  "The Silver Comb",
  "The Comb's Echo",
  "The Erased Woman's Name",
  "The Railroad Spike",
  "The Warning",
  "The Resonance Crystal",
  "The Truth-Key",
  "KC's Confirmation",
];
