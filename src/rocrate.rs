//! RO-Crate 1.2 JSON-LD for one SPARQL retrieval.
//!
//! The crate is the package (`./`) plus the result and query files linked with
//! `hasPart`. Attached evidence records the endpoint, SHA-256 of both files,
//! and a `CreateAction` for the HTTP exchange.

use chrono::{DateTime, Utc};
use serde_json::json;

const CONTEXT: &str = "https://w3id.org/ro/crate/1.2/context";
const PROFILE: &str = "https://w3id.org/ro/crate/1.2";
const DESCRIPTOR_ID: &str = "ro-crate-metadata.json";
const ROOT_ID: &str = "./";

/// RO-Crate requires a root `license`. Vitrify is endpoint-agnostic and cannot
/// know the retrieved data's license, so it asserts none rather than inventing
/// one; the spec permits a textual license describing how the crate may be used.
const LICENSE_NOTICE: &str =
    "No license asserted by Vitrify; consult the source endpoint's terms of use.";

/// The fixed name of the metadata file inside a crate.
pub const METADATA_FILE_NAME: &str = DESCRIPTOR_ID;
/// The executed query snapshot stored inside each crate.
pub const QUERY_FILE_NAME: &str = "query.rq";

/// Observed facts of one successful SPARQL retrieval, enough to describe the
/// result file and the exchange that produced it.
pub struct Retrieval {
    pub result_name: String,
    pub media_type: Option<String>,
    pub byte_size: u64,
    pub sha256: String,
    pub query_byte_size: u64,
    pub query_sha256: String,
    pub endpoint: String,
    pub accept: Option<String>,
    pub status: u16,
    pub final_url: String,
    pub started: DateTime<Utc>,
    pub ended: DateTime<Utc>,
}

/// Builds an RO-Crate 1.2 metadata document for one SPARQL result.
pub fn metadata_json(retrieval: &Retrieval) -> String {
    let mut result_file = json!({
        "@id": retrieval.result_name,
        "@type": "File",
        "contentSize": retrieval.byte_size.to_string(),
        "sha256": retrieval.sha256,
    });
    if let Some(media_type) = &retrieval.media_type {
        result_file["encodingFormat"] = json!(media_type);
    }
    let query_file = json!({
        "@id": QUERY_FILE_NAME,
        "@type": "File",
        "contentSize": retrieval.query_byte_size.to_string(),
        "encodingFormat": "application/sparql-query",
        "sha256": retrieval.query_sha256,
    });

    let retrieval_description = match retrieval.accept.as_deref() {
        Some(accept) => format!("HTTP {}; Accept: {accept}", retrieval.status),
        None => format!("HTTP {}; Accept: omitted", retrieval.status),
    };
    let document = json!({
        "@context": CONTEXT,
        "@graph": [
            {
                "@id": DESCRIPTOR_ID,
                "@type": "CreativeWork",
                "conformsTo": { "@id": PROFILE },
                "about": { "@id": ROOT_ID },
            },
            {
                "@id": ROOT_ID,
                "@type": "Dataset",
                "name": retrieval.result_name,
                "description": "SPARQL retrieval materialized by Vitrify.",
                "datePublished": retrieval.ended.to_rfc3339(),
                "license": LICENSE_NOTICE,
                "hasPart": [
                    { "@id": retrieval.result_name },
                    { "@id": QUERY_FILE_NAME },
                ],
                "publisher": { "@id": retrieval.endpoint },
                "author": { "@id": "https://vitrify.iolanta.tech" },
            },
            result_file,
            query_file,
            {
                "@id": "https://vitrify.iolanta.tech",
                "@type": "SoftwareApplication",
                "name": "Vitrify",
                "url": "https://vitrify.iolanta.tech",
                "version": env!("CARGO_PKG_VERSION"),
            },
            {
                "@id": retrieval.endpoint,
                "@type": "Organization",
            },
            {
                "@id": "#retrieval",
                "@type": "CreateAction",
                "startTime": retrieval.started.to_rfc3339(),
                "endTime": retrieval.ended.to_rfc3339(),
                "instrument": { "@id": "https://vitrify.iolanta.tech" },
                "agent": { "@id": "https://vitrify.iolanta.tech" },
                "object": [
                    { "@id": retrieval.endpoint },
                    { "@id": QUERY_FILE_NAME },
                ],
                "result": { "@id": retrieval.result_name },
                "identifier": retrieval.final_url,
                "description": retrieval_description,
            },
        ],
    });

    let mut text = serde_json::to_string_pretty(&document).expect("the document is serializable");
    text.push('\n');
    text
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::TimeZone;
    use serde_json::Value;

    const EMPTY_SHA256: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

    fn sample(result_name: &str, media_type: Option<&str>, byte_size: u64) -> Retrieval {
        Retrieval {
            result_name: result_name.to_owned(),
            media_type: media_type.map(str::to_owned),
            byte_size,
            sha256: EMPTY_SHA256.to_owned(),
            query_byte_size: 28,
            query_sha256: EMPTY_SHA256.to_owned(),
            endpoint: "https://query.wikidata.org/sparql".to_owned(),
            accept: Some("text/csv".to_owned()),
            status: 200,
            final_url: "https://query.wikidata.org/sparql".to_owned(),
            started: Utc.with_ymd_and_hms(2026, 9, 27, 12, 0, 0).unwrap(),
            ended: Utc.with_ymd_and_hms(2026, 9, 27, 12, 0, 1).unwrap(),
        }
    }

    fn graph(doc: &str) -> Vec<Value> {
        let value: Value = serde_json::from_str(doc).expect("valid JSON");
        value["@graph"].as_array().expect("@graph array").clone()
    }

    fn entity(graph: &[Value], id: &str) -> Value {
        graph
            .iter()
            .find(|e| e["@id"] == id)
            .unwrap_or_else(|| panic!("entity {id} present"))
            .clone()
    }

    fn object_ids(action: &Value) -> Vec<&str> {
        action["object"]
            .as_array()
            .expect("CreateAction object is an array")
            .iter()
            .map(|item| item["@id"].as_str().expect("@id"))
            .collect()
    }

    #[test]
    fn records_media_type_and_size() {
        let doc = metadata_json(&sample("female-persons.csv", Some("text/csv"), 42));
        let graph = graph(&doc);

        let descriptor = entity(&graph, "ro-crate-metadata.json");
        assert_eq!(descriptor["@type"], "CreativeWork");
        assert_eq!(descriptor["about"]["@id"], "./");
        assert_eq!(descriptor["conformsTo"]["@id"], PROFILE);

        let root = entity(&graph, "./");
        assert_eq!(root["@type"], "Dataset");
        assert!(root["license"].is_string());
        assert!(root["datePublished"].is_string());
        assert_eq!(root["hasPart"][0]["@id"], "female-persons.csv");

        let file = entity(&graph, "female-persons.csv");
        assert_eq!(file["@type"], "File");
        assert_eq!(file["encodingFormat"], "text/csv");
        assert_eq!(file["contentSize"], "42");
    }

    #[test]
    fn records_sha256_of_the_result() {
        let mut retrieval = sample("female-persons.csv", Some("text/csv"), 42);
        retrieval.sha256 =
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".into();
        let file = entity(&graph(&metadata_json(&retrieval)), "female-persons.csv");
        assert_eq!(
            file["sha256"],
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        );
    }

    #[test]
    fn records_the_executed_query_file() {
        let mut retrieval = sample("out.csv", Some("text/csv"), 1);
        retrieval.query_byte_size = 46;
        retrieval.query_sha256 =
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".into();
        let query = entity(&graph(&metadata_json(&retrieval)), QUERY_FILE_NAME);
        assert_eq!(query["@type"], "File");
        assert_eq!(query["encodingFormat"], "application/sparql-query");
        assert_eq!(query["contentSize"], "46");
        assert_eq!(query["sha256"], retrieval.query_sha256);
    }

    #[test]
    fn create_action_links_software_query_endpoint_and_file() {
        let retrieval = sample("out.csv", Some("text/csv"), 1);
        let graph = graph(&metadata_json(&retrieval));
        let action = entity(&graph, "#retrieval");
        assert_eq!(action["@type"], "CreateAction");
        assert_eq!(action["instrument"]["@id"], "https://vitrify.iolanta.tech");
        assert_eq!(action["agent"]["@id"], "https://vitrify.iolanta.tech");
        assert_eq!(action["result"]["@id"], "out.csv");
        let objects = object_ids(&action);
        assert!(objects.contains(&"https://query.wikidata.org/sparql"));
        assert!(objects.contains(&QUERY_FILE_NAME));
        assert_eq!(action["identifier"], "https://query.wikidata.org/sparql");
        assert_eq!(action["description"], "HTTP 200; Accept: text/csv");
        assert_eq!(action["startTime"], "2026-09-27T12:00:00+00:00");
        assert_eq!(action["endTime"], "2026-09-27T12:00:01+00:00");

        let software = entity(&graph, "https://vitrify.iolanta.tech");
        assert_eq!(software["@type"], "SoftwareApplication");
        assert_eq!(software["name"], "Vitrify");
        assert_eq!(software["url"], "https://vitrify.iolanta.tech");
        assert_eq!(software["version"], env!("CARGO_PKG_VERSION"));
    }

    #[test]
    fn dataset_publisher_is_the_endpoint() {
        let retrieval = sample("out.csv", Some("text/csv"), 1);
        let graph = graph(&metadata_json(&retrieval));
        let root = entity(&graph, "./");
        assert_eq!(
            root["publisher"]["@id"],
            "https://query.wikidata.org/sparql"
        );
        let endpoint = entity(&graph, "https://query.wikidata.org/sparql");
        assert_eq!(endpoint["@type"], "Organization");
    }

    #[test]
    fn omits_media_type_when_absent() {
        let doc = metadata_json(&sample("out.bin", None, 0));
        let file = entity(&graph(&doc), "out.bin");
        assert!(file.get("encodingFormat").is_none());
        assert_eq!(file["contentSize"], "0");
    }

    #[test]
    fn escapes_awkward_names() {
        let doc = metadata_json(&sample("a\"b\\c.csv", Some("text/csv"), 1));
        let file = entity(&graph(&doc), "a\"b\\c.csv");
        assert_eq!(file["@type"], "File");
    }

    #[test]
    fn date_published_is_an_iso_datetime() {
        let doc = metadata_json(&sample("out.csv", None, 0));
        let date = entity(&graph(&doc), "./")["datePublished"]
            .as_str()
            .unwrap()
            .to_owned();
        assert_eq!(date, "2026-09-27T12:00:01+00:00");
    }
}
