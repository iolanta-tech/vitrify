---
"@context": urn:vitrify:pages
hide: [toc]
audience: user
---

# :material-file-document-edit-outline: Add an example

Add a Markdown page under `docs/examples/`. Its frontmatter supplies the
SPARQL query, the endpoint URL, and an optional requested format:

````markdown
---
"@context": urn:vitrify:examples
endpoints:
  - https://query.wikidata.org/sparql
format: csv
query: |
  PREFIX wd: <http://www.wikidata.org/entity/>
  PREFIX wdt: <http://www.wikidata.org/prop/direct/>

  SELECT ?person WHERE {
    ?person wdt:P31 wd:Q5 .
  }
  LIMIT 5
---

# Five humans

Retrieve five items classified as humans.
````

Use a descriptive filename and one level-one heading. Keep the query complete.
The result preview shows the first five rows. Omit `format` to let the endpoint
choose its response type. The [CLI reference](../cli.md) lists accepted format
names.

Open a pull request that includes the new page. CI retrieves each changed
example and saves the capture beside that page.

Each capture is a new timestamped directory beside its example. A failed
retrieval stays in the history. Requests keep the CLI's 120-second timeout and
1 GiB response limit.

Keep the page filename when you want to retain its captures. When renaming a
page, move its capture directory and preserve published routes.
