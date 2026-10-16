---
hide: [toc]
---

# :material-sort-numeric-descending: Top ten metaclasses

{{ history_chart('top-metaclasses') }}

With Vitrify installed, run this command in the directory where you want to
save `top-metaclasses/`:

```bash
{{ retrieval_command('top-metaclasses') }}
```

The query ranks metaclasses in Wikidata by their number of
distinct direct `instance of` (P31) statements. Candidates are explicitly typed
metaclasses: they have an
`instance of` type equal to [metaclass](https://www.wikidata.org/wiki/Q19478619)
or one of its subclasses, such as second-order class. This follows recorded
types, rather than checking that each instance is itself a class. The counts
use truthy P31 values and do not include instances inherited
through subclasses. Ties are resolved by item URI.

{{ directory_preview('top-metaclasses') }}

{{ file_tabs('top-metaclasses') }}
