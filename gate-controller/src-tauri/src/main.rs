#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod config;
mod relay;
mod webhook_server;

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use relay::ConnectionManager;

fn main() {
    tauri::Builder::default()
        .manage(ConnectionManager(Arc::new(Mutex::new(HashMap::new()))))
        .setup(|app| {
            webhook_server::start_server(app.handle().clone());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // New config commands
            relay::get_configured_relays,
            relay::add_ch340_relay,
            relay::add_hw348_relay,
            relay::add_cp210x_relay,
            relay::remove_relay,
            relay::trigger_relay_action,
            // Existing discovery commands
            relay::list_serial_ports,
            relay::list_hw348_relays,
            // Token commands
            relay::get_webhook_token,
            relay::regenerate_webhook_token
        ])
        .run(tauri::generate_context!())
        .expect("error while running Tauri application");
}
