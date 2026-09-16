# Red team

Run before the synthesis of every investigation, by a reader who did not write it. With an agent: a fresh session or a subagent with read access only. Replace `<investigation>`.

```
Working directory: this repo. Change no files.

Role: red team. Your job is to break the investigation, not to confirm it.

Read investigations/<investigation>/README.md, every study-NN/README.md and study-NN/frozen/protocol.json under it, method/README.md, and the register entries the investigation cites in knowledge/registry.json, including the snapshot each points at.

Attack along five lines:

1. Convenient conclusion. Would this conclusion be comfortable for the author, the funder or the supervisor? Look in both directions: a conclusion that flatters the hypothesis, and one that looks self-critical, since that is the cheapest way to appear objective.

2. Selection of evidence. Which sources would a hostile reviewer cite that the investigation does not? Which cited excerpt, read in full, says less than the reading claims? Check the anchor against the snapshot.

3. The measure. Does the measure in the protocol measure what the argument chain claims? Could it move for a reason unrelated to the hypothesis? Were the thresholds justified or picked to be passable?

4. The competing hypothesis. Is it a straw man? Write the strongest rival a competent opponent would put forward, and check whether the study could distinguish it from the hypothesis.

5. Generalisation. Where does the synthesis reach beyond the sample, the data kind, the setting or the period? Which limitation in a study README is missing from the synthesis?

Deliver a Markdown report of at most 800 words. Objections ordered by severity. For each: what it hits (file and section), why, and what resolves it: change the claim, add a study, add a limitation, or mark as undecided. No politeness.
```

Write what the red team found and what changed into the synthesis, dated and marked "after red team".
