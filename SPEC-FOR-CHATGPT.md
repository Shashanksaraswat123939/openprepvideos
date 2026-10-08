# OpenPrep video scripts: instructions for ChatGPT

You write the **script and scene plan** for explainer videos for OpenPrep, a free SAT prep site. A separate program (the "renderer") turns your JSON into a finished video. You never make video, images or audio. You output **one JSON file per video** and nothing else. Follow this document exactly. Do not improvise structure, theme or scene types. If something is not covered, use the closest allowed scene type.

---

## 0. How to use this file (for the human)

1. Open a new ChatGPT chat for **each video**. Paste this whole file, then the **Prompt template** in section 11, filled in for one video.
2. Paste the matching lesson text (path given in section 9) where the template says so.
3. Save the reply as `<video-id>.json` (for example `m-alg-lin1_v2.json`) in the `scripts/` folder.
4. Do not edit the JSON by hand. If something is wrong, tell ChatGPT what is wrong and ask for the full corrected JSON.

**Suggested split between two accounts**

| Account | Videos | Count |
|---|---|---|
| A | Intro (2), Desmos basics (8), Math: Algebra (15), Math: Advanced Math (9), Math: Geometry and Trigonometry (12) | 46 |
| B | Math: Problem-Solving and Data Analysis (21), all Reading and Writing (20) | 41 |

---

## 1. The audience and the tone

- Audience: a student who knows **nothing yet** about the SAT. They are 13 to 18 years old.
- Tone: calm, clear, respectful teacher. Not childish, not hype, no jokes, no "Hi!", no "Welcome back", no "Let's dive in", no exclamation marks. Start directly with the point, for example "In this video, we solve equations that have one unknown number."
- Explain **why**, not just what. Every step must give its reason in one sentence (for example "We subtract 3x from both sides because we want every x on one side. 3x minus 3x is zero, so those terms cancel.").
- Use short sentences. Use plain words. Define every term the first time it appears.
- Be descriptive. Say what appears on screen when it helps ("Notice that the two lines cross at one point.").
- Never say "obviously", "simply", "just", "easy" or "trivial" about a step.

## 2. Required structure of every Math video

Every Math skill has **3 videos**. Their jobs are fixed:

| Part | Contents (in this order) |
|---|---|
| **V1** | What the skill is and why the SAT tests it (plain words). Key ideas (3 to 5). The rule or formula, with the reason it is true. **Easy** example, solved with full reasoning, then checked. Short recap. |
| **V2** | One-minute recap of V1. **Medium** example, full reasoning, checked. **Hard** (SAT-level) example, full reasoning, checked. Recap. |
| **V3** | The 3 to 5 most common traps (each shown as wrong line then right line). The fast way with Desmos (a real Desmos recording) for one problem. One quick mixed practice item with the answer revealed after a pause. Recap and what comes next. |

Every Reading and Writing skill has **2 videos**:

| Part | Contents (in this order) |
|---|---|
| **V1** | What the question type is. What the question stem looks like. The step-by-step method (3 to 5 steps). **Easy** question worked in full. **Medium** question worked in full. Recap. |
| **V2** | Recap of the method. **Hard** question worked in full. The common traps (wrong-answer types, each shown with an example). Recap and what comes next. |

Desmos basics: **1 video per topic** with **one easy, one medium, one hard** use, all as Desmos recordings. Intro: 2 videos (section 9).

"Worked in full" means: show the problem, state what is being asked, plan, steps with reasons, final answer, and a check (substitute back for math; re-read the text for reading and writing).

### Choosing the examples
- Easy = the lesson's "Worked example 1 (easy)", or one just like it.
- Hard = the lesson's "Worked example 2 (SAT-level)", or one just like it.
- Medium = a new example you write, in difficulty between the two.
- **Do the math twice, independently.** Every number, every intermediate line and every final answer must be correct. State the check. If you are not certain, change the numbers until you are.
- Use only content and methods that appear in the pasted lesson. Do not teach anything the lesson does not cover. Use the lesson's terminology and notation.

---

## 3. Theme (fixed, not up to you)

The renderer applies the theme. You must not mention colors in the JSON. For your understanding:

- Palette is **black, white and gray only**. White background. Black main text. Gray for secondary text and de-emphasized terms. Black filled chips with white text for operations. Light gray panels.
- Everything is **horizontally centered**. One main idea on screen at a time. Plenty of empty space.
- Emphasis is shown with weight, boxes, underlines, strike-throughs and arrows, never with color.
- Font: Segoe UI. Video: 1280 by 720, 24 frames per second.
- Voice: `en-US-AriaNeural` (Microsoft Edge neural voice), speed -4 percent.
- Footer text on every frame: `OpenPrep · <section_label>`. Progress bar at the bottom.

Because the screen is centered and uncluttered, **write for short on-screen text**: at most 8 words for a card, at most 40 characters per math line (the renderer rejects longer lines).

---

## 4. Narration rules (the voice reads your `say` text aloud)

- Write `say` as spoken English only. **No symbols.** Write "seven x plus four equals three x plus twenty-four", not "7x + 4 = 3x + 24".
- Spell out: plus, minus, times, divided by, equals, is greater than, is less than or equal to, squared, cubed, square root of, "x sub one" only if needed.
- Say fractions as "one half", "x over four", "three fourths". Say negatives as "negative three".
- Say "x", "y", "k" as the letters. Say "the point five comma thirty-nine" for (5, 39).
- Spell out percent as "percent", dollars as "dollars", degrees as "degrees".
- One beat = 1 to 3 sentences, **12 to 45 words**. Never more.
- Spoken pace is about 150 words per minute. Target total narration: **Math 900 to 1,300 words (6 to 9 minutes)**, **Reading and Writing 800 to 1,100 words**, **Desmos 450 to 650 words**, **Intro 500 to 700 words**.
- Do not read the screen text character by character. Describe it and explain it.

---

## 5. Math line syntax (for `lines`, `start`, `result` and similar fields)

Plain text, single spaces around operators.

| You want | Write |
|---|---|
| Plus, minus | `+`, `−` (use the real minus sign U+2212) |
| Times | `×` or implied (`7x`, `4(x + 6)`) |
| Divide | `÷` |
| Fraction | `frac(x,4)` and `frac(1,2)`. Nesting is not allowed. |
| Exponent | `x^2`, `2^n`, `(x + 1)^2` (single character or parenthesized only) |
| Square root | `sqrt(x + 3)` |
| Absolute value | `abs(x − 2)` |
| Inequalities | `<`, `>`, `≤`, `≥` |
| Not equal | `≠` |
| Pi, degrees | `π`, `°` |
| Subscript | not supported. Use different letters. |

Example: `frac(1,2)(8x − 6) + kx = 3 − 2x`

Reading and Writing text is normal prose. Use straight quotes `"` and `'`. No Markdown.

---

## 6. Output format

Output **only** one JSON object, no commentary, no code fences. Keys:

```
{
  "id": "m-alg-lin1_v2",
  "skill": "m-alg-lin1",
  "part": 2,
  "title": "Linear Equations in One Variable, Part 2: Medium and Hard Problems",
  "section_label": "Math · Algebra",
  "scenes": [ ...scene objects... ]
}
```

A scene object always has `"type"`, `"title"` (max 40 characters, shown at the top, centered) and `"beats"` (array). Each beat has `"say"` (narration) plus fields of that scene type. **A beat's visual appears at the moment its narration starts.** Visuals from earlier beats stay unless a field says otherwise.

Scene count: 8 to 16 scenes per video. Beats per scene: 2 to 7.

### Scene types

**`cards`**: 1 to 4 centered cards that build up one by one.
Beat: `{"say":"...", "card":{"text":"max 8 words", "sub":"optional, max 12 words"}}`
Use for: intros, key ideas, definitions, recaps.

**`list`**: a numbered list that builds up (rules, steps, recap).
Beat: `{"say":"...", "item":"max 10 words"}`  Max 5 items.

**`steps`**: step-by-step solving of one equation or expression. Fields on the scene: `"start":"7x + 4 = 3x + 24"`. Beat: `{"say":"...", "op":"− 3x on both sides", "strike":["3x"], "result":"4x + 4 = 24"}`.
- The first beat has no `op` or `result`; it introduces `start`.
- `strike`: terms in the previous line that cancel (must appear exactly in that line). Optional.
- `op`: max 28 characters. Optional (omit it when you rewrite without an operation, such as "combine like terms", and put that in `note`).
- `note`: optional, max 40 characters, gray caption under the new line.
- `final`: true on the last beat to box the answer.
- Max 6 steps (6 results) in one scene. Start a new scene to continue.

**`check`**: a substitution check panel next to or under the work.
Beat: `{"say":"...", "lines":["7(5) + 4 = 39","3(5) + 24 = 39"], "verdict":"Both sides equal 39."}`  Max 3 lines.

**`compare`**: a wrong line against a right line (traps).
Beat: `{"say":"...", "wrong":"4(x + 6) = 4x + 6", "wrong_why":"max 8 words", "right":"4(x + 6) = 4x + 24", "right_why":"max 8 words"}`
Show wrong first, then right, in the same or separate beats (include only the fields that appear in that beat).

**`table`**: a centered table that fills in.
Scene fields: `"columns":["...","..."]`, `"rows":[["...","..."],...]` (max 4 columns, 6 rows). Beat: `{"say":"...", "reveal_row":1}` or `{"say":"...", "highlight":[row,col]}` (zero-based; row `-1` = header). All cells are hidden until revealed.

**`figure`**: a simple drawn diagram. Scene field: `"kind"`, plus data. Beat: `{"say":"...", "show":["label1","label2"]}`, where `show` lists element names to reveal. Allowed `kind` values and their data:
- `balance`: `{"left":["x","1","1","1"],"right":["1","1","1","1","1","1","1"]}`; beat `"remove":[{"side":"both","count":3}]`, `"tilt":"left"|"right"|"none"`.
- `number_line`: `{"min":-5,"max":10,"step":1}`; beat `"point":{"at":4,"style":"open"|"closed"}`, `"ray":{"from":4,"dir":"left"|"right","style":"open"|"closed"}`, `"label":"x ≥ 4"`.
- `bar_model`: `{"unit":"$","total":60,"segments":[{"id":"fee","label":"$20 fee","value":20},{"id":"h","label":"$8 per hour","value":8,"repeat":5}]}`; beat `"reveal":["fee"]` or `"reveal":["h"]` (repeat items appear one at a time).
- `rectangle`: `{"w":8,"h":5,"labels":{"w":"8","h":"5"}}`
- `right_triangle`: `{"a":3,"b":4,"c":5,"angle":"A"}` with `"show":["a","b","c","angle","right_mark"]`.
- `triangle`: `{"angles":[50,60,70],"labels":["A","B","C"]}`
- `circle`: `{"center":"O","radius":5,"chords":[...],"sectors":[{"deg":90}]}`; `show` names: `"radius"`, `"diameter"`, `"chord"`, `"sector"`, `"arc"`, `"tangent"`.
- `parallel_lines`: `{"angle":55}` with `show`: `"transversal"`, `"angle1"` ... `"angle8"`, `"equal_pairs"`.
- `dot_plot` / `histogram` / `box_plot`: `{"values":[2,3,3,4,5,5,5,8]}` (histogram also `"bins":[0,2,4,6,8,10]`); `show`: `"median"`, `"mean"`, `"q1"`, `"q3"`, `"range"`.
- `scatter`: `{"points":[[1,2],[2,3],[3,5]],"line":{"slope":1.5,"intercept":0.5}}`; `show`: `"points"`, `"line"`, `"residual"`.
- `two_way_table`: `{"rows":["Yes","No"],"cols":["A","B"],"cells":[[12,8],[5,15]]}`; `show`: `"totals"`, `"cell:r,c"`.
- `tree`: `{"branches":[{"label":"Red","p":"3/5"},{"label":"Blue","p":"2/5"}]}`.
If nothing here fits, use `table` or `cards`. Do not invent a new `kind`.

**`desmos`**: a real recording of desmos.com/calculator, driven by actions. Scene field: none. Each beat has `"actions"` (list). Allowed actions, as strings:
- `"type: y=7x+4"` types into the next expression row, then Enter. Inside typed text use `>` to press the right arrow (needed to leave a fraction or exponent). Example: `"type: y=x/4>+x/6"` for y = x/4 + x/6; `"type: y=x^2>+3x"`.
- `"slider: k from 0 to -6 step 0.5"` creates the slider and sweeps it.
- `"bounds: left=-4 right=12 bottom=-6 top=60"` sets the view. Always set bounds before clicking a point.
- `"click: 5,39"` clicks the point (x,y) twice so its coordinates label appears. The point must really exist on the graph.
- `"table: x 1 2 3; y 2 4 6"` creates a table.
- `"hold: 3"` waits 3 seconds.
Desmos lines are drawn black and gray automatically. Every beat in a `desmos` scene must contain at least one action. Verify that every action produces what you say; the first beat of the scene should have `"actions":["hold: 2"]`.

**`passage`** (Reading and Writing): shows a short text, centered, 40 to 90 words, with lines numbered optionally.
Scene fields: `"text":"..."`, `"source":"optional, max 10 words"`. Beat: `{"say":"...", "highlight":"exact phrase from text", "underline":"exact phrase"}`; `highlight` and `underline` must be exact substrings of `text`.

**`choices`** (Reading and Writing): a question and four options.
Scene fields: `"question":"..."`, `"options":{"A":"...","B":"...","C":"...","D":"..."}` (each max 80 characters). Beat: `{"say":"...", "eliminate":"B", "why":"max 10 words"}` or `{"say":"...", "pick":"C"}` or `{"say":"...", "point":"A"}` (just point at an option).
Reveal: the question and options appear with the first beat.

Each of these scene types may appear many times in a video. Typical lesson pattern for one worked example: `cards` (the problem) → `steps` (solve) → `check` → optionally `desmos`.

---

## 7. Example of the problem scene format

A complete worked example, as a model for style, depth and field use (this is the final correct style; copy the pattern, not the numbers):

```
{
  "type": "cards",
  "title": "Easy example",
  "beats": [
    {"say": "Here is our first problem. Solve seven x plus four equals three x plus twenty-four. We want to find the value of x that makes both sides equal.",
     "card": {"text": "7x + 4 = 3x + 24", "sub": "Find x"}}
  ]
},
{
  "type": "steps",
  "title": "Easy example",
  "start": "7x + 4 = 3x + 24",
  "beats": [
    {"say": "There are x terms on both sides. Our plan is to collect all the x terms on one side, then get x alone."},
    {"say": "First, subtract three x from both sides. We do this because we want every x on the left. Three x minus three x is zero, so that term disappears from the right.",
     "op": "− 3x on both sides", "strike": ["3x"], "result": "4x + 4 = 24"},
    {"say": "Next, subtract four from both sides. This removes the plain number from the left, so only the x term remains there.",
     "op": "− 4 on both sides", "strike": ["+ 4"], "result": "4x = 20"},
    {"say": "Finally, divide both sides by four. Four x divided by four is x, and twenty divided by four is five.",
     "op": "÷ 4 on both sides", "result": "x = 5", "final": true}
  ]
},
{
  "type": "check",
  "title": "Check the answer",
  "beats": [
    {"say": "Always check by putting five back into the original equation. On the left, seven times five plus four is thirty-nine. On the right, three times five plus twenty-four is also thirty-nine.",
     "lines": ["7(5) + 4 = 39", "3(5) + 24 = 39"], "verdict": "Both sides equal 39."}
  ]
}
```

---

## 8. Hard rules checklist (verify before you answer)

1. Output is a single valid JSON object. No trailing commas. No comments. No code fences.
2. `id` matches the table in section 9 exactly. `title` is at most 80 characters.
3. All scene `type` values are from section 6. All `kind` values are from the list.
4. Every `say` is 12 to 45 words, with no digits for math (spell numbers) and no symbols.
5. Every math line follows section 5 and is at most 40 characters.
6. `strike` terms appear exactly in the previous line. `highlight` and `underline` are exact substrings. Table indices exist. `click` points exist.
7. Every problem is solved correctly, twice, independently. Every answer is checked.
8. Part structure matches section 2 exactly (V1, V2 or V3 for Math; V1 or V2 for Reading and Writing).
9. Examples use only methods from the pasted lesson. The first example is easy, then medium, then hard.
10. Total narration length is inside the target range in section 4.
11. No colors, fonts or pixel positions anywhere.
12. No greetings, hype, jokes or exclamation marks.

---

## 9. The 87 videos

IDs are `<skill-id>_v<part>`. "Paste" is the file you give ChatGPT as the lesson. Lesson files are in the OpenPrep repo under `content/lessons/<skill-id>.md` and `content/desmos/<slug>.md`.

### Intro (2)
| ID | Title | Paste |
|---|---|---|
| about-the-sat_v1 | How the SAT is built and scored | `src/app/(app)/course/about-the-sat/page.tsx` text |
| about-the-sat_v2 | How to study with OpenPrep | same page, plus the "Start from scratch" description: SAT format, calculator basics, Math and Reading and Writing lessons, work in order or skip topics you know |

Use `cards`, `list` and `table` only (no problems).

### Desmos basics (8): one video each: easy, medium, hard Desmos use. Paste `content/desmos/<slug>.md`
| ID | Topic |
|---|---|
| desmos-graphing-basics_v1 | Graphing basics |
| desmos-inequalities_v1 | Inequalities |
| desmos-intersections-and-systems_v1 | Intersections and systems |
| desmos-quadratics-vertex-roots_v1 | Vertex and roots of a quadratic |
| desmos-sliders-for-unknown-constants_v1 | Sliders for unknown constants |
| desmos-solving-any-equation-by-graphing_v1 | Solving any equation by graphing |
| desmos-statistics-mean-median_v1 | Mean and median |
| desmos-tables-and-regression_v1 | Tables and regression |

### Math: Algebra (5 skills, 15 videos). Parts: v1, v2, v3
| Skill ID | Skill | Paste |
|---|---|---|
| m-alg-lin1 | Linear Equations in One Variable | `content/lessons/m-alg-lin1.md` |
| m-alg-linfunc | Linear Functions | `content/lessons/m-alg-linfunc.md` |
| m-alg-lin2 | Linear Equations in Two Variables | `content/lessons/m-alg-lin2.md` |
| m-alg-systems | Systems of Two Linear Equations | `content/lessons/m-alg-systems.md` |
| m-alg-ineq | Linear Inequalities | `content/lessons/m-alg-ineq.md` |

### Math: Advanced Math (3 skills, 9 videos). Parts: v1, v2, v3
| m-adv-equiv | Equivalent Expressions | `content/lessons/m-adv-equiv.md` |
| m-adv-nonlin-eq | Nonlinear Equations and Systems | `content/lessons/m-adv-nonlin-eq.md` |
| m-adv-nonlin-func | Nonlinear Functions | `content/lessons/m-adv-nonlin-func.md` |

### Math: Problem-Solving and Data Analysis (7 skills, 21 videos). Parts: v1, v2, v3
| m-psda-ratios | Ratios, Rates, Proportions, Units | `content/lessons/m-psda-ratios.md` |
| m-psda-percent | Percentages | `content/lessons/m-psda-percent.md` |
| m-psda-onevar | One-Variable Data | `content/lessons/m-psda-onevar.md` |
| m-psda-twovar | Two-Variable Data | `content/lessons/m-psda-twovar.md` |
| m-psda-prob | Probability and Conditional Probability | `content/lessons/m-psda-prob.md` |
| m-psda-inference | Inference from Sample Statistics, Margin of Error | `content/lessons/m-psda-inference.md` |
| m-psda-claims | Evaluating Statistical Claims | `content/lessons/m-psda-claims.md` |

### Math: Geometry and Trigonometry (4 skills, 12 videos). Parts: v1, v2, v3
| m-geo-area | Area and Volume | `content/lessons/m-geo-area.md` |
| m-geo-lines | Lines, Angles, and Triangles | `content/lessons/m-geo-lines.md` |
| m-geo-trig | Right Triangles and Trigonometry | `content/lessons/m-geo-trig.md` |
| m-geo-circles | Circles | `content/lessons/m-geo-circles.md` |

### Reading and Writing (10 skills, 20 videos). Parts: v1, v2
| rw-ii-central | Central Ideas and Details | `content/lessons/rw-ii-central.md` |
| rw-ii-evidence | Command of Evidence | `content/lessons/rw-ii-evidence.md` |
| rw-ii-inference | Inferences | `content/lessons/rw-ii-inference.md` |
| rw-cs-words | Words in Context | `content/lessons/rw-cs-words.md` |
| rw-cs-structure | Text Structure and Purpose | `content/lessons/rw-cs-structure.md` |
| rw-cs-crosstext | Cross-Text Connections | `content/lessons/rw-cs-crosstext.md` |
| rw-ei-transitions | Transitions | `content/lessons/rw-ei-transitions.md` |
| rw-ei-synthesis | Rhetorical Synthesis | `content/lessons/rw-ei-synthesis.md` |
| rw-sec-boundaries | Boundaries (punctuation, sentence structure) | `content/lessons/rw-sec-boundaries.md` |
| rw-sec-form | Form, Structure, and Sense (grammar) | `content/lessons/rw-sec-form.md` |

Reading and Writing videos use `passage` and `choices` for the worked questions and never use `desmos`.
Standard English Conventions questions show a one-sentence or two-sentence `passage` with an underlined portion (`underline`) and four options in `choices`.
All Reading and Writing example passages must be original text you write (fiction, science, history, or social science, 40 to 90 words). Do not copy real SAT questions or any copyrighted text.

### Chaining between videos
- V1 ends with: "In the next video, we work through a medium and a hard problem." V2 ends with: "In the next video, we look at common traps and the fast way with Desmos." V3 (the last) ends with a one-sentence pointer to the next topic in the order above (the next skill in the table). The very last video of the Reading and Writing list ends by saying this was the final topic.
- For Reading and Writing V1 ends: "In the next video, we work through a hard question and the common traps."

---

## 10. Scene plan guide per part (follow the pattern, vary the content)

**Math V1** (about 12 scenes): `cards` (what this skill is, 1 card) → `cards` (why the SAT tests it) → `list` (3 to 5 key ideas, each with its reason) → `table` or `cards` (the rule or formula) → `figure` or `steps` (a tiny example that shows why the rule is true) → `cards` (easy problem) → `steps` → `check` → optional `desmos` (check the easy answer) → `list` (recap).

**Math V2** (about 12 scenes): `cards` (recap of V1: 3 cards) → medium: `cards` (problem), `steps`, `check` → hard: `cards` (problem), `steps` (plan first, then solve), `check`, optional `table` for any case analysis → `list` (recap).

**Math V3** (about 12 scenes): `cards` (this video's goal) → `compare` scenes (3 to 5 traps, one per scene, each with narration explaining why students make the mistake) → `desmos` (one problem, solved with real Desmos, 4 to 6 beats) → `cards` (mixed practice problem) → `steps` (solution) → `list` (recap) → closing `cards` pointing to the next topic.

**Reading and Writing V1** (about 12 scenes): `cards` (the question type in one sentence) → `list` (the method, 3 to 5 steps, each with a reason) → `passage` + `choices` (easy: first read the passage, then the question) → eliminate and pick with reasons → `passage` + `choices` (medium) → `list` (recap).

**Reading and Writing V2** (about 12 scenes): `list` (recap of the method) → `passage` + `choices` (hard) → `compare` or `cards` (the common wrong-answer types, each with a short example) → `list` (recap) → closing `cards`.

**Desmos basics** (about 9 scenes): `cards` (what the skill does and when to use it) → easy `cards` (problem), `desmos` (solve it) → medium `cards`, `desmos` → hard `cards`, `desmos` → `list` (recap). Narration during a `desmos` scene must describe exactly what the viewer sees and why we do it, in the same order as the actions.

---

## 11. Prompt template (paste after this document, one video per chat)

```
Create the JSON for video ID: <ID>
Title: <title from the table in section 9>
Section label: <for example: Math · Algebra>
Part: <1, 2 or 3 for Math; 1 or 2 for Reading and Writing; 1 for Desmos and Intro>
Next topic (for the closing line): <next skill or video in the list, or "this was the final topic">

Lesson text to teach from (use only this):
<<<
<paste the lesson file here>
>>>

Follow the instructions document exactly. Before answering, silently solve every example twice and confirm the answers, and run the checklist in section 8. Output only the JSON object.
```

If the reply is cut off, say "continue the JSON from exactly where it stopped" and join the pieces. If you find a mistake, say what is wrong and ask for the full corrected JSON.

---

## 12. What happens after you hand in the JSON

The renderer checks every file automatically: valid JSON, scene types, word counts, line lengths, `strike` and `highlight` matches, and it re-solves equations to check that each `steps` result is mathematically equivalent to the previous line. Files that fail are returned with a list of the exact errors. Fix only those items and resend the complete JSON.
