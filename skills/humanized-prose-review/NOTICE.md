# Notice

`references/humanizer-4.0.0.md` is a modified copy of the `SKILL.md` from
[blader/humanizer](https://github.com/blader/humanizer), version 4.0.0
(commit b48c832). The modifications are Copyright (c) 2026 Ethan Kent and
are released under the same MIT License.

The copy differs from upstream 4.0.0 in these places, and is otherwise
unchanged:

- Patterns 12 through 18: the example passages under "Before" and
  "After" were replaced with original ones. The labels, the blank lines
  above them, and the rest of each pattern are upstream's, except as
  listed below.
- Pattern 15: the named example inside the "Problem" text ("Roger Ebert
  highlighted the lasting influence") was replaced with an unnamed one
  ("the reviewer emphasized its lasting influence").
- Pattern 20: the two emoji in the "Before (emojis)" example were
  replaced with descriptions of them ("[rocket emoji]" and "[light-bulb
  emoji]").
- The rule against adding facts is kept from 3.1.0, because
  humanized-prose-review forbids invented details. Upstream 4.0.0
  removed it. The opening line keeps "Do not make anything up."; step 2
  of "How to work" keeps its 3.1.0 wording ("Do not add a fact, name,
  number, date, quote, or citation unless it comes from the source or
  the user", through "Fiction is exempt because invented detail is the
  task.") in place of upstream's "Where the text is generic, add a
  specific detail you know to be true."; step 3 checks whether the
  rewrite "added, dropped, or changed" a fact and treats an unsupported
  addition as an error, where upstream checks only "dropped or changed";
  and the "Problem" text of patterns 14 and 17 keeps its 3.1.0 wording,
  which names only relationships and sources the source text gives.

Humanizer's patterns are drawn from Wikipedia's
[Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
maintained by WikiProject AI Cleanup. No text from that page is reproduced
here; the link is given as credit for the ideas.

`references/researched-tells.md` summarizes findings from the sources it
links, in its own words. `scripts/detect.py` calls Open Pangram (EditLens),
SlopTotal, Pangram and GPTZero when a user installs or subscribes to them.
None of their code or weights are included here. EditLens is CC BY-NC-SA 4.0,
so its code must not be copied into this skill.

The original is distributed under the following license:

```
MIT License

Copyright (c) 2025 Siqi Chen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
