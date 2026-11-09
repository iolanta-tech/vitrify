//! HTTP client helpers shared by the SPARQL and context commands.

use std::io::Read;
use std::time::Duration;

use oxhttp::Client;
use oxhttp::model::header::{
    ACCEPT, CACHE_CONTROL, CONTENT_ENCODING, CONTENT_TYPE, DATE, ETAG, EXPIRES, LAST_MODIFIED,
    LOCATION,
};
use oxhttp::model::{
    Body, HeaderMap, HeaderName, HeaderValue, Method, Request, Response, StatusCode,
};

use crate::error::{Error, Result};

const TIMEOUT: Duration = Duration::from_secs(120);
pub(crate) const MAX_REDIRECTS: usize = 5;

/// Headers copied into retrieval metadata, in this order, when the response has them.
const RECORDED_HEADERS: &[HeaderName] = &[
    CONTENT_TYPE,
    ETAG,
    LAST_MODIFIED,
    CACHE_CONTROL,
    EXPIRES,
    DATE,
];

fn user_agent() -> String {
    format!("vitrify/{}", env!("CARGO_PKG_VERSION"))
}

pub(crate) fn client() -> Result<Client> {
    Ok(Client::new()
        .with_global_timeout(TIMEOUT)
        .with_user_agent(user_agent())
        .map_err(|error| Error::new(format!("invalid User-Agent: {error}")))?
        .with_redirection_limit(0))
}

pub(crate) fn redirect_target(response: &Response<Body>, from: &str) -> Result<String> {
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

pub(crate) fn check_content_encoding(response: &Response<Body>) -> Result<()> {
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
pub(crate) fn response_media_type(response: &Response<Body>) -> Option<String> {
    media_type_from_headers(response.headers())
}

fn media_type_from_headers(headers: &HeaderMap) -> Option<String> {
    headers
        .get(CONTENT_TYPE)
        .and_then(|value| value.to_str().ok())
        .map(|value| value.split(';').next().unwrap_or("").trim().to_owned())
        .filter(|essence| !essence.is_empty())
}

/// A successful GET body, bounded by `max_bytes`, after redirects.
pub(crate) struct Downloaded {
    pub final_url: String,
    pub status: u16,
    pub media_type: Option<String>,
    pub headers: Vec<(String, String)>,
    pub body: Vec<u8>,
}

/// GET `url`, following redirects, and read the body into memory.
///
/// oxhttp consumes a GET redirect inside `Client::request` when the limit is 0
/// and returns an error that carries the next URL. That URL is the redirect
/// target this function follows.
pub(crate) fn download(url: &str, accept: &str, max_bytes: u64) -> Result<Downloaded> {
    let client = client()?;
    let accept =
        HeaderValue::try_from(accept).map_err(|_| Error::new("the Accept header is not valid"))?;
    let mut target = url.to_string();
    for hop in 0..=MAX_REDIRECTS {
        let request = Request::builder()
            .method(Method::GET)
            .uri(target.as_str())
            .header(ACCEPT, accept.clone())
            .body(Body::empty())
            .map_err(|error| {
                Error::new(format!("could not build the request to {target}: {error}"))
            })?;
        let response = match client.request(request) {
            Ok(response) => response,
            Err(error) => {
                if let Some(next) = redirect_target_from_client_error(&error) {
                    if hop == MAX_REDIRECTS {
                        return Err(Error::new(format!(
                            "context URL exceeded the redirect limit of {MAX_REDIRECTS}"
                        )));
                    }
                    target = next;
                    continue;
                }
                return Err(Error::new(format!("request to {target} failed: {error}")));
            }
        };
        let status = response.status();
        if status.is_redirection() {
            if is_followed_redirect(status) {
                if hop == MAX_REDIRECTS {
                    return Err(Error::new(format!(
                        "context URL exceeded the redirect limit of {MAX_REDIRECTS}"
                    )));
                }
                target = redirect_target(&response, &target)?;
                continue;
            }
            return Err(Error::new(format!(
                "context URL returned redirect {status}, which is not followed"
            )));
        }
        if !status.is_success() {
            return Err(Error::new(format!("context URL returned HTTP {status}")));
        }
        check_content_encoding(&response)?;
        let media_type = response_media_type(&response);
        let headers = recorded_headers(response.headers());
        let status_code = status.as_u16();
        let body = read_limited(response, max_bytes)?;
        return Ok(Downloaded {
            final_url: target,
            status: status_code,
            media_type,
            headers,
            body,
        });
    }
    Err(Error::new(format!(
        "context URL exceeded the redirect limit of {MAX_REDIRECTS}"
    )))
}

/// oxhttp's message when a GET redirect is not returned to the caller.
const CLIENT_REDIRECT_PREFIX: &str =
    "The server requested too many redirects (1). The latest redirection target is ";

fn redirect_target_from_client_error(error: &std::io::Error) -> Option<String> {
    let target = error
        .to_string()
        .strip_prefix(CLIENT_REDIRECT_PREFIX)?
        .to_owned();
    if target.starts_with("http://") || target.starts_with("https://") {
        Some(target)
    } else {
        None
    }
}

fn is_followed_redirect(status: StatusCode) -> bool {
    matches!(
        status,
        StatusCode::MOVED_PERMANENTLY
            | StatusCode::FOUND
            | StatusCode::SEE_OTHER
            | StatusCode::TEMPORARY_REDIRECT
            | StatusCode::PERMANENT_REDIRECT
    )
}

fn recorded_headers(headers: &HeaderMap) -> Vec<(String, String)> {
    RECORDED_HEADERS
        .iter()
        .filter_map(|name| {
            let value = headers.get(name)?.to_str().ok()?;
            Some((name.as_str().to_owned(), value.to_owned()))
        })
        .collect()
}

pub(crate) fn read_limited(response: Response<Body>, max_bytes: u64) -> Result<Vec<u8>> {
    let mut reader = response.into_body().take(max_bytes + 1);
    let mut body = Vec::new();
    let mut buffer = [0u8; 8192];
    loop {
        let read = reader
            .read(&mut buffer)
            .map_err(|error| Error::new(format!("could not read the response body: {error}")))?;
        if read == 0 {
            break;
        }
        if body.len() as u64 + read as u64 > max_bytes {
            return Err(Error::new(format!(
                "response body exceeds the {max_bytes}-byte limit"
            )));
        }
        body.extend_from_slice(&buffer[..read]);
    }
    Ok(body)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn response(status: u16, content_type: Option<&str>, body: &[u8]) -> Response<Body> {
        let mut builder = Response::builder().status(StatusCode::from_u16(status).unwrap());
        if let Some(value) = content_type {
            builder = builder.header(CONTENT_TYPE, value);
        }
        builder.body(Body::from(body.to_vec())).unwrap()
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

    #[test]
    fn read_limited_rejects_a_body_over_the_limit() {
        let within_limit = response(200, None, b"abcdef");
        assert_eq!(read_limited(within_limit, 6).unwrap(), b"abcdef");
        let over_limit = response(200, None, b"abcdef");
        assert!(read_limited(over_limit, 5).is_err());
    }

    #[test]
    fn recorded_headers_keep_the_raw_content_type_and_known_fields() {
        let response = Response::builder()
            .status(StatusCode::OK)
            .header(CONTENT_TYPE, "application/ld+json; charset=utf-8")
            .header(ETAG, "\"abc\"")
            .header("x-untracked", "no")
            .body(Body::from(Vec::new()))
            .unwrap();
        assert_eq!(
            recorded_headers(response.headers()),
            vec![
                (
                    "content-type".to_owned(),
                    "application/ld+json; charset=utf-8".to_owned()
                ),
                ("etag".to_owned(), "\"abc\"".to_owned()),
            ]
        );
    }
}
