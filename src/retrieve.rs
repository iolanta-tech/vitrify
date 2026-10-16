//! One SPARQL retrieval: POST the query, then write the result and its crate.

use std::fs::File;
use std::io::{Read, Write};
use std::path::Path;
use std::time::{Duration, Instant};

use chrono::Utc;
use oxhttp::Client;
use oxhttp::model::header::{ACCEPT, CONTENT_ENCODING, CONTENT_TYPE, HeaderValue, LOCATION};
use oxhttp::model::{Body, Method, Request, Response, StatusCode};
use sha2::{Digest, Sha256};

use crate::error::{Error, Result};
use crate::rocrate::{self, METADATA_FILE_NAME, QUERY_FILE_NAME, Retrieval};
use crate::sparql::{self, Format};

const TIMEOUT: Duration = Duration::from_secs(120);
const MAX_REDIRECTS: usize = 5;
const MAX_BYTES: u64 = 1 << 30; // 1 GiB
const QUERY_CONTENT_TYPE: &str = "application/sparql-query";

fn user_agent() -> String {
    format!("vitrify/{}", env!("CARGO_PKG_VERSION"))
}

/// The plan and timing of the HTTP exchange, known before the body is stored.
struct Exchange {
    endpoint: String,
    query: String,
    format: Option<&'static Format>,
    started: chrono::DateTime<Utc>,
    final_url: String,
}

/// Executes one retrieval, recording its outcome even when the request fails.
pub fn fetch_to_file(
    endpoint: &str,
    query: &str,
    format: Option<&'static Format>,
    output_dir: &Path,
) -> Result<()> {
    let client = Client::new()
        .with_global_timeout(TIMEOUT)
        .with_user_agent(user_agent())
        .map_err(|e| Error::new(format!("invalid User-Agent: {e}")))?
        .with_redirection_limit(0);
    let mut exchange = Exchange {
        endpoint: endpoint.to_owned(),
        query: query.to_owned(),
        format,
        started: Utc::now(),
        final_url: endpoint.to_owned(),
    };
    record_attempt(output_dir, &mut exchange, |exchange| {
        let (response, final_url) = perform(&client, endpoint, query, format.map(|f| f.accept))?;
        exchange.final_url = final_url;
        Ok(response)
    })
}

fn record_attempt(
    output_dir: &Path,
    exchange: &mut Exchange,
    request: impl FnOnce(&mut Exchange) -> Result<Response<Body>>,
) -> Result<()> {
    let (query_byte_size, query_sha256) = write_query_snapshot(output_dir, &exchange.query)?;
    let metadata_path = output_dir.join(METADATA_FILE_NAME);
    let initial = rocrate::attempt_json(&rocrate::Attempt {
        endpoint: &exchange.endpoint,
        query: &exchange.query,
        accept: exchange.format.map(|f| f.accept),
        started: exchange.started,
        ended: None,
        duration: None,
        error: None,
        response_status: None,
        final_url: &exchange.final_url,
        partial: None,
    });
    write_metadata(&metadata_path, &initial)?;
    let clock = Instant::now();
    let mut response_status = None;
    let mut media_type = None;
    let mut result_name = None;
    let outcome = (|| {
        let response = request(exchange)?;
        let status = response.status();
        response_status = Some(status.as_u16());
        if !status.is_success() {
            return Err(Error::new(format!("endpoint returned HTTP {status}")));
        }
        check_content_encoding(&response)?;
        media_type = response_media_type(&response);
        let extension = exchange.format.map(|f| f.extension)
            .or_else(|| sparql::extension_for_media_type(media_type.as_deref()))
            .unwrap_or_else(|| {
                eprintln!("warning: no extension is known for the response Content-Type; writing results.dat");
                "dat"
            });
        let name = format!("results.{extension}");
        let result_path = output_dir.join(&name);
        result_name = Some(name.clone());
        let (byte_size, sha256) = stream_body(response, &result_path)?;
        let ended = Utc::now();
        let duration = clock.elapsed().as_secs_f64();
        let row_count = File::open(&result_path)
            .ok()
            .and_then(|file| crate::row_count::count(file).ok());
        let document = rocrate::metadata_json(&Retrieval {
            result_name: name,
            media_type: media_type.clone(),
            byte_size,
            sha256,
            query_byte_size,
            query_sha256,
            endpoint: exchange.endpoint.clone(),
            accept: exchange.format.map(|f| f.accept.to_owned()),
            status: status.as_u16(),
            final_url: exchange.final_url.clone(),
            started: exchange.started,
            ended,
            duration,
            row_count,
        });
        Ok((document, result_path))
    })();
    match outcome {
        Ok((document, result_path)) => {
            write_metadata(&metadata_path, &document)?;
            eprintln!("wrote: {}", result_path.display());
            eprintln!("metadata: {}", metadata_path.display());
            Ok(())
        }
        Err(error) => {
            let ended = Utc::now();
            let duration = clock.elapsed().as_secs_f64();
            let message = error.to_string();
            let partial = result_name
                .as_deref()
                .filter(|name| output_dir.join(name).is_file());
            let document = rocrate::attempt_json(&rocrate::Attempt {
                endpoint: &exchange.endpoint,
                query: &exchange.query,
                accept: exchange.format.map(|f| f.accept),
                started: exchange.started,
                ended: Some(ended),
                duration: Some(duration),
                error: Some(&message),
                response_status,
                final_url: &exchange.final_url,
                partial: partial.map(|name| (name, media_type.as_deref())),
            });
            write_metadata(&metadata_path, &document).map_err(|write_error| {
                Error::new(format!(
                    "{error}; could not persist retrieval metadata: {write_error}"
                ))
            })?;
            Err(error)
        }
    }
}

#[cfg(test)]
fn write_crate(response: Response<Body>, output_dir: &Path, exchange: &Exchange) -> Result<()> {
    let mut exchange = Exchange {
        endpoint: exchange.endpoint.clone(),
        query: exchange.query.clone(),
        format: exchange.format,
        started: exchange.started,
        final_url: exchange.final_url.clone(),
    };
    record_attempt(output_dir, &mut exchange, |_| Ok(response))
}

fn perform(
    client: &Client,
    endpoint: &str,
    query: &str,
    accept: Option<&'static str>,
) -> Result<(Response<Body>, String)> {
    let mut target = endpoint.to_string();
    for _ in 0..=MAX_REDIRECTS {
        let mut builder = Request::builder().method(Method::POST).uri(target.as_str());
        if let Some(accept) = accept {
            builder = builder.header(ACCEPT, HeaderValue::from_static(accept));
        }
        let request = builder
            .header(CONTENT_TYPE, HeaderValue::from_static(QUERY_CONTENT_TYPE))
            .body(Body::from(query.as_bytes().to_vec()))
            .map_err(|e| Error::new(format!("could not build the request to {target}: {e}")))?;

        let response = client
            .request(request)
            .map_err(|e| Error::new(format!("request to {target} failed: {e}")))?;

        let status = response.status();
        if status.is_redirection() {
            match status {
                StatusCode::TEMPORARY_REDIRECT | StatusCode::PERMANENT_REDIRECT => {
                    target = redirect_target(&response, &target)?;
                    continue;
                }
                other => {
                    return Err(Error::new(format!(
                        "endpoint returned redirect {other}, which is not followed for a POST query"
                    )));
                }
            }
        }
        return Ok((response, target));
    }
    Err(Error::new(format!(
        "endpoint exceeded the redirect limit of {MAX_REDIRECTS}"
    )))
}

fn redirect_target(response: &Response<Body>, from: &str) -> Result<String> {
    let location = response
        .headers()
        .get(LOCATION)
        .ok_or_else(|| Error::new("redirect response has no Location header"))?
        .to_str()
        .map_err(|_| Error::new("redirect Location header is not valid text"))?;
    if location.starts_with("http://") || location.starts_with("https://") {
        Ok(location.to_string())
    } else {
        Err(Error::new(format!(
            "relative redirect from {from} to {location} is not supported"
        )))
    }
}

/// Replace metadata atomically so an interrupted write retains the previous state.
fn write_metadata(path: &Path, document: &str) -> Result<()> {
    let temporary = path.with_extension("json.tmp");
    write_bytes(&temporary, document.as_bytes())?;
    std::fs::rename(&temporary, path)
        .map_err(|e| Error::new(format!("cannot replace {}: {e}", path.display())))
}

/// Stores the exact UTF-8 query sent to the endpoint in the crate.
fn write_query_snapshot(root: &Path, query: &str) -> Result<(u64, String)> {
    let path = root.join(QUERY_FILE_NAME);
    let bytes = query.as_bytes();
    write_bytes(&path, bytes)?;
    Ok((bytes.len() as u64, format!("{:x}", Sha256::digest(bytes))))
}

fn check_content_encoding(response: &Response<Body>) -> Result<()> {
    if let Some(value) = response.headers().get(CONTENT_ENCODING) {
        let coding = value
            .to_str()
            .map_err(|_| Error::new("Content-Encoding header is not valid text"))?
            .trim()
            .to_ascii_lowercase();
        if !matches!(coding.as_str(), "identity" | "gzip" | "deflate" | "") {
            return Err(Error::new(format!(
                "unsupported response Content-Encoding `{coding}`"
            )));
        }
    }
    Ok(())
}

/// The response media type (type and subtype, without parameters), if present.
fn response_media_type(response: &Response<Body>) -> Option<String> {
    response
        .headers()
        .get(CONTENT_TYPE)
        .and_then(|value| value.to_str().ok())
        .map(|value| value.split(';').next().unwrap_or("").trim().to_owned())
        .filter(|essence| !essence.is_empty())
}

fn write_bytes(path: &Path, bytes: &[u8]) -> Result<()> {
    let mut file = File::create(path)
        .map_err(|e| Error::new(format!("cannot create {}: {e}", path.display())))?;
    file.write_all(bytes)
        .map_err(|e| Error::new(format!("cannot write {}: {e}", path.display())))?;
    file.flush()
        .map_err(|e| Error::new(format!("cannot flush {}: {e}", path.display())))?;
    file.sync_all()
        .map_err(|e| Error::new(format!("cannot sync {}: {e}", path.display())))
}

fn stream_body(response: Response<Body>, path: &Path) -> Result<(u64, String)> {
    let mut file = File::create(path)
        .map_err(|e| Error::new(format!("cannot create {}: {e}", path.display())))?;
    let mut reader = response.into_body().take(MAX_BYTES + 1);
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 8192];
    let mut written = 0u64;
    loop {
        let n = reader
            .read(&mut buffer)
            .map_err(|e| Error::new(format!("could not read the response body: {e}")))?;
        if n == 0 {
            break;
        }
        hasher.update(&buffer[..n]);
        file.write_all(&buffer[..n])
            .map_err(|e| Error::new(format!("could not write the result: {e}")))?;
        written += n as u64;
        if written > MAX_BYTES {
            return Err(Error::new(format!(
                "response body exceeds the {MAX_BYTES}-byte limit"
            )));
        }
    }
    file.flush()
        .map_err(|e| Error::new(format!("could not flush the result: {e}")))?;
    file.sync_all()
        .map_err(|e| Error::new(format!("could not sync the result: {e}")))?;
    Ok((written, format!("{:x}", hasher.finalize())))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sparql::Format;
    use std::fs;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    use serde_json::Value;

    /// Builds an in-memory response; no socket is involved.
    fn response(status: u16, content_type: Option<&str>, body: &[u8]) -> Response<Body> {
        let mut builder = Response::builder().status(StatusCode::from_u16(status).unwrap());
        if let Some(value) = content_type {
            builder = builder.header(CONTENT_TYPE, value);
        }
        builder.body(Body::from(body.to_vec())).unwrap()
    }

    fn unique_dir() -> PathBuf {
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let dir = std::env::temp_dir().join(format!("vitrify-unit-{}-{nanos}", std::process::id()));
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    const CSV_FORMAT: Format = Format {
        accept: "text/csv",
        extension: "csv",
    };

    fn exchange() -> Exchange {
        Exchange {
            endpoint: "https://example.org/sparql".to_owned(),
            query: "SELECT ?s WHERE { ?s ?p ?o }".to_owned(),
            format: Some(&CSV_FORMAT),
            started: Utc::now(),
            final_url: "https://example.org/sparql".to_owned(),
        }
    }

    fn crate_entity(dir: &Path, id: &str) -> Value {
        let text = fs::read_to_string(dir.join(METADATA_FILE_NAME)).unwrap();
        let doc: Value = serde_json::from_str(&text).unwrap();
        doc["@graph"]
            .as_array()
            .unwrap()
            .iter()
            .find(|entity| entity["@id"] == id)
            .unwrap_or_else(|| panic!("entity {id} present"))
            .clone()
    }

    fn result_entity(dir: &Path, name: &str) -> Value {
        crate_entity(dir, name)
    }

    #[test]
    fn writes_result_and_records_media_type() {
        let dir = unique_dir();
        write_crate(
            response(200, Some("text/csv;charset=utf-8"), b"a,b\n"),
            &dir,
            &exchange(),
        )
        .unwrap();

        assert_eq!(fs::read(dir.join("results.csv")).unwrap(), b"a,b\n");
        let file = result_entity(&dir, "results.csv");
        assert_eq!(file["@type"], "File");
        assert_eq!(file["encodingFormat"], "text/csv");
        assert_eq!(file["contentSize"], "4");
    }

    #[test]
    fn records_even_an_unexpected_media_type() {
        let dir = unique_dir();
        write_crate(
            response(200, Some("text/html"), b"<html>"),
            &dir,
            &exchange(),
        )
        .unwrap();

        assert_eq!(fs::read(dir.join("results.csv")).unwrap(), b"<html>");
        assert_eq!(
            result_entity(&dir, "results.csv")["encodingFormat"],
            "text/html"
        );
    }

    #[test]
    fn writes_body_but_omits_media_type_when_absent() {
        let dir = unique_dir();
        let mut exchange = exchange();
        exchange.format = None;
        write_crate(response(200, None, b"x"), &dir, &exchange).unwrap();

        assert_eq!(fs::read(dir.join("results.dat")).unwrap(), b"x");
        assert!(
            result_entity(&dir, "results.dat")
                .get("encodingFormat")
                .is_none()
        );
    }

    #[test]
    fn records_sha256_matching_the_file_on_disk() {
        let dir = unique_dir();
        let body = b"a,b\n";
        write_crate(response(200, Some("text/csv"), body), &dir, &exchange()).unwrap();

        let expected = format!("{:x}", Sha256::digest(body));
        assert_eq!(result_entity(&dir, "results.csv")["sha256"], expected);
        assert_eq!(
            format!(
                "{:x}",
                Sha256::digest(fs::read(dir.join("results.csv")).unwrap())
            ),
            expected
        );
    }

    #[test]
    fn records_query_endpoint_accept_and_status() {
        let dir = unique_dir();
        let mut exchange = exchange();
        exchange.query = "SELECT ?person WHERE { ?person wdt:P31 wd:Q5 }".to_owned();
        exchange.format = Some(&CSV_FORMAT);
        write_crate(response(200, Some("text/csv"), b"x"), &dir, &exchange).unwrap();

        let query = crate_entity(&dir, QUERY_FILE_NAME);
        assert_eq!(
            fs::read_to_string(dir.join(QUERY_FILE_NAME)).unwrap(),
            "SELECT ?person WHERE { ?person wdt:P31 wd:Q5 }"
        );
        assert_eq!(query["@type"], "File");
        assert_eq!(query["encodingFormat"], "application/sparql-query");
        assert_eq!(
            crate_entity(&dir, "./")["publisher"]["@id"],
            "https://example.org/sparql"
        );
        let action = crate_entity(&dir, "#retrieval");
        assert_eq!(action["description"], "HTTP 200; Accept: text/csv");
        assert_eq!(action["identifier"], "https://example.org/sparql");
    }

    #[test]
    fn non_success_status_records_failure_without_overwriting_existing_result() {
        let dir = unique_dir();
        let to = dir.join("results.csv");
        fs::write(&to, b"OLD").unwrap();

        assert!(write_crate(response(500, Some("text/csv"), b"boom"), &dir, &exchange(),).is_err());
        assert_eq!(fs::read(&to).unwrap(), b"OLD");
        let action = crate_entity(&dir, "#retrieval");
        assert_eq!(
            action["actionStatus"]["@id"],
            "http://schema.org/FailedActionStatus"
        );
        assert!(action.get("result").is_none());
        assert_eq!(
            crate_entity(&dir, "#error")["description"],
            "endpoint returned HTTP 500 Internal Server Error"
        );
    }

    #[test]
    fn interrupted_body_is_preserved_as_incomplete() {
        struct Interrupted(bool);
        impl Read for Interrupted {
            fn read(&mut self, buffer: &mut [u8]) -> std::io::Result<usize> {
                if self.0 {
                    Err(std::io::Error::new(
                        std::io::ErrorKind::TimedOut,
                        "download timed out",
                    ))
                } else {
                    self.0 = true;
                    buffer[..4].copy_from_slice(b"s\npa");
                    Ok(4)
                }
            }
        }
        let dir = unique_dir();
        let response = Response::builder()
            .status(StatusCode::OK)
            .header(CONTENT_TYPE, "text/csv")
            .body(Body::from_read(Interrupted(false)))
            .unwrap();
        assert!(write_crate(response, &dir, &exchange()).is_err());
        assert_eq!(fs::read(dir.join("results.csv")).unwrap(), b"s\npa");
        let action = crate_entity(&dir, "#retrieval");
        assert_eq!(
            action["actionStatus"]["@id"],
            "http://schema.org/FailedActionStatus"
        );
        assert!(action.get("result").is_none());
        assert_eq!(
            crate_entity(&dir, "results.csv")["description"],
            "Incomplete response from a failed retrieval."
        );
    }

    #[test]
    fn count_measures_the_response_stream_independently_of_media_type() {
        let dir = unique_dir();
        let mut exchange = exchange();
        static TURTLE_FORMAT: Format = Format {
            accept: "text/turtle",
            extension: "ttl",
        };
        exchange.format = Some(&TURTLE_FORMAT);
        write_crate(
            response(
                200,
                Some("application/sparql-results+json"),
                br#"{"head":{"vars":["s"]},"results":{"bindings":[{}]}}"#,
            ),
            &dir,
            &exchange,
        )
        .unwrap();
        assert_eq!(crate_entity(&dir, "#row-count")["value"], 1);
        write_crate(
            response(200, Some("application/sparql-results+json"), b"invalid"),
            &dir,
            &exchange,
        )
        .unwrap();
        assert_eq!(crate_entity(&dir, "#row-count")["value"], 1);
        assert_eq!(
            crate_entity(&dir, "#retrieval")["actionStatus"]["@id"],
            "http://schema.org/CompletedActionStatus"
        );
    }

    #[test]
    fn unsupported_content_encoding_is_rejected() {
        let with_encoding = |coding: &str| {
            Response::builder()
                .status(StatusCode::OK)
                .header(CONTENT_TYPE, "text/csv")
                .header(CONTENT_ENCODING, coding)
                .body(Body::from(Vec::new()))
                .unwrap()
        };
        assert!(check_content_encoding(&with_encoding("br")).is_err());
        assert!(check_content_encoding(&with_encoding("gzip")).is_ok());
        assert!(check_content_encoding(&with_encoding("identity")).is_ok());
    }

    #[test]
    fn response_media_type_drops_parameters() {
        assert_eq!(
            response_media_type(&response(200, Some("Text/CSV; charset=utf-8"), b"")).as_deref(),
            Some("Text/CSV")
        );
        assert_eq!(response_media_type(&response(200, None, b"")), None);
    }

    #[test]
    fn redirect_target_requires_an_absolute_location() {
        let redirect = |location: Option<&str>| {
            let mut builder = Response::builder().status(StatusCode::TEMPORARY_REDIRECT);
            if let Some(value) = location {
                builder = builder.header(LOCATION, value);
            }
            builder.body(Body::from(Vec::new())).unwrap()
        };
        assert_eq!(
            redirect_target(&redirect(Some("https://example.org/x")), "https://a").unwrap(),
            "https://example.org/x"
        );
        assert!(redirect_target(&redirect(Some("/relative")), "https://a").is_err());
        assert!(redirect_target(&redirect(None), "https://a").is_err());
    }
}
