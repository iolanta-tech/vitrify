//! Query intake and SPARQL response-format negotiation.

use phf::phf_map;
use std::fs;
use std::io::{self, IsTerminal, Read};

use crate::error::{Error, Result};

/// An output format accepted by Vitrify.
#[derive(Clone, Copy)]
pub struct Format {
    pub accept: &'static str,
    pub extension: &'static str,
}

/// The request media type and result-file extension for each named format.
///
/// Result-set XML and RDF/XML have separate names because they are different
/// media types and apply to different SPARQL query forms.
static FORMATS: phf::Map<&'static str, Format> = phf_map! {
    "json" => Format { accept: "application/sparql-results+json", extension: "json" },
    "xml" => Format { accept: "application/sparql-results+xml", extension: "xml" },
    "csv" => Format { accept: "text/csv", extension: "csv" },
    "tsv" => Format { accept: "text/tab-separated-values", extension: "tsv" },
    "jsonld" => Format { accept: "application/ld+json", extension: "jsonld" },
    "turtle" => Format { accept: "text/turtle", extension: "ttl" },
    "ntriples" => Format { accept: "application/n-triples", extension: "nt" },
    "rdfxml" => Format { accept: "application/rdf+xml", extension: "rdf" },
};

/// Resolves a `--format` name. `None` leaves format selection to the endpoint.
pub fn requested_format(name: Option<&str>) -> Result<Option<&'static Format>> {
    let Some(name) = name else {
        return Ok(None);
    };
    FORMATS.get(name).map(Some).ok_or_else(|| {
        Error::new(format!(
            "unknown format `{name}`; supported formats: json, xml, csv, tsv, turtle, ntriples, rdfxml, jsonld"
        ))
    })
}

/// Maps a response Content-Type to a known file extension.
pub fn extension_for_media_type(media_type: Option<&str>) -> Option<&'static str> {
    let media_type = media_type?;
    FORMATS
        .values()
        .find(|format| format.accept.eq_ignore_ascii_case(media_type))
        .map(|format| format.extension)
}

/// Loads the query text named by `--query`.
///
/// `-` reads standard input; any other value is a file path. The result must be
/// non-empty UTF-8. Standard input is only touched when the argument is `-`.
pub fn load_query(query_arg: &str) -> Result<String> {
    let text = if query_arg == "-" {
        read_stdin()?
    } else {
        read_file(query_arg)?
    };
    if text.trim().is_empty() {
        return Err(Error::new("the query is empty"));
    }
    Ok(text)
}

fn read_stdin() -> Result<String> {
    let mut stdin = io::stdin();
    if stdin.is_terminal() {
        return Err(Error::new(
            "--query - was given but standard input is a terminal",
        ));
    }
    let mut text = String::new();
    stdin
        .read_to_string(&mut text)
        .map_err(|e| Error::new(format!("cannot read the query from standard input: {e}")))?;
    Ok(text)
}

fn read_file(path: &str) -> Result<String> {
    let bytes =
        fs::read(path).map_err(|e| Error::new(format!("cannot read query file {path}: {e}")))?;
    String::from_utf8(bytes)
        .map_err(|_| Error::new(format!("query file {path} is not valid UTF-8")))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn named_formats_map_to_request_media_types_and_extensions() {
        let csv = requested_format(Some("csv")).unwrap().unwrap();
        assert_eq!(csv.accept, "text/csv");
        assert_eq!(csv.extension, "csv");

        let turtle = requested_format(Some("turtle")).unwrap().unwrap();
        assert_eq!(turtle.accept, "text/turtle");
        assert_eq!(turtle.extension, "ttl");

        assert_eq!(
            extension_for_media_type(Some("application/sparql-results+json")),
            Some("json")
        );
    }

    #[test]
    fn omitted_format_is_allowed_and_unknown_format_is_rejected() {
        assert!(requested_format(None).unwrap().is_none());
        assert!(requested_format(Some("unknown")).is_err());
        assert_eq!(extension_for_media_type(None), None);
        assert_eq!(
            extension_for_media_type(Some("application/octet-stream")),
            None
        );
    }

    fn temp_query(contents: &[u8]) -> PathBuf {
        let nanos = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path =
            std::env::temp_dir().join(format!("vitrify-query-{}-{nanos}.rq", std::process::id()));
        fs::write(&path, contents).unwrap();
        path
    }

    #[test]
    fn load_query_reads_a_file_verbatim() {
        let path = temp_query(b"SELECT ?s WHERE { ?s ?p ?o }");
        let query = load_query(path.to_str().unwrap()).unwrap();
        assert_eq!(query, "SELECT ?s WHERE { ?s ?p ?o }");
    }

    #[test]
    fn load_query_rejects_an_empty_query() {
        let path = temp_query(b"   \n\t");
        assert!(load_query(path.to_str().unwrap()).is_err());
    }

    #[test]
    fn load_query_rejects_non_utf8() {
        let path = temp_query(&[0xff, 0xfe, 0x00]);
        assert!(load_query(path.to_str().unwrap()).is_err());
    }

    #[test]
    fn load_query_rejects_a_missing_file() {
        assert!(load_query("/no/such/vitrify/query.rq").is_err());
    }
}
