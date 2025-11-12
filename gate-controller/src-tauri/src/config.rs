use serde::{Deserialize, Serialize};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use tauri::{AppHandle, Manager};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub enum RelayType {
    #[serde(rename = "ch340")]
    CH340,
    #[serde(rename = "hw348")]
    HW348,
    #[serde(rename = "cp210x")]
    CP210x,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ConfiguredRelay {
    pub id: String,
    #[serde(rename = "type")]
    pub relay_type: RelayType,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub channels: Option<u8>,
}

#[derive(Serialize, Deserialize, Debug, Clone, Default)]
pub struct AppConfig {
    pub relays: Vec<ConfiguredRelay>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub webhook_token: Option<String>,
}

fn get_config_dir(app: &AppHandle) -> Result<PathBuf, String> {
    let config_dir = app.path().app_config_dir().map_err(|e| e.to_string())?;
    if !config_dir.exists() {
        fs::create_dir_all(&config_dir).map_err(|e| e.to_string())?;
    }
    Ok(config_dir)
}

fn get_config_path(app: &AppHandle) -> Result<PathBuf, String> {
    Ok(get_config_dir(app)?.join("config.json"))
}

fn get_log_path(app: &AppHandle) -> Result<PathBuf, String> {
    Ok(get_config_dir(app)?.join("webhook_logs.txt"))
}

pub fn append_to_log(app: &AppHandle, log_line: &str) -> Result<(), String> {
    let path = get_log_path(app)?;
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|e| e.to_string())?;

    writeln!(file, "{}", log_line).map_err(|e| e.to_string())
}

pub fn load_config(app: &AppHandle) -> Result<AppConfig, String> {
    let path = get_config_path(app)?;
    if !path.exists() {
        return Ok(AppConfig::default());
    }
    let content = fs::read_to_string(path).map_err(|e| e.to_string())?;
    if content.trim().is_empty() {
        return Ok(AppConfig::default());
    }
    serde_json::from_str(&content).map_err(|e| e.to_string())
}

pub fn save_config(app: &AppHandle, config: &AppConfig) -> Result<(), String> {
    let path = get_config_path(app)?;
    let content = serde_json::to_string_pretty(config).map_err(|e| e.to_string())?;
    fs::write(path, content).map_err(|e| e.to_string())
}