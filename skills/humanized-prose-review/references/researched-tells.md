# Researched tells

These patterns come from a survey of published research and practitioner
writing in November 2026. Humanizer 3.1.0 and the additional tells do not
list them, or list only part of them. Each entry gives its evidence, so you
can weigh it:

- Measured: a study with a stated corpus and method.
- Vendor: measured by a company that sells detection or humanizing,
  with little method published.
- Editors: Wikipedia editors' observation from cleanup work.
- Anecdote: forum or blog reports with no counts.

`**Lint:**` gives the `tell_lint.py` rule, or says none when only an auditor
can judge the tell. No single entry proves anything. Word habits change with
model releases, so distrust a vendor's word list sooner than a structural
pattern.

## Sentence structure

### R1. Participial clauses in general

**Evidence:** Measured. Instruction-tuned models use present participial
clauses at 2 to 5 times the human rate (Reinhart et al.).
**Watch for:** a clause after a comma that opens with an -ing verb, whatever
the verb: "The job finished early, leaving the queue empty." §15 is limited to
riders that claim significance.
**Fix:** Give the second event its own subject and verb, or cut it. Keep a
participle that says how or when something happened and reads naturally.
**Lint:** `participial-clause`

### R2. Nominalization chains

**Evidence:** Measured. Nominalizations run at 1.5 to 2 times the human rate
(Reinhart et al.), and The Economist found more Latinate suffixes than in
human text.
**Watch for:** nouns ending in -tion, -ment, -ance or -ence joined by *of*:
"the implementation of the validation".
**Fix:** Turn the main noun back into a verb with a named actor.
**Lint:** `nominal-chain`

### R3. A "that" clause as the subject

**Evidence:** Measured. Reinhart et al. give 173 to 331 percent of the human
rate, read here from a summary of the paper's appendix, so check its Table 3
before quoting this.
**Watch for:** "That the build failed suggests..."
**Fix:** Start with the fact: "The build failed, which suggests..."
**Lint:** none

### R4. Long sentences joined by "and"

**Evidence:** Measured. Models write long sentences with little variety in
length. They use fewer commas and semicolons than people, hardly any
parentheses, and "and" more than any other word (The Economist, 55,940
sentences, read through an excerpt). GPT-4o avoided clausal coordination in
Reinhart et al., so this varies by model.
**Watch for:** three or more *and*s in one sentence, and the sentence metrics
in the lint report.
**Fix:** Split the sentence where the logic turns, and use the punctuation
that says how the parts relate.
**Lint:** `and-chain`

## Word habits

### R6. Claude's stock phrases

**Evidence:** Anecdote from Hacker News threads, Claude forums and a Claude
Code issue. Extends A1 and §12.
**Watch for:** load-bearing (figurative), worth stating plainly, carry the
argument, full stop (as a closer), "and the trap", the crux, first-class
citizen, honest take, the honest answer, sit with that, belt and suspenders,
smoking gun.
**Fix:** Say what the thing does. Keep *load-bearing* for walls.
**Lint:** `claude-phrase`, `load-bearing`, `full-stop`, `claude-idiom`

### R7. Claude's word swaps

**Evidence:** Anecdote from one Hacker News thread, read through a summary.
Extends A1.
**Watch for:** *names* as a verb for *says* or *lists*; *verdict* for
*result*; *judge* for *validate*.
**Fix:** Use the plain word.
**Lint:** `name-verb`

### R8. "It changes no behavior"

**Evidence:** Anecdote from the same thread.
**Watch for:** a verb followed by *no* and a noun where English would use
*does not*: "the list contains no string".
**Fix:** "The list doesn't contain a string."
**Lint:** `verb-no`

### R9. Caveat shapes from 2026

**Evidence:** Editors. Wikipedia's page says these were extremely uncommon
before mid-2026.
**Watch for:** "does not establish", "should not be confused with", and
"rather than" used as a caveat.
**Fix:** State the limit directly, or cut a caveat nobody needs.
**Lint:** `caveat-shape`, `rather-than`

### R10. Stock frames

**Evidence:** Vendor. WriteHuman's list comes from 80,141 pairs that compare
AI input with its own humanized output. No human writing is in the comparison.
**Watch for:** plays a role, crucial role in, role in shaping, ensuring that,
while maintaining, aligns well with, is essential for, shaped by.
**Fix:** Say how one thing acts on the other.
**Lint:** `stock-frame`

### R11. Reminder and insight phrases

**Evidence:** Vendor. Pangram's n-gram ratios run into the thousands, with no
published sample.
**Watch for:** as a poignant, a powerful reminder, reminder of the enduring,
faced numerous challenges, newfound sense of purpose, even in the face of, in
today's fast-paced world, in the ever-evolving, important to note, paving the
way, shed light on, complex interplay, valuable insights; the words realm,
moreover, multifaceted, nuanced, camaraderie, palpable, profoundly.
**Fix:** Cut the phrase, then see whether the sentence still says anything.
**Lint:** `stock-phrase`, `shed-light`, `research-word`

### R12. Stock scenes and reviews

**Evidence:** Vendor (Pangram's phrase lists). Mostly fiction and reviews, so
rare in technical prose.
**Watch for:** took a slow sip, weight of unspoken, recently had the
pleasure, highly recommend, game-changer.
**Fix:** Write what happened.
**Lint:** `scene-stock`

### R13. Default names

**Evidence:** Vendor, April 2025, with no method and possibly stale. Pangram
says Emily or Sarah made up 60 to 70 percent of names in AI articles.
**Watch for:** either name in an invented example.
**Fix:** Use a less obvious name, or a real example.
**Lint:** `default-name`

### R18. Stiff waffle

**Evidence:** Anecdote from editors at an ACES session, reported by Poynter.
**Watch for:** it can be argued that, broadly speaking, and an arch tone.
**Fix:** Make the claim, or say who argues it.
**Lint:** `waffle`

### R19. A near synonym in the wrong register

**Evidence:** Anecdote. Kory Stamper, reported by Poynter, says AI "fails at
contingency": *parsimonious* for lean staffing, *facile* for simple.
**Watch for:** a word that fits the dictionary but not the setting.
**Fix:** Use the word a person in that setting would use.
**Lint:** none

### R21. Synonym cycling

**Evidence:** Editors, citing Huang et al. Wikipedia lists this as dated.
**Watch for:** the same thing called three names in a row to avoid repeating
a word.
**Fix:** Repeat the word. A reader takes a new name for a new thing.
**Lint:** none

## What is missing

### R5. Absent specifics

**Evidence:** Measured for quotation (The Economist: models "do not quote
experts"); vendor for the rest (Pangram).
**Watch for:** no quoted person, few proper nouns, no first-hand experience,
no local knowledge, no criticism of any view, relentless positivity.
**Fix:** Ask the author for the detail. Never invent one to fill the gap.
Wikipedia's editors, citing Geng and Trotta and Reinhart et al., list forms
people use more: *there
is a*, *wrote*, *died*, *very*, *perhaps*, *tends to*, *in order to*, *the
fact that*. Leave these alone.
**Lint:** none

### R20. Saying a subject is minor, then praising it

**Evidence:** Editors.
**Watch for:** a preamble granting that the subject is small, followed by a
claim of its importance anyway.
**Fix:** Keep the facts and drop both moves.
**Lint:** none

## Format and residue

### R14. Decorative Unicode

**Evidence:** Vendor. Pangram lists box drawing, the approximately sign, the
warning sign and arrows; check marks and keycap digits lead its emoji list.
**Watch for:** those characters in prose. Arrows are in §20.
**Fix:** Use words: *about 5 minutes*, *Warning:*, *done*.
**Lint:** `decor-unicode`

### R15. Markdown in plain text

**Evidence:** Vendor and Editors. Pangram reports bold at 43 times and headers
at 23 times the human rate. Wikipedia calls stray triple backticks among the
least ambiguous signs.
**Watch for:** literal asterisks, hashes, backticks or `[text](url)` in a
commit message, email or other plain-text target.
**Fix:** Remove the syntax. Run the lint with `--plain` for such targets.
**Lint:** `markdown-leak`

### R16. The template essay

**Evidence:** Vendor (Pangram's guide to AI writing patterns).
**Watch for:** paragraphs of near-equal length, a long conclusion opening
*Overall* or *In summary*, a first sentence that repeats the request.
**Fix:** End on the last new fact. Let paragraphs run as long as their point.
**Lint:** `conclusion-opener`

### R17. The edit-summary formula

**Evidence:** Editors, about Wikipedia edit summaries; it applies directly to
commit messages and PR descriptions.
**Watch for:** stacked assurances ("for clarity and compliance"), "preserving
the original meaning", service tone ("carefully reviewed", "apologize for any
inconvenience").
**Fix:** Say what changed and why.
**Lint:** `commit-formula`

### R22. Citation and template residue

**Evidence:** Editors. An invalid ISBN checksum is a very likely sign. A
`utm_source=chatgpt.com` link shows only that a chatbot found the source.
**Watch for:** invalid ISBNs; DOIs that fail to resolve or lead elsewhere;
`utm_source=openai`, `utm_source=chatgpt.com`, `utm_source=copilot.com`,
`referrer=grok.com`; placeholders such as `2026-xx-xx`,
`INSERT_SOURCE_URL_HERE`, `[Describe the section here]`.
**Fix:** Check every citation against its source, and remove what fails. The
lint checks ISBNs and strings only, so an auditor must resolve DOIs.
**Lint:** `url-residue`, `placeholder`, `isbn-checksum`

## Reading the evidence

- Em dashes are a Claude signal now. The Economist found only Claude still
  above the human rate, and Pangram found Gemini 3 Pro below it. §8 still
  applies as a style rule, but a clean dash count says little about other
  models.
- Sources disagree. Pangram says AI avoids semicolons, while explainx,
which sells training, lists semicolon antithesis as a Claude habit. WriteHuman found semicolon rates and
  sentence length barely changed by humanizing. Treat rhythm metrics as
  prompts for an auditor.

## Sources

- Reinhart et al., [Do LLMs write like humans?](https://arxiv.org/html/2410.16107v1)
- Shaib et al., [Measuring AI "Slop" in Text](https://arxiv.org/html/2509.19163)
- The Economist, ["How to spot AI writing"](https://www.economist.com/culture/2026/07/30/how-to-spot-ai-writing), read through [an excerpt](https://daringfireball.net/linked/2026/08/11/economist-ai-writing)
- Pangram, [9 Signs of AI Writing](https://www.pangram.com/signs-of-ai-writing), [spotting patterns](https://www.pangram.com/blog/comprehensive-guide-to-spotting-ai-writing-patterns), [overused phrases](https://www.pangram.com/blog/walking-through-ai-phrases)
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- [WriteHuman](https://writehuman.ai/blog/ai-tells-in-2026), which sells a humanizer
- [Poynter](https://www.poynter.org/reporting-editing/2026/ai-changing-human-writing-editors-em-dash/)
- [explainx](https://explainx.ai/blog/claude-opus-5-load-bearing-claudisms-writing-tells-2026) and [a Hacker News summary](https://zeli.app/en/story/49461817), both anecdotal
