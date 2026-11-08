//! Parse and emit YAML 1.2 with [`saphyr`].

use saphyr::{LoadableYamlNode, Scalar, ScalarStyle, Yaml, YamlEmitter};
use serde_json::{Map, Number, Value};

use crate::error::{Error, Result};

pub fn from_slice(bytes: &[u8]) -> Result<Value> {
    let text = std::str::from_utf8(bytes).map_err(|_| Error::new("input is not UTF-8"))?;
    from_str(text)
}

pub fn from_str(text: &str) -> Result<Value> {
    let mut documents = Yaml::load_from_str(text).map_err(|error| Error::new(error.to_string()))?;
    if documents.len() != 1 {
        return Err(Error::new("expected one YAML document"));
    }
    json_from_yaml(documents.remove(0))
}

pub fn to_string(value: &Value) -> Result<String> {
    let yaml = yaml_from_json(value);
    let mut text = String::new();
    let mut emitter = YamlEmitter::new(&mut text);
    emitter
        .dump(&yaml)
        .map_err(|error| Error::new(error.to_string()))?;
    if !text.ends_with('\n') {
        text.push('\n');
    }
    Ok(text)
}

fn json_from_yaml(node: Yaml<'_>) -> Result<Value> {
    match node {
        Yaml::Value(Scalar::Null) => Ok(Value::Null),
        Yaml::Value(Scalar::Boolean(value)) => Ok(Value::Bool(value)),
        Yaml::Value(Scalar::Integer(value)) => Ok(Value::Number(value.into())),
        Yaml::Value(Scalar::FloatingPoint(value)) => Number::from_f64(value.into_inner())
            .map(Value::Number)
            .ok_or_else(|| Error::new("non-finite number")),
        Yaml::Value(Scalar::String(value)) => Ok(Value::String(value.into_owned())),
        Yaml::Sequence(items) => items
            .into_iter()
            .map(json_from_yaml)
            .collect::<Result<Vec<_>>>()
            .map(Value::Array),
        Yaml::Mapping(mapping) => {
            let mut object = Map::new();
            for (key, value) in mapping {
                object.insert(string_key(&key)?, json_from_yaml(value)?);
            }
            Ok(Value::Object(object))
        }
        Yaml::Tagged(_, node) => json_from_yaml(*node),
        Yaml::Representation(text, style, tag) => {
            let scalar = Scalar::parse_from_cow_and_metadata(text, style, tag.as_ref())
                .ok_or_else(|| Error::new("unsupported scalar"))?;
            json_from_yaml(Yaml::Value(scalar))
        }
        Yaml::Alias(_) => Err(Error::new("aliases are not supported")),
        Yaml::BadValue => Err(Error::new("invalid YAML value")),
    }
}

fn string_key(node: &Yaml<'_>) -> Result<String> {
    node.as_str()
        .map(str::to_owned)
        .ok_or_else(|| Error::new("mapping key is not a string"))
}

fn yaml_from_json(value: &Value) -> Yaml<'_> {
    match value {
        Value::Null => Yaml::Value(Scalar::Null),
        Value::Bool(value) => Yaml::Value(Scalar::Boolean(*value)),
        Value::Number(number) => yaml_from_number(number),
        Value::String(value) => Yaml::Value(Scalar::String(value.as_str().into())),
        Value::Array(items) => Yaml::Sequence(items.iter().map(yaml_from_json).collect()),
        Value::Object(mapping) => {
            let mut object = saphyr::Mapping::new();
            for (key, value) in mapping {
                object.insert(
                    Yaml::Value(Scalar::String(key.as_str().into())),
                    yaml_from_json(value),
                );
            }
            Yaml::Mapping(object)
        }
    }
}

fn yaml_from_number(number: &Number) -> Yaml<'_> {
    if let Some(integer) = number.as_i64() {
        return Yaml::Value(Scalar::Integer(integer));
    }
    Yaml::Representation(number.to_string().into(), ScalarStyle::Plain, None)
}
