use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(
    name = "vitrify",
    version,
    about = "Turn a SPARQL retrieval into a durable local file"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Execute a SPARQL query and write the response to a file.
    Sparql(SparqlArgs),
}

#[derive(clap::Args)]
struct SparqlArgs {
    /// SPARQL endpoint IRI.
    #[arg(long)]
    endpoint: String,
    /// Query file path, or `-` to read the query from standard input.
    #[arg(long)]
    query: String,
    /// Output directory for the result and its RO-Crate.
    #[arg(long)]
    to: PathBuf,
    /// Requested result format; omitted to use the endpoint's choice.
    #[arg(long)]
    format: Option<String>,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let result = match &cli.command {
        Command::Sparql(args) => vitrify::sparql(
            &args.endpoint,
            &args.query,
            args.format.as_deref(),
            &args.to,
        ),
    };
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("error: {error}");
            ExitCode::FAILURE
        }
    }
}
