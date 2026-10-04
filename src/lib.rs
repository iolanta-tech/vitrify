//! Vitrify turns one SPARQL retrieval into a durable local file.
//!
//! Executes one query against an endpoint and saves the response body in an
//! output directory alongside its RO-Crate.

mod error;
mod retrieve;
mod rocrate;
mod sparql;

use std::fs;
use std::path::Path;

pub use error::{Error, Result};

/// Runs one `vitrify sparql` retrieval.
///
/// `query_arg` is the `--query` value: `-` for standard input, otherwise a file
/// path. `endpoint` is the SPARQL endpoint IRI, `format` is an optional format
/// name, and `to` is the output directory.
pub fn sparql(endpoint: &str, query_arg: &str, format: Option<&str>, to: &Path) -> Result<()> {
    let requested_format = sparql::requested_format(format)?;
    let query = sparql::load_query(query_arg)?;
    fs::create_dir_all(to).map_err(|error| {
        Error::new(format!(
            "cannot create output directory {}: {error}",
            to.display()
        ))
    })?;
    eprintln!("endpoint: {endpoint}");
    retrieve::fetch_to_file(endpoint, &query, requested_format, to)
}
