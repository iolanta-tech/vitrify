---
hide: [toc]
---

# :material-layers: Fourth-order classes

With Vitrify installed, run this command in the directory where you want to
save `fourth-order-classes/`:

```bash
--8<-- "docs/examples/fourth-order-classes/retrieve.sh"
```

The query lists all items in QLever's Wikidata snapshot whose recorded
`instance of` (P31) type is
[fourth-order class](https://www.wikidata.org/wiki/Q24027474) or a subclass
of that type, ordered by English label and item URI. A fourth-order class has
third-order classes as its instances. This query selects recorded types;
it does not check the order of every instance.

The captured match is labeled **third-order class**: it names the collection
of third-order classes, so the collection itself is fourth-order.

{{ directory_preview('fourth-order-classes') }}

{{ file_tabs('fourth-order-classes') }}
