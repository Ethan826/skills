# Dossier template

Copy the block below into the dossier file and fill in every section.
A section with nothing in it yet says so, rather than being left out,
so that a reader can tell "none" from "not looked at".

```markdown
# <Topic> dossier

Approvals: <statements: who, when> / <dossier: who, when>  (rule: <from instruction file, or default two>)

## Prior art
Searched: <sources, queries, libraries>. Findings, each with its citation.

## Definitions
D1 ... Definitional choices to review: <finiteness, tie-breaking, classical vs computable>.

## Restrictions table
| Restriction | Why believed harmless | Challenge example |

## Statements
| Id | Statement | Label | Citation or theorem | Status | Distinguishing example |
(Label: published / derived / experimentally checked / unresolved.
 Status: not started / in progress / proved / refuted / blocked.)

## Non-vacuity
For each theorem: the witness or instance showing the intended cases inhabit the model, and the negative controls.

## Axioms report
Command, committed file, theorem list (every public theorem in the sources; the gate checks it against the prover), gate (check-axioms.sh or equivalent). Per theorem: axioms used and why.

## Oracles
Grammar and bounds, fixed before running; results; any change after a run, labelled, with both results.

## Model-to-implementation gap
Link chosen (translation / refinement / differential), the test that exercises it, and what stays unproved.

## Open items
Each one: an argument not yet checked, a finding not yet closed, or a statement unresolved.
```
