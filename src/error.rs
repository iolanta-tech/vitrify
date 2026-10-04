use std::fmt;

/// An error that aborts a materialization.
///
/// It carries a human-readable message that the CLI prints to standard error.
#[derive(Debug)]
pub struct Error(String);

impl Error {
    pub fn new(message: impl Into<String>) -> Self {
        Self(message.into())
    }
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl std::error::Error for Error {}

/// Result specialized to [`Error`].
pub type Result<T> = std::result::Result<T, Error>;
