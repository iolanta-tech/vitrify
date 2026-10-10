---
hide: [toc]
---

# :material-layers-triple: Metaclasses of metaclasses

With Vitrify installed, run this command in the directory where you want to
save `metaclasses-of-metaclasses/`:

```bash
--8<-- "docs/examples/metaclasses-of-metaclasses/retrieve.sh"
```

The query finds explicitly typed metaclasses in QLever's Wikidata snapshot
whose recorded direct instances are all explicitly typed metaclasses too.
It requires at least one instance, ranks up to ten matches by distinct
instance count, and shows one example instance per match. Metaclass typing
uses `instance of` (P31), followed by the type's `subclass of` (P279) hierarchy
to [metaclass](https://www.wikidata.org/wiki/Q19478619).

Wikidata calls a class of second-order classes a
[third-order class](https://www.wikidata.org/wiki/Q24017465).
The query also allows mixed or higher orders. It checks recorded truthy P31
values; missing metaclass typing excludes a candidate, and unrecorded
instances cannot be checked. Ties and example instances are selected by URI.

{{ directory_preview('metaclasses-of-metaclasses') }}

{{ file_tabs('metaclasses-of-metaclasses') }}
