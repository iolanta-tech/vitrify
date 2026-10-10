---
hide: [toc]
---

# :material-sort-numeric-descending: Top ten metaclasses

With Vitrify installed, run this command in the directory where you want to
save `top-metaclasses/`:

```bash
--8<-- "docs/examples/top-metaclasses/retrieve.sh"
```

The query ranks metaclasses in QLever's Wikidata snapshot by their number of
distinct direct `instance of` (P31) statements. Candidates are explicitly typed
metaclasses: they have an
`instance of` type equal to [metaclass](https://www.wikidata.org/wiki/Q19478619)
or one of its subclasses, such as second-order class. This follows recorded
types, rather than checking that each instance is itself a class. The counts
use truthy P31 values and do not include instances inherited
through subclasses. Ties are resolved by item URI.

{{ directory_preview('top-metaclasses') }}

{{ file_tabs('top-metaclasses') }}
