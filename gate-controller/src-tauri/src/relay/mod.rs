
// ==============================
// ========= MODULES ============
// ==============================
mod ch340;
mod hw348;
mod cp210x;

// ==============================
// ========== IMPORTS ===========
// ==============================
use crate::config::{self, ConfiguredRelay, RelayType};
use rand::{distributions::Alphanumeric, thread_rng, Rng};
use serialport::{self, SerialPort};
use std::{
    collections::HashMap,
    sync::{Arc, Mutex},
};
use tauri::{AppHandle, State};

// ==============================
// ====== CONNECTION STATE ======
// ==============================

// This state is for all serial-based connections (CH340, CP210x, etc.)
pub struct ConnectionManager(pub Arc<Mutex<HashMap<String, Box<dyn SerialPort + Send>>>>);

// ==============================
// ========= DATA TYPES =========
// ==============================

// Re-exporting for convenience in main.rs
pub use hw348::UsbRelayInfo;

#[derive(serde::Deserialize)]
pub struct RelayActionPayload {
    pub id: String,
    pub action: String, // "on" or "off"
    pub channel: Option<u8>,
    pub toggle: Option<bool>,
    pub period: Option<u64>, // in milliseconds
}

// ==============================
// ======== TOKEN COMMANDS ======
// ==============================

#[tauri::command]
pub fn get_webhook_token(app: AppHandle) -> Result<Option<String>, String> {
    let config = config::load_config(&app)?;
    Ok(config.webhook_token)
}

#[tauri::command]
pub fn regenerate_webhook_token(app: AppHandle) -> Result<String, String> {
    let mut config = config::load_config(&app)?;
    let new_token: String = thread_rng()
        .sample_iter(&Alphanumeric)
        .take(32)
        .map(char::from)
        .collect();

    config.webhook_token = Some(new_token.clone());
    config::save_config(&app, &config)?;
    Ok(new_token)
}

// ==============================
// ==== CONFIGURATION COMMANDS ===
// ==============================

#[tauri::command]
pub fn get_configured_relays(app: AppHandle) -> Result<Vec<ConfiguredRelay>, String> {
    let config = config::load_config(&app)?;
    Ok(config.relays)
}

#[tauri::command]
pub fn add_ch340_relay(app: AppHandle, port: String, channels: u8) -> Result<(), String> {
    let mut config = config::load_config(&app)?;
    if config.relays.iter().any(|r| r.id == port) {
        return Err(format!("Relay with ID '{}' already exists.", port));
    }

    let new_relay = ConfiguredRelay {
        id: port,
        relay_type: RelayType::CH340,
        channels: Some(channels),
    };

    config.relays.push(new_relay);
    config::save_config(&app, &config)
}

#[tauri::command]
pub fn add_hw348_relay(app: AppHandle, serial_number: String, channels: u8) -> Result<(), String> {
    let mut config = config::load_config(&app)?;
    if config.relays.iter().any(|r| r.id == serial_number) {
        return Err(format!("Relay with ID '{}' already exists.", serial_number));
    }

    let new_relay = ConfiguredRelay {
        id: serial_number,
        relay_type: RelayType::HW348,
        channels: Some(channels),
    };

    config.relays.push(new_relay);
    config::save_config(&app, &config)
}

#[tauri::command]
pub fn add_cp210x_relay(app: AppHandle, port: String, channels: u8) -> Result<(), String> {
    let mut config = config::load_config(&app)?;
    if config.relays.iter().any(|r| r.id == port) {
        return Err(format!("Relay with ID '{}' already exists.", port));
    }

    let new_relay = ConfiguredRelay {
        id: port,
        relay_type: RelayType::CP210x,
        channels: Some(channels),
    };

    config.relays.push(new_relay);
    config::save_config(&app, &config)
}

#[tauri::command]
pub fn remove_relay(app: AppHandle, id: String) -> Result<(), String> {
    let mut config = config::load_config(&app)?;
    config.relays.retain(|r| r.id != id);
    config::save_config(&app, &config)
}

// ==============================
// ====== RELAY ACTION LOGIC ====
// ==============================

#[tauri::command]
pub fn trigger_relay_action(
    app: AppHandle,
    connections: State<'_, ConnectionManager>,
    payload: RelayActionPayload,
) -> Result<(), String> {
    let toggle = payload.toggle.unwrap_or(false);
    let period = payload.period.unwrap_or(0);

    if toggle && period == 0 {
        return Err("Period must be greater than 0 for toggle action.".to_string());
    }

    let connections_arc = connections.0.clone();

    // --- Execute Initial Action ---
    execute_relay_action(&app, &connections_arc, &payload.id, &payload.action, payload.channel)?;

    // --- Handle Toggle if Requested ---
    if toggle {
        let app_handle = app.clone();
        let id_clone = payload.id.clone();
        let inverted_action = if payload.action == "on" { "off" } else { "on" }.to_string();
        let channel_clone = payload.channel;

        std::thread::spawn(move || {
            std::thread::sleep(std::time::Duration::from_millis(period));
            let _ = execute_relay_action(&app_handle, &connections_arc, &id_clone, &inverted_action, channel_clone);
        });
    }

    Ok(())
}

fn execute_relay_action(
    app: &AppHandle,
    connections: &Arc<Mutex<HashMap<String, Box<dyn SerialPort + Send>>>>,
    id: &str,
    action: &str,
    channel: Option<u8>,
) -> Result<(), String> {
    let config = config::load_config(app)?;
    let relay = config
        .relays
        .iter()
        .find(|r| r.id == id)
        .ok_or_else(|| format!("Relay with ID '{}' not found in config.", id))?;

    match relay.relay_type {
        RelayType::HW348 => {
            let ch = channel.ok_or_else(|| "Channel is required for HW348 relays.".to_string())?;
            let max_channels = relay.channels.ok_or_else(|| "Channel configuration is missing for HW348 relay.".to_string())?;
            hw348::trigger_hw348_action(&relay.id, action, ch, max_channels)
        }
        RelayType::CH340 => {
            let ch = channel.ok_or_else(|| "Channel is required for CH340 relays.".to_string())?;
            if let Some(max_channels) = relay.channels {
                if ch == 0 || ch > max_channels {
                    return Err(format!(
                        "Invalid channel '{}' for relay '{}'. Must be between 1 and {}.",
                        ch, id, max_channels
                    ));
                }
            }
            ch340::trigger_ch340_action(connections, &relay.id, action, ch)
        }
        RelayType::CP210x => {
            let ch = channel.ok_or_else(|| "Channel is required for CP210x relays.".to_string())?;
            if let Some(max_channels) = relay.channels {
                if ch == 0 || ch > max_channels {
                    return Err(format!(
                        "Invalid channel '{}' for relay '{}'. Must be between 1 and {}.",
                        ch, id, max_channels
                    ));
                }
            }
            cp210x::trigger_cp210x_action(connections, &relay.id, action, ch)
        }
    }
}
// ==============================
// ===== HELPER / DISCOVERY =====
// ==============================

#[tauri::command]
pub fn list_serial_ports() -> Result<Vec<String>, String> {
    let ports = serialport::available_ports().map_err(|e| e.to_string())?;
    Ok(ports.into_iter().map(|p| p.port_name).collect())
}

#[tauri::command]
pub fn list_hw348_relays() -> Result<Vec<UsbRelayInfo>, String> {
    hw348::list_hw348_relays()
}
