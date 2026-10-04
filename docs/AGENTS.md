# Docs audience

This site publishes at https://vitrify.iolanta.tech. Write every page for
the readers below. MkDocs excludes this file from the built site.

## Primary reader

A local-RDF practitioner. They already write SPARQL, keep data in files, and
query those files with tools such as [sparqld](https://sparqld.iolanta.tech).
They use Make or DVC for the pipeline. The remote source they care about most
is **Wikidata**.

They open this site because a Wikidata query result is mutable: the same
request later can return different bytes, or fail. They want one deliberate
retrieval written to disk as an ordinary file, with enough attached evidence
to know what was fetched. After that, they work on the file — not the
endpoint.

Assume SPARQL, Wikidata prefixes, and a local Unix/RDF workflow. Do not assume
they already know RO-Crate, `Accept`, or content negotiation. Explain those
only as far as they change what Vitrify writes.

Wikidata is the default example endpoint. Other SPARQL services are in scope;
they are not the landing story.

## Also: coding agents

The same pages must be executable by a coding agent working in a repository.
Give complete commands, paths, and flags. Do not hide argv in prose or split
a working invocation across a paragraph and a partial snippet.

Do not write a separate "for agents" track. One command, one crate, one
result file. A human copies it; an agent runs it.

## Voice

Lead with a Wikidata SPARQL command and the file it produced. The result file
is the hero; `ro-crate-metadata.json` is attached evidence, not a wrapper.

The next step after Vitrify is local work (sparqld, Unix tools, Make/DVC) on
that file. Vitrify is not a workflow runner and must not be invoked again
unless the reader explicitly wants a new retrieval.
