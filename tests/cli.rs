//! End-to-end integration tests for the `vitrify` binary.
//!
//! These run the compiled CLI against a local loopback HTTP server, so they
//! necessarily open a port: their whole purpose is to prove that the real HTTP
//! client puts the query on the wire (verbatim body, `Content-Type`, and the
//! optional `Accept` selected by `--format`) and writes the returned body.
//!
//! The pure decision logic — extension-to-media-type, query loading, the
//! status/`Content-Type`/`Content-Encoding` checks, and leaving an existing
//! result output unchanged on failure — is covered by socket-free unit tests in
//! `src/sparql.rs`, `src/retrieve.rs`, and `src/context.rs`. The context
//! command's HTTP behavior is covered at the bottom of this file.

use std::fs;
use std::io::Read;
use std::net::{Ipv4Addr, SocketAddr, TcpListener};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use assert_cmd::Command;
use oxhttp::Server;
use oxhttp::model::header::{ACCEPT, CONTENT_TYPE, ETAG, LOCATION};
use oxhttp::model::{Body, Request, Response, StatusCode};
use serde_json::Value;
use sha2::{Digest, Sha256};

/// The request as the loopback server saw it.
#[derive(Default)]
struct Captured {
    accept: Option<String>,
    content_type: Option<String>,
    body: String,
}

struct Fixture {
    base_url: String,
    captured: Arc<Mutex<Captured>>,
    _server: oxhttp::ListeningServer,
}

static PORT_SELECTION: Mutex<()> = Mutex::new(());

fn lock_ports() -> std::sync::MutexGuard<'static, ()> {
    PORT_SELECTION
        .lock()
        .unwrap_or_else(|error| error.into_inner())
}

fn free_port() -> u16 {
    TcpListener::bind((Ipv4Addr::LOCALHOST, 0))
        .unwrap()
        .local_addr()
        .unwrap()
        .port()
}

/// Starts a loopback server that records the request and replies `200` with
/// `content_type` and `body`.
fn spawn(reply_content_type: &'static str, reply_body: &'static [u8]) -> Fixture {
    let _selection = lock_ports();
    for _ in 0..32 {
        let port = free_port();
        let captured = Arc::new(Mutex::new(Captured::default()));
        let handler_captured = Arc::clone(&captured);
        let server = Server::new(move |request: &mut Request<Body>| {
            let header = |name: &oxhttp::model::header::HeaderName| {
                request
                    .headers()
                    .get(name)
                    .and_then(|v| v.to_str().ok())
                    .map(str::to_owned)
            };
            let accept = header(&ACCEPT);
            let request_content_type = header(&CONTENT_TYPE);
            let mut request_body = String::new();
            let _ = request.body_mut().read_to_string(&mut request_body);
            {
                let mut guard = handler_captured.lock().unwrap();
                guard.accept = accept;
                guard.content_type = request_content_type;
                guard.body = request_body;
            }
            Response::builder()
                .status(StatusCode::OK)
                .header(CONTENT_TYPE, reply_content_type)
                .body(Body::from(reply_body.to_vec()))
                .unwrap()
        })
        .bind(SocketAddr::from((Ipv4Addr::LOCALHOST, port)));
        match server.spawn() {
            Ok(listening) => {
                return Fixture {
                    base_url: format!("http://{}:{port}/sparql", Ipv4Addr::LOCALHOST),
                    captured,
                    _server: listening,
                };
            }
            Err(error) if error.kind() == std::io::ErrorKind::AddrInUse => continue,
            Err(error) => panic!("failed to bind the test server: {error}"),
        }
    }
    panic!("no free localhost port");
}

fn temp_dir() -> PathBuf {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!("vitrify-cli-{}-{nanos}", std::process::id()));
    fs::create_dir_all(&dir).unwrap();
    dir
}

const SELECT: &str = "SELECT ?s WHERE { ?s ?p ?o } LIMIT 1";

#[test]
fn response_content_type_names_the_file_while_format_sets_accept() {
    let body = b"s\nhttp://example.org/a\n";
    let fixture = spawn("Text/CSV; charset=utf-8", body);
    let dir = temp_dir();
    Command::cargo_bin("vitrify")
        .unwrap()
        .args(["sparql", "--endpoint", &fixture.base_url, "--query", "-"])
        .args(["--format", "turtle", "--to"])
        .arg(&dir)
        .write_stdin(SELECT)
        .assert()
        .success();

    assert_eq!(
        fixture.captured.lock().unwrap().accept.as_deref(),
        Some("text/turtle")
    );
    assert_eq!(fs::read(dir.join("results.csv")).unwrap(), body);
    assert!(!dir.join("results.ttl").exists());
    let document: Value =
        serde_json::from_slice(&fs::read(dir.join("ro-crate-metadata.json")).unwrap()).unwrap();
    let action = document["@graph"]
        .as_array()
        .unwrap()
        .iter()
        .find(|entity| entity["@id"] == "#retrieval")
        .unwrap();
    assert_eq!(action["result"]["@id"], "results.csv");
}

#[test]
fn posts_query_from_file_verbatim_and_writes_the_body() {
    let fixture = spawn("text/csv;charset=utf-8", b"s\nhttp://example.org/a\n");
    let dir = temp_dir();
    let query = dir.join("query.rq");
    fs::write(&query, SELECT).unwrap();
    Command::cargo_bin("vitrify")
        .unwrap()
        .args(["sparql", "--endpoint", &fixture.base_url, "--query"])
        .arg(&query)
        .args(["--format", "csv"])
        .arg("--to")
        .arg(&dir)
        .assert()
        .success();

    let out = dir.join("results.csv");
    assert_eq!(fs::read(&out).unwrap(), b"s\nhttp://example.org/a\n");
    let captured = fixture.captured.lock().unwrap();
    assert_eq!(captured.accept.as_deref(), Some("text/csv"));
    assert_eq!(
        captured.content_type.as_deref(),
        Some("application/sparql-query")
    );
    assert_eq!(captured.body, SELECT);
    drop(captured);

    let crate_json: Value =
        serde_json::from_str(&fs::read_to_string(dir.join("ro-crate-metadata.json")).unwrap())
            .unwrap();
    let graph = crate_json["@graph"].as_array().unwrap();
    let entity = |id: &str| {
        graph
            .iter()
            .find(|e| e["@id"] == id)
            .unwrap_or_else(|| panic!("entity {id}"))
    };
    let body = fs::read(&out).unwrap();
    assert_eq!(
        entity("results.csv")["sha256"],
        hex::encode(Sha256::digest(&body))
    );
    assert_eq!(fs::read(dir.join("query.rq")).unwrap(), SELECT.as_bytes());
    assert_eq!(entity("query.rq")["@type"], "File");
}

#[test]
fn reads_the_query_from_stdin_when_query_is_dash() {
    let fixture = spawn("text/csv", b"s\n");
    let dir = temp_dir();
    Command::cargo_bin("vitrify")
        .unwrap()
        .args(["sparql", "--endpoint", &fixture.base_url, "--query", "-"])
        .arg("--to")
        .arg(&dir)
        .write_stdin(SELECT)
        .assert()
        .success();

    let captured = fixture.captured.lock().unwrap();
    assert_eq!(captured.body, SELECT);
    assert_eq!(captured.accept, None);
}

#[test]
fn connection_failure_is_a_saved_failed_attempt() {
    let _selection = lock_ports();
    let port = free_port();
    let dir = temp_dir();
    Command::cargo_bin("vitrify")
        .unwrap()
        .args([
            "sparql",
            "--endpoint",
            &format!("http://127.0.0.1:{port}/sparql"),
            "--query",
            "-",
        ])
        .arg("--to")
        .arg(&dir)
        .write_stdin(SELECT)
        .assert()
        .failure();
    let document: Value =
        serde_json::from_str(&fs::read_to_string(dir.join("ro-crate-metadata.json")).unwrap())
            .unwrap();
    let graph = document["@graph"].as_array().unwrap();
    let action = graph
        .iter()
        .find(|entity| entity["@id"] == "#retrieval")
        .unwrap();
    assert_eq!(
        action["actionStatus"]["@id"],
        "http://schema.org/FailedActionStatus"
    );
    assert!(action.get("result").is_none());
    assert!(action["endTime"].is_string());
    assert!(graph.iter().any(|entity| entity["@id"] == "#error"));
    assert_eq!(fs::read_to_string(dir.join("query.rq")).unwrap(), SELECT);
    assert!(!dir.join("results.csv").exists());
}

#[test]
fn invalid_endpoint_does_not_initialize_an_attempt() {
    let dir = temp_dir().join("output");
    Command::cargo_bin("vitrify")
        .unwrap()
        .args(["sparql", "--endpoint", "relative/path", "--query", "-"])
        .arg("--to")
        .arg(&dir)
        .write_stdin(SELECT)
        .assert()
        .failure();
    assert!(!dir.exists());
}

struct SeenRequest {
    method: String,
    accept: Option<String>,
    path: String,
}

struct Running {
    base_url: String,
    seen: Arc<Mutex<Vec<SeenRequest>>>,
    _server: oxhttp::ListeningServer,
}

fn start<F>(respond: F) -> Running
where
    F: Fn(&str, &str) -> Response<Body> + Send + Sync + 'static,
{
    let respond = Arc::new(respond);
    let _selection = lock_ports();
    for _ in 0..32 {
        let port = free_port();
        let base_url = format!("http://{}:{port}", Ipv4Addr::LOCALHOST);
        let seen = Arc::new(Mutex::new(Vec::new()));
        let seen_handler = Arc::clone(&seen);
        let respond = Arc::clone(&respond);
        let base_for_handler = base_url.clone();
        let server = Server::new(move |request: &mut Request<Body>| {
            let path = request.uri().path().to_owned();
            let accept = request
                .headers()
                .get(ACCEPT)
                .and_then(|value| value.to_str().ok())
                .map(str::to_owned);
            seen_handler.lock().unwrap().push(SeenRequest {
                method: request.method().to_string(),
                accept,
                path: path.clone(),
            });
            respond(&path, &base_for_handler)
        })
        .bind(SocketAddr::from((Ipv4Addr::LOCALHOST, port)));
        match server.spawn() {
            Ok(listening) => {
                return Running {
                    base_url,
                    seen,
                    _server: listening,
                };
            }
            Err(error) if error.kind() == std::io::ErrorKind::AddrInUse => continue,
            Err(error) => panic!("failed to bind the test server: {error}"),
        }
    }
    panic!("no free localhost port");
}

const CONTEXT_BODY: &[u8] =
    br#"{"@context":{"@vocab":"http://example.org/","z":"http://z.example/","a":"http://a.example/"}}"#;

const CONTEXT_ACCEPT: &str = concat!(
    "application/ld+json;profile=\"http://www.w3.org/ns/json-ld#context\", ",
    "application/ld+json;q=0.9, ",
    "application/ld+yaml;q=0.8, ",
    "application/json;q=0.5, ",
    "application/yaml;q=0.4"
);

fn context_ok() -> Response<Body> {
    Response::builder()
        .status(StatusCode::OK)
        .header(CONTENT_TYPE, "application/ld+json; charset=utf-8")
        .header(ETAG, "\"v1\"")
        .body(Body::from(CONTEXT_BODY.to_vec()))
        .unwrap()
}

fn assert_failed_without_stdout(args: &[&str]) {
    let output = Command::cargo_bin("vitrify")
        .unwrap()
        .args(args)
        .output()
        .unwrap();
    assert!(
        !output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(
        output.stdout.is_empty(),
        "stdout: {}",
        String::from_utf8_lossy(&output.stdout)
    );
}

#[test]
fn context_prints_jsonld_with_the_request_accept_and_digest() {
    let running = start(|_, _| context_ok());
    let url = format!("{}/context.jsonld", running.base_url);
    let output = Command::cargo_bin("vitrify")
        .unwrap()
        .args(["context", &url])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let seen = running.seen.lock().unwrap();
    assert_eq!(seen.len(), 1);
    assert_eq!(seen[0].method, "GET");
    assert_eq!(seen[0].accept.as_deref(), Some(CONTEXT_ACCEPT));
    assert_eq!(seen[0].path, "/context.jsonld");
    drop(seen);

    let document: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(document["@context"]["@vocab"], "http://example.org/");
    assert_eq!(document["@context"]["z"], "http://z.example/");
    assert_eq!(document["@id"], url);
    assert_eq!(
        document["http://schema.org/sha256"]["@value"],
        hex::encode(Sha256::digest(CONTEXT_BODY))
    );
    assert_eq!(
        document["http://schema.org/contentSize"]["@value"],
        CONTEXT_BODY.len().to_string()
    );
    assert_eq!(
        document["http://schema.org/encodingFormat"]["@value"],
        "application/ld+json"
    );
    assert!(document.get("@included").is_none());
    let action = &document["@reverse"]["http://schema.org/result"];
    assert_eq!(action["@type"], "http://schema.org/CreateAction");
    let response = &action["http://schema.org/object"]["http://www.w3.org/2011/http#resp"];
    assert_eq!(
        response["http://www.w3.org/2011/http#statusCodeValue"]["@value"],
        200
    );
    let headers = response["http://www.w3.org/2011/http#headers"]
        .as_array()
        .unwrap();
    assert!(headers.iter().any(|header| {
        header["http://www.w3.org/2011/http#fieldName"]["@value"] == "etag"
            && header["http://www.w3.org/2011/http#fieldValue"]["@value"] == "\"v1\""
    }));
}

#[test]
fn context_can_print_yamlld() {
    let running = start(|_, _| context_ok());
    let url = format!("{}/context.jsonld", running.base_url);
    let output = Command::cargo_bin("vitrify")
        .unwrap()
        .args(["context", &url, "--as", "yamlld"])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8(output.stdout).unwrap();
    assert!(!stdout.trim_start().starts_with('{'));
    assert!(stdout.contains("http://example.org/"));
    assert!(stdout.contains(&hex::encode(Sha256::digest(CONTEXT_BODY))));
}

#[test]
fn context_follows_a_redirect_and_records_both_urls() {
    let running = start(|path, base| {
        if path == "/start.jsonld" {
            Response::builder()
                .status(StatusCode::FOUND)
                .header(LOCATION, format!("{base}/final.jsonld"))
                .body(Body::empty())
                .unwrap()
        } else {
            context_ok()
        }
    });
    let requested = format!("{}/start.jsonld", running.base_url);
    let output = Command::cargo_bin("vitrify")
        .unwrap()
        .args(["context", &requested])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let seen = running.seen.lock().unwrap();
    assert_eq!(seen[0].path, "/start.jsonld");
    assert_eq!(seen[1].path, "/final.jsonld");
    drop(seen);
    let document: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(document["@id"], requested);
    assert_eq!(
        document["http://schema.org/contentUrl"]["@id"],
        format!("{}/final.jsonld", running.base_url)
    );
}

#[test]
fn context_warns_when_the_context_points_at_a_remote_document() {
    let running = start(|_, _| {
        Response::builder()
            .status(StatusCode::OK)
            .header(CONTENT_TYPE, "application/ld+json")
            .body(Body::from(
                br#"{"@context":"http://example.org/remote.jsonld"}"#.to_vec(),
            ))
            .unwrap()
    });
    let url = format!("{}/remote-ref.jsonld", running.base_url);
    let output = Command::cargo_bin("vitrify")
        .unwrap()
        .args(["context", &url])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(String::from_utf8_lossy(&output.stderr).contains("not vitrified"));
    let document: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(document["@context"], "http://example.org/remote.jsonld");
}

#[test]
fn context_failures_exit_nonzero_and_print_nothing() {
    let missing = start(|_, _| {
        Response::builder()
            .status(StatusCode::NOT_FOUND)
            .body(Body::from(b"missing".to_vec()))
            .unwrap()
    });
    assert_failed_without_stdout(&["context", &format!("{}/missing.jsonld", missing.base_url)]);

    let broken = start(|_, _| {
        Response::builder()
            .status(StatusCode::INTERNAL_SERVER_ERROR)
            .body(Body::from(b"boom".to_vec()))
            .unwrap()
    });
    assert_failed_without_stdout(&["context", &format!("{}/broken.jsonld", broken.base_url)]);

    let not_json = start(|_, _| {
        Response::builder()
            .status(StatusCode::OK)
            .header(CONTENT_TYPE, "application/ld+json")
            .body(Body::from(b"not-json".to_vec()))
            .unwrap()
    });
    assert_failed_without_stdout(&["context", &format!("{}/bad.jsonld", not_json.base_url)]);

    let _selection = lock_ports();
    let port = free_port();
    drop(_selection);
    assert_failed_without_stdout(&[
        "context",
        &format!("http://127.0.0.1:{port}/context.jsonld"),
    ]);
}
