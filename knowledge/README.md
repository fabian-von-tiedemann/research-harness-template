# Knowledge register

`registry.json` holds three lists: `sources`, `claims`, `documents`. Every claim points at the excerpt it rests on; every excerpt is a hashed snapshot in `snapshots/`. Documents are the chapters and reports that depend on claims. `INDEX.md` is generated. The validator checks declarations, never truth.

## Add a source

1. Put the excerpt you will cite in a text file. For a paper, the paragraphs you read with a citation line at the top. For a dataset, the file itself. For an interview, the de-identified passage.
2. `python3 -m harness snapshot <file>`. It copies the file into `snapshots/<sha256>.txt` and prints a source entry with `sha256`, `snapshot` and `anchor` filled in.
3. Paste the entry into `sources`, set `id`, `kind`, `origin` and `access`.
4. `python3 -m harness validate`.

Source kinds: `literature` (published work), `transcript` (interview or observation record), `empirical_report` (a study's reported results), `dataset`, `model_trial` (output of a model run you made), `analysis` (a derived analysis, yours or someone else's), `note` (unverified working note).

## Add a claim

Template in `method/templates.md`. `type` says what kind of thing it is. `status` says how much the evidence carries. `review_status` says whether anyone other than the author checked. `reconsider_if` is mandatory and concrete. `evidence[].anchor` must equal the source's anchor: you cite the preserved excerpt, not a line range you remember.

## When a source changes

Add a new source entry with a new `version` and the same `family`; keep the old one. Then:

```sh
python3 -m harness impact S001
```

It lists every claim and document that rests on the source, directly or through other claims, as review proposals. Nothing changes status automatically.

## Give an agent the right context

```sh
python3 -m harness context K003 K007
```

Prints the claims, everything they depend on, and the source excerpts inlined, with a log of why each record was included.

## Personal data

Never put a transcript with identifiable people into `snapshots/` until de-identification has been decided and done. The register is committed to git; git remembers. Where raw data live, how long they are kept and how they are de-identified belongs in your data management plan, not here.
