//! RO-Crate 1.3 JSON-LD for one SPARQL retrieval.
//!
//! The crate is the package (`./`) plus the result and query files linked with
//! `hasPart`. Attached evidence records the endpoint, SHA-256 of both files,
//! and a `CreateAction` for the HTTP exchange.

use chrono::{DateTime, Utc};
use serde_json::json;

const CONTEXT: &str = "https://w3id.org/ro/crate/1.3/context";
const PROFILE: &str = "https://w3id.org/ro/crate/1.3";
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
    pub duration: f64,
}

/// Builds an RO-Crate 1.3 metadata document for one SPARQL result.
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
    let mut document = json!({
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
                "additionalProperty": [{"@id": "#retrieval-duration"}],
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
                "actionStatus": { "@id": "http://schema.org/CompletedActionStatus" },
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

    let graph = document["@graph"].as_array_mut().unwrap();
    graph.push(duration_property(retrieval.duration));
    serde_json::to_string_pretty(&document).expect("the document is serializable") + "\n"
}

fn duration_property(seconds: f64) -> serde_json::Value {
    json!({
        "@id": "#retrieval-duration", "@type": "PropertyValue", "propertyID": "retrieval-duration",
        "name": "Retrieval duration", "value": seconds, "unitCode": "SEC"
    })
}

/// A retrieval initialized before the request, or finalized after a failure.
pub struct Attempt<'a> {
    pub endpoint: &'a str,
    pub query: &'a str,
    pub accept: Option<&'a str>,
    pub started: DateTime<Utc>,
    pub ended: Option<DateTime<Utc>>,
    pub duration: Option<f64>,
    pub error: Option<&'a str>,
    pub response_status: Option<u16>,
    pub final_url: &'a str,
    pub partial: Option<(&'a str, Option<&'a str>)>,
}

/// Records an active or failed action without asserting a complete result.
pub fn attempt_json(attempt: &Attempt<'_>) -> String {
    use sha2::{Digest, Sha256};
    let mut root = json!({
        "@id": ROOT_ID, "@type": "Dataset", "name": "SPARQL retrieval",
        "description": "SPARQL retrieval recorded by Vitrify.",
        "datePublished": attempt.ended.unwrap_or(attempt.started).to_rfc3339(),
        "license": LICENSE_NOTICE,
        "publisher": {"@id": attempt.endpoint},
        "hasPart": [{"@id": QUERY_FILE_NAME}]
    });
    if attempt.duration.is_some() {
        root["additionalProperty"] = json!([{ "@id": "#retrieval-duration" }]);
    }
    let state = if attempt.error.is_some() {
        "FailedActionStatus"
    } else {
        "ActiveActionStatus"
    };
    let mut action = json!({
        "@id": "#retrieval", "@type": "CreateAction",
        "actionStatus": {"@id": format!("http://schema.org/{state}")},
        "startTime": attempt.started.to_rfc3339(),
        "instrument": {"@id": "https://vitrify.iolanta.tech"},
        "agent": {"@id": "https://vitrify.iolanta.tech"},
        "object": [{"@id": attempt.endpoint}, {"@id": QUERY_FILE_NAME}],
        "identifier": attempt.final_url,
    });
    let accept = attempt.accept.unwrap_or("omitted");
    action["description"] = json!(match attempt.response_status {
        Some(status) => format!("HTTP {status}; Accept: {accept}"),
        None => format!("Accept: {accept}"),
    });
    if let Some(ended) = attempt.ended {
        action["endTime"] = json!(ended.to_rfc3339());
    }
    let mut graph = vec![
        json!({"@id": DESCRIPTOR_ID, "@type": "CreativeWork", "conformsTo": {"@id": PROFILE}, "about": {"@id": ROOT_ID}}),
        json!({"@id": QUERY_FILE_NAME, "@type": "File", "encodingFormat": "application/sparql-query",
            "contentSize": attempt.query.len().to_string(), "sha256": format!("{:x}", Sha256::digest(attempt.query.as_bytes()))}),
        json!({"@id": attempt.endpoint, "@type": "Organization"}),
        json!({"@id": "https://vitrify.iolanta.tech", "@type": "SoftwareApplication", "name": "Vitrify",
            "url": "https://vitrify.iolanta.tech", "version": env!("CARGO_PKG_VERSION")}),
    ];
    if let Some(duration) = attempt.duration {
        graph.push(duration_property(duration));
    }
    if let Some(error) = attempt.error {
        action["error"] = json!({"@id": "#error"});
        graph.push(json!({"@id": "#error", "@type": "Thing", "description": error}));
    }
    if let Some((name, media_type)) = attempt.partial {
        root["hasPart"]
            .as_array_mut()
            .unwrap()
            .push(json!({"@id": name}));
        let mut partial = json!({"@id": name, "@type": "File", "description": "Incomplete response from a failed retrieval."});
        if let Some(media_type) = media_type {
            partial["encodingFormat"] = json!(media_type);
        }
        graph.push(partial);
    }
    graph.push(root);
    graph.push(action);
    serde_json::to_string_pretty(&json!({"@context": CONTEXT, "@graph": graph})).unwrap() + "\n"
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
            duration: 1.0,
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
        let document: Value = serde_json::from_str(&doc).unwrap();
        assert_eq!(
            document["@context"],
            "https://w3id.org/ro/crate/1.3/context"
        );
        let graph = graph(&doc);

        let descriptor = entity(&graph, "ro-crate-metadata.json");
        assert_eq!(descriptor["@type"], "CreativeWork");
        assert_eq!(descriptor["about"]["@id"], "./");
        assert_eq!(
            descriptor["conformsTo"]["@id"],
            "https://w3id.org/ro/crate/1.3"
        );

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
    fn attempts_use_ro_crate_1_3() {
        let retrieval = sample("results.csv", Some("text/csv"), 42);
        for (error, partial, status) in [
            (None, None, "ActiveActionStatus"),
            (Some("HTTP 503"), None, "FailedActionStatus"),
            (
                Some("Interrupted download"),
                Some(("results.csv", Some("text/csv"))),
                "FailedActionStatus",
            ),
        ] {
            let doc = attempt_json(&Attempt {
                endpoint: &retrieval.endpoint,
                query: "ASK {}",
                accept: None,
                started: retrieval.started,
                ended: error.map(|_| retrieval.ended),
                duration: error.map(|_| retrieval.duration),
                error,
                response_status: None,
                final_url: &retrieval.final_url,
                partial,
            });
            let document: Value = serde_json::from_str(&doc).unwrap();
            assert_eq!(
                document["@context"],
                "https://w3id.org/ro/crate/1.3/context"
            );
            let graph = graph(&doc);
            assert_eq!(
                entity(&graph, DESCRIPTOR_ID)["conformsTo"]["@id"],
                "https://w3id.org/ro/crate/1.3"
            );
            let action = entity(&graph, "#retrieval");
            assert_eq!(
                action["actionStatus"]["@id"],
                format!("http://schema.org/{status}")
            );
            assert!(action.get("result").is_none());
            if partial.is_some() {
                assert_eq!(entity(&graph, "results.csv")["@type"], "File");
            }
        }
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
