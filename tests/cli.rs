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
//! `src/sparql.rs` and `src/retrieve.rs`.

use std::fs;
use std::io::Read;
use std::net::{Ipv4Addr, SocketAddr, TcpListener};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use assert_cmd::Command;
use oxhttp::Server;
use oxhttp::model::header::{ACCEPT, CONTENT_TYPE};
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
    Fixture {
        base_url: format!("http://{}:{port}/sparql", Ipv4Addr::LOCALHOST),
        captured,
        _server: server.spawn().unwrap(),
    }
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
        format!("{:x}", Sha256::digest(&body))
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
