//! Counts LF bytes plus one in a response stream.

use std::io::{self, Read};

/// Count text rows in bounded chunks, including an empty final row after an LF.
pub fn count(mut reader: impl Read) -> io::Result<u64> {
    let mut rows = 1;
    let mut buffer = [0; 8192];
    loop {
        let length = reader.read(&mut buffer)?;
        if length == 0 {
            return Ok(rows);
        }
        rows += buffer[..length]
            .iter()
            .filter(|&&byte| byte == b'\n')
            .count() as u64;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn counts_raw_lf_bytes_plus_one() {
        for (content, expected) in [
            ("", 1),
            ("one", 1),
            ("one\n", 2),
            ("one\ntwo", 2),
            ("one\r\ntwo\r\n", 3),
            ("one\rtwo", 1),
            ("name,value\n\"a\nb\",1\n", 4),
            ("{\"results\":{\"bindings\":[{},{}]}}", 1),
            ("\n\n", 3),
        ] {
            assert_eq!(count(content.as_bytes()).unwrap(), expected);
        }
    }

    #[test]
    fn counts_large_streams_without_a_size_cap() {
        let length = 20 * 1024 * 1024;
        assert_eq!(count(io::repeat(b'\n').take(length)).unwrap(), length + 1);
    }

    #[test]
    fn propagates_read_errors() {
        struct Unreadable;
        impl Read for Unreadable {
            fn read(&mut self, _: &mut [u8]) -> io::Result<usize> {
                Err(io::Error::other("unreadable"))
            }
        }
        assert!(count(Unreadable).is_err());
    }
}
