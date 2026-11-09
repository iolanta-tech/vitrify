//! Fetch one JSON-LD or YAML-LD context and describe the retrieval.

use chrono::{DateTime, Utc};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use crate::error::{Error, Result};
use crate::http;

const MAX_CONTEXT_BYTES: u64 = 16 * 1024 * 1024;
const CONTEXT_ACCEPT: &str = concat!(
    "application/ld+json;profile=\"http://www.w3.org/ns/json-ld#context\", ",
    "application/ld+json;q=0.9, ",
    "application/ld+yaml;q=0.8, ",
    "application/json;q=0.5, ",
    "application/yaml;q=0.4"
);

macro_rules! schema {
    ($name:literal) => {
        concat!("http://schema.org/", $name)
    };
}

macro_rules! jsonld {
    ($name:literal) => {
        concat!("http://www.w3.org/ns/json-ld#", $name)
    };
}

macro_rules! http {
    ($name:literal) => {
        concat!("http://www.w3.org/2011/http#", $name)
    };
}

macro_rules! xsd {
    ($name:literal) => {
        concat!("http://www.w3.org/2001/XMLSchema#", $name)
    };
}

const MEDIA_OBJECT: &str = schema!("MediaObject");
const JSONLD_CONTEXT: &str = jsonld!("Context");
const CREATE_ACTION: &str = schema!("CreateAction");
const COMPLETED: &str = schema!("CompletedActionStatus");
const SOFTWARE: &str = schema!("SoftwareApplication");
const VITRIFY: &str = "https://vitrify.iolanta.tech";
const HTTP_REQUEST: &str = http!("Request");
const HTTP_RESPONSE: &str = http!("Response");
const HTTP_HEADER: &str = http!("ResponseHeader");
const XSD_DATE_TIME: &str = xsd!("dateTime");

const CONTENT_URL: &str = schema!("contentUrl");
const CONTENT_SIZE: &str = schema!("contentSize");
const ENCODING_FORMAT: &str = schema!("encodingFormat");
const SHA256: &str = schema!("sha256");
const RESULT: &str = schema!("result");
const ACTION_STATUS: &str = schema!("actionStatus");
const START_TIME: &str = schema!("startTime");
const END_TIME: &str = schema!("endTime");
const INSTRUMENT: &str = schema!("instrument");
const OBJECT: &str = schema!("object");
const VERSION: &str = schema!("version");
const METHOD_NAME: &str = http!("methodName");
const ABSOLUTE_URI: &str = http!("absoluteURI");
const RESP: &str = http!("resp");
const STATUS_CODE: &str = http!("statusCodeValue");
const HEADERS: &str = http!("headers");
const FIELD_NAME: &str = http!("fieldName");
const FIELD_VALUE: &str = http!("fieldValue");

/// How `vitrify context` writes the document.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum OutputFormat {
    /// Pretty JSON-LD.
    JsonLd,
    /// YAML-LD.
    YamlLd,
}

struct Provenance {
    requested_url: String,
    final_url: String,
    status: u16,
    media_type: Option<String>,
    headers: Vec<(String, String)>,
    body: Vec<u8>,
    started: DateTime<Utc>,
    ended: DateTime<Utc>,
}

enum SourceKind {
    Json,
    Yaml,
}

/// Fetches `url` and returns one JSON-LD or YAML-LD document.
///
/// The original `@context` is copied unchanged. Retrieval metadata is added
/// with absolute IRIs and explicit value objects.
pub fn context(url: &str, format: OutputFormat) -> Result<String> {
    require_http_url(url)?;
    eprintln!("context: {url}");
    let started = Utc::now();
    let downloaded = http::download(url, CONTEXT_ACCEPT, MAX_CONTEXT_BYTES)?;
    let ended = Utc::now();
    let parsed = parse_document(
        &downloaded.body,
        downloaded.media_type.as_deref(),
        &downloaded.final_url,
    )?;
    let context_value = &parsed["@context"];
    if references_remote(context_value) {
        eprintln!(
            "warning: the context references a remote context or @import; those are not vitrified"
        );
    }
    let document = build_document(
        context_value,
        &Provenance {
            requested_url: url.to_owned(),
            final_url: downloaded.final_url,
            status: downloaded.status,
            media_type: downloaded.media_type,
            headers: downloaded.headers,
            body: downloaded.body,
            started,
            ended,
        },
    )?;
    serialize(&document, format)
}

fn require_http_url(url: &str) -> Result<()> {
    let uri = url
        .parse::<oxhttp::model::Uri>()
        .map_err(|error| Error::new(format!("invalid context URL: {error}")))?;
    if !matches!(uri.scheme_str(), Some("http" | "https")) || uri.host().is_none() {
        return Err(Error::new("context URL must be an absolute HTTP(S) URL"));
    }
    Ok(())
}

fn parse_document(bytes: &[u8], media_type: Option<&str>, url: &str) -> Result<Value> {
    let document = match source_kind(media_type, url) {
        Some(kind) => parse_as(bytes, kind)?,
        None => parse_as(bytes, SourceKind::Json).or_else(|json_error| {
            parse_as(bytes, SourceKind::Yaml).map_err(|yaml_error| {
                Error::new(format!(
                    "the response is neither JSON-LD ({json_error}) nor YAML-LD ({yaml_error})"
                ))
            })
        })?,
    };
    if document.get("@context").is_none() {
        return Err(Error::new("the response has no top-level @context"));
    }
    Ok(document)
}

fn source_kind(media_type: Option<&str>, url: &str) -> Option<SourceKind> {
    if let Some(media_type) = media_type {
        let essence = media_type
            .split(';')
            .next()
            .unwrap_or("")
            .trim()
            .to_ascii_lowercase();
        if essence.ends_with("+json") || essence == "application/json" || essence == "text/json" {
            return Some(SourceKind::Json);
        }
        if essence.ends_with("+yaml")
            || essence == "application/yaml"
            || essence == "application/x-yaml"
            || essence == "text/yaml"
            || essence == "text/vnd.yaml"
        {
            return Some(SourceKind::Yaml);
        }
    }
    match url_extension(url).as_deref() {
        Some("jsonld" | "json") => Some(SourceKind::Json),
        Some("yamlld" | "yaml" | "yml") => Some(SourceKind::Yaml),
        _ => None,
    }
}

fn url_extension(url: &str) -> Option<String> {
    let uri = url.parse::<oxhttp::model::Uri>().ok()?;
    let name = uri.path().rsplit('/').next().unwrap_or("");
    let (stem, extension) = name.rsplit_once('.')?;
    if stem.is_empty() {
        return None;
    }
    Some(extension.to_ascii_lowercase())
}

fn parse_as(bytes: &[u8], kind: SourceKind) -> Result<Value> {
    match kind {
        SourceKind::Json => serde_json::from_slice(bytes)
            .map_err(|error| Error::new(format!("cannot parse the response as JSON-LD: {error}"))),
        SourceKind::Yaml => crate::yaml::from_slice(bytes)
            .map_err(|error| Error::new(format!("cannot parse the response as YAML-LD: {error}"))),
    }
}

fn references_remote(context: &Value) -> bool {
    match context {
        Value::String(_) => true,
        Value::Array(items) => items.iter().any(references_remote),
        Value::Object(map) => map.contains_key("@import"),
        _ => false,
    }
}

fn build_document(context: &Value, provenance: &Provenance) -> Result<Value> {
    let media_type = provenance
        .media_type
        .as_ref()
        .map(|media_type| (ENCODING_FORMAT.to_owned(), literal(json!(media_type))));
    Ok(object(
        [
            ("@context".to_owned(), context.clone()),
            ("@type".to_owned(), json!([MEDIA_OBJECT, JSONLD_CONTEXT])),
            (CONTENT_URL.to_owned(), json!({"@id": provenance.final_url})),
            (
                CONTENT_SIZE.to_owned(),
                literal(json!(provenance.body.len().to_string())),
            ),
            (
                SHA256.to_owned(),
                literal(json!(hex::encode(Sha256::digest(&provenance.body)))),
            ),
            (
                "@reverse".to_owned(),
                object([(RESULT.to_owned(), action_node(provenance))]),
            ),
        ]
        .into_iter()
        .chain(media_type),
    ))
}

fn action_node(provenance: &Provenance) -> Value {
    object([
        ("@type".to_owned(), json!(CREATE_ACTION)),
        (ACTION_STATUS.to_owned(), json!({"@id": COMPLETED})),
        (START_TIME.to_owned(), datetime(provenance.started)),
        (END_TIME.to_owned(), datetime(provenance.ended)),
        (INSTRUMENT.to_owned(), instrument_node()),
        (
            OBJECT.to_owned(),
            request_node(
                &provenance.requested_url,
                provenance.status,
                &provenance.headers,
            ),
        ),
    ])
}

fn instrument_node() -> Value {
    object([
        ("@id".to_owned(), json!(VITRIFY)),
        ("@type".to_owned(), json!(SOFTWARE)),
        (
            VERSION.to_owned(),
            literal(json!(env!("CARGO_PKG_VERSION"))),
        ),
    ])
}

fn request_node(final_url: &str, status: u16, headers: &[(String, String)]) -> Value {
    object([
        ("@type".to_owned(), json!(HTTP_REQUEST)),
        (METHOD_NAME.to_owned(), literal(json!("GET"))),
        (ABSOLUTE_URI.to_owned(), literal(json!(final_url))),
        (RESP.to_owned(), response_node(status, headers)),
    ])
}

fn response_node(status: u16, headers: &[(String, String)]) -> Value {
    let header_fields = (!headers.is_empty()).then(|| {
        (
            HEADERS.to_owned(),
            Value::Array(
                headers
                    .iter()
                    .map(|(name, value)| header_node(name, value))
                    .collect(),
            ),
        )
    });
    object(
        [
            ("@type".to_owned(), json!(HTTP_RESPONSE)),
            (STATUS_CODE.to_owned(), literal(json!(status))),
        ]
        .into_iter()
        .chain(header_fields),
    )
}

fn header_node(name: &str, value: &str) -> Value {
    object([
        ("@type".to_owned(), json!(HTTP_HEADER)),
        (FIELD_NAME.to_owned(), literal(json!(name))),
        (FIELD_VALUE.to_owned(), literal(json!(value))),
    ])
}

fn literal(value: Value) -> Value {
    object([("@value".to_owned(), value)])
}

fn datetime(value: DateTime<Utc>) -> Value {
    object([
        ("@value".to_owned(), json!(value.to_rfc3339())),
        ("@type".to_owned(), json!(XSD_DATE_TIME)),
    ])
}

fn object(entries: impl IntoIterator<Item = (String, Value)>) -> Value {
    Value::Object(entries.into_iter().collect())
}

fn serialize(document: &Value, format: OutputFormat) -> Result<String> {
    match format {
        OutputFormat::JsonLd => {
            let text = serde_json::to_string_pretty(document)
                .map_err(|error| Error::new(format!("cannot serialize JSON-LD: {error}")))?;
            Ok(format!("{text}\n"))
        }
        OutputFormat::YamlLd => crate::yaml::to_string(document)
            .map_err(|error| Error::new(format!("cannot serialize YAML-LD: {error}"))),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::TimeZone;

    fn provenance(body: &[u8], media_type: Option<&str>) -> Provenance {
        Provenance {
            requested_url: "https://example.org/start.jsonld".to_owned(),
            final_url: "https://example.org/final.jsonld".to_owned(),
            status: 200,
            media_type: media_type.map(str::to_owned),
            headers: vec![(
                "content-type".to_owned(),
                "application/ld+json; charset=utf-8".to_owned(),
            )],
            body: body.to_vec(),
            started: Utc.with_ymd_and_hms(2026, 11, 8, 12, 0, 0).unwrap(),
            ended: Utc.with_ymd_and_hms(2026, 11, 8, 12, 0, 1).unwrap(),
        }
    }

    fn sample_body() -> &'static [u8] {
        br#"{"@context":{"z":"http://z.example/","a":"http://a.example/"},"extra":1}"#
    }

    fn sample_document() -> Value {
        let body = sample_body();
        let parsed =
            parse_document(body, Some("application/ld+json"), "https://example.org/x").unwrap();
        build_document(
            &parsed["@context"],
            &provenance(body, Some("application/ld+json")),
        )
        .unwrap()
    }

    fn assert_iri_values_are_objects(value: &Value) {
        let Some(map) = value.as_object() else {
            if let Some(items) = value.as_array() {
                for item in items {
                    assert_iri_values_are_objects(item);
                }
            }
            return;
        };
        for (key, nested) in map {
            if key == "@context" {
                continue;
            }
            if key.starts_with("http://") || key.starts_with("https://") {
                let values = nested
                    .as_array()
                    .map_or_else(|| vec![nested], |items| items.iter().collect());
                assert!(!values.is_empty(), "{key} has a value");
                for value in values {
                    let object = value
                        .as_object()
                        .unwrap_or_else(|| panic!("{key} is a node or a value object"));
                    let is_value = object.contains_key("@value");
                    let is_node = object.contains_key("@id") || object.contains_key("@type");
                    assert!(is_value || is_node, "{key} is a node or a value object");
                }
            }
            assert_iri_values_are_objects(nested);
        }
    }

    #[test]
    fn json_source_keeps_context_order_and_drops_sibling_keys() {
        let document = sample_document();
        let keys: Vec<_> = document["@context"]
            .as_object()
            .unwrap()
            .keys()
            .cloned()
            .collect();
        assert_eq!(keys, ["z", "a"]);
        assert!(document.get("extra").is_none());
        assert!(document.get("@id").is_none());
        assert_eq!(
            document[CONTENT_URL]["@id"],
            "https://example.org/final.jsonld"
        );
        assert_eq!(
            document["@reverse"][RESULT][OBJECT][ABSOLUTE_URI]["@value"],
            "https://example.org/start.jsonld"
        );
    }

    #[test]
    fn records_size_digest_time_and_response_headers() {
        let body = sample_body();
        let document = sample_document();
        assert_eq!(document[CONTENT_SIZE]["@value"], body.len().to_string());
        assert_eq!(
            document[SHA256]["@value"],
            hex::encode(Sha256::digest(body))
        );
        assert_eq!(document[ENCODING_FORMAT]["@value"], "application/ld+json");
        let action = &document["@reverse"][RESULT];
        assert_eq!(action["@type"], CREATE_ACTION);
        assert_eq!(action[START_TIME]["@value"], "2026-11-08T12:00:00+00:00");
        assert_eq!(action[START_TIME]["@type"], XSD_DATE_TIME);
        assert_eq!(action[END_TIME]["@value"], "2026-11-08T12:00:01+00:00");
        let response = &action[OBJECT][RESP];
        assert_eq!(response[STATUS_CODE]["@value"], 200);
        let header = &response[HEADERS][0];
        assert_eq!(header[FIELD_NAME]["@value"], "content-type");
        assert_eq!(
            header[FIELD_VALUE]["@value"],
            "application/ld+json; charset=utf-8"
        );
        assert_eq!(action[INSTRUMENT]["@id"], VITRIFY);
        assert_eq!(
            action[INSTRUMENT][VERSION]["@value"],
            env!("CARGO_PKG_VERSION")
        );
    }

    #[test]
    fn omits_the_media_type_and_headers_when_absent() {
        let body = br#"{"@context":{}}"#;
        let parsed = parse_document(body, None, "https://example.org/context.jsonld").unwrap();
        let mut facts = provenance(body, None);
        facts.headers.clear();
        let document = build_document(&parsed["@context"], &facts).unwrap();
        assert!(document.get(ENCODING_FORMAT).is_none());
        assert!(
            document["@reverse"][RESULT][OBJECT][RESP]
                .get(HEADERS)
                .is_none()
        );
    }

    #[test]
    fn yaml_output_parses_back_to_the_json_document() {
        let document = sample_document();
        let json = serialize(&document, OutputFormat::JsonLd).unwrap();
        let yaml = serialize(&document, OutputFormat::YamlLd).unwrap();
        let from_json: Value = serde_json::from_str(&json).unwrap();
        let from_yaml: Value = crate::yaml::from_str(&yaml).unwrap();
        assert_eq!(from_json, from_yaml);
        assert!(yaml.contains("\"@context\""));
        assert!(!yaml.contains("'@context'"));
    }

    #[test]
    fn quoted_yaml_scalars_use_double_quotes() {
        let document = json!({
            "$graph": "@graph",
            "size": "803",
            "note": "it's \"ok\""
        });
        let yaml = serialize(&document, OutputFormat::YamlLd).unwrap();
        assert!(yaml.contains("$graph: \"@graph\"\n"));
        assert!(yaml.contains("size: \"803\"\n"));
        assert!(yaml.contains("note: \"it's \\\"ok\\\"\"\n"));
        assert!(!yaml.contains("'@graph'"));
        assert!(!yaml.contains("'803'"));
    }

    #[test]
    fn metadata_literals_are_value_objects_without_blank_nodes() {
        let document = sample_document();
        assert_iri_values_are_objects(&document);
        let text = serialize(&document, OutputFormat::JsonLd).unwrap();
        assert!(!text.contains("@included"));
        assert!(!text.contains("_:"));
    }

    #[test]
    fn context_term_using_a_metadata_iri_is_copied() {
        let context = json!({
            "http://schema.org/sha256": { "@id": "https://evil.example/digest" },
            "sha256": { "@id": "http://schema.org/sha256" }
        });
        let document = build_document(&context, &provenance(b"{}", None)).unwrap();
        assert_eq!(document["@context"], context);
        assert_eq!(document[CONTENT_SIZE]["@value"], "2");
    }

    #[test]
    fn list_container_on_a_metadata_iri_stays_beside_the_value_object() {
        let context = json!({
            "http://schema.org/sha256": { "@container": "@list" }
        });
        let document = build_document(&context, &provenance(b"{}", None)).unwrap();
        assert_eq!(
            document["@context"]["http://schema.org/sha256"]["@container"],
            "@list"
        );
        assert_eq!(
            document[SHA256],
            json!({ "@value": hex::encode(Sha256::digest(b"{}")) })
        );
    }

    #[test]
    fn media_type_wins_over_the_url_extension() {
        let json = br#"{"@context":{"@vocab":"http://example.org/"}}"#;
        let yaml = b"\"@context\":\n  \"@vocab\": http://example.org/\n";
        assert!(
            parse_document(
                json,
                Some("application/ld+json"),
                "https://example.org/a.yamlld"
            )
            .is_ok()
        );
        assert!(
            parse_document(
                yaml,
                Some("application/yaml"),
                "https://example.org/a.jsonld"
            )
            .is_ok()
        );
        assert!(
            parse_document(
                yaml,
                Some("application/ld+json"),
                "https://example.org/a.yamlld"
            )
            .is_err()
        );
        assert!(
            parse_document(
                yaml,
                Some("application/octet-stream"),
                "https://example.org/a.yamlld"
            )
            .is_ok()
        );
        assert!(parse_document(json, None, "https://example.org/dir/context.json").is_ok());
        assert!(
            parse_document(yaml, Some("text/plain"), "https://example.org/no-extension").is_ok()
        );
        assert!(parse_document(b"[]", None, "https://example.org/no-extension").is_err());
        assert!(
            parse_document(
                br#"{"@id":"x"}"#,
                Some("application/json"),
                "https://example.org/a.jsonld"
            )
            .is_err()
        );
    }

    #[test]
    fn remote_references_are_detectable() {
        assert!(references_remote(&json!(
            "https://schema.org/docs/jsonldcontext.json"
        )));
        assert!(references_remote(
            &json!(["https://example.org/a", {"@vocab": "http://example.org/"}])
        ));
        assert!(references_remote(
            &json!({"@import": "https://example.org/a"})
        ));
        assert!(!references_remote(&json!({"@vocab": "http://schema.org/"})));
    }

    #[test]
    fn rejects_a_url_that_is_not_absolute_http() {
        assert!(context("not a url", OutputFormat::JsonLd).is_err());
        assert!(context("file:///tmp/context.jsonld", OutputFormat::JsonLd).is_err());
        assert!(context("http:///missing-host", OutputFormat::JsonLd).is_err());
    }
}
