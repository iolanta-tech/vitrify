---
title: Parse and write YAML-LD with saphyr
status: decided
date: 2026-11-08
author: Anatoly Scherbakov
tags: [decision]
hide: [toc]
---

# Parse and write YAML-LD with saphyr

{{ adr_metadata(date, status) }}

## :material-text-box-outline: Context

Vitrify parses and writes YAML-LD. That library follows YAML 1.2.

## :material-arrow-decision-outline: Decision

<table data-adr-comparison markdown="1">
  <tr markdown="span">
    <th>Alternative</th>
    <th>YAML 1.2</th>
    <th>Decision</th>
  </tr>
  <tr markdown="span">
    <th class="chosen">[:fontawesome-brands-github: `saphyr-rs/saphyr`](https://github.com/saphyr-rs/saphyr)</th>
    <td class="chosen">[:white_check_mark:](https://github.com/saphyr-rs/saphyr "YAML 1.2 parser and document model")</td>
    <td class="chosen">:white_check_mark: Chosen</td>
  </tr>
  <tr markdown="span">
    <th class="not-selected">[:fontawesome-brands-github: `Ethiraric/yaml-rust2`](https://github.com/Ethiraric/yaml-rust2)</th>
    <td class="not-selected">[:white_check_mark:](https://github.com/Ethiraric/yaml-rust2 "YAML 1.2; directs new work to saphyr")</td>
    <td class="not-selected">:material-minus-circle-outline: Not selected</td>
  </tr>
  <tr markdown="span">
    <th class="not-selected">[:fontawesome-brands-github: `recursive-ai-oss/oneyaml-rust`](https://github.com/recursive-ai-oss/oneyaml-rust)</th>
    <td class="not-selected">[:white_check_mark:](https://github.com/recursive-ai-oss/oneyaml-rust "YAML 1.2 comment-preserving editor")</td>
    <td class="not-selected">:material-minus-circle-outline: Not selected</td>
  </tr>
  <tr markdown="span">
    <th class="not-selected">[:fontawesome-brands-github: `bourumir-wyngs/serde-saphyr`](https://github.com/bourumir-wyngs/serde-saphyr)</th>
    <td class="not-selected">[:white_check_mark:](https://github.com/bourumir-wyngs/serde-saphyr "YAML 1.2")</td>
    <td class="not-selected">:material-minus-circle-outline: Not selected</td>
  </tr>
  <tr markdown="span">
    <th class="excl">[:fontawesome-brands-github: `acatton/serde-yaml-ng`](https://github.com/acatton/serde-yaml-ng)</th>
    <td class="excl hot">[:x:](https://github.com/acatton/serde-yaml-ng/blob/master/README.md "YAML 1.1 only")</td>
    <td class="excl">:x: YAML 1.1 only.</td>
  </tr>
  <tr markdown="span">
    <th class="excl">[:fontawesome-brands-github: `yaml/yaml-serde`](https://github.com/yaml/yaml-serde)</th>
    <td class="excl hot">[:x:](https://github.com/yaml/yaml-serde "YAML 1.1 only")</td>
    <td class="excl">:x: YAML 1.1 only.</td>
  </tr>
  <tr markdown="span">
    <th class="excl">[:fontawesome-brands-github: `cafkafk/serde-norway`](https://github.com/cafkafk/serde-norway)</th>
    <td class="excl hot">[:x:](https://github.com/cafkafk/serde-norway "YAML 1.1 only")</td>
    <td class="excl">:x: YAML 1.1 only.</td>
  </tr>
  <tr markdown="span">
    <th class="excl">[:fontawesome-brands-github: `dtolnay/serde-yaml`](https://github.com/dtolnay/serde-yaml)</th>
    <td class="excl hot">[:x:](https://github.com/dtolnay/serde-yaml "Archived YAML 1.1 crate")</td>
    <td class="excl">:x: Archived.</td>
  </tr>
  <tr markdown="span">
    <th class="excl">[:fontawesome-brands-github: `sebastienrousseau/serde_yml`](https://github.com/sebastienrousseau/serde_yml)</th>
    <td class="excl hot">[:x:](https://github.com/sebastienrousseau/serde_yml "YAML 1.1 only")</td>
    <td class="excl">:x: Deprecated.</td>
  </tr>
</table>

## :material-arrow-right-bold-outline: Consequences

- Parsing and writing YAML-LD uses saphyr.

#### Implementation Steps

- [ ] Parse and write YAML-LD with saphyr.
