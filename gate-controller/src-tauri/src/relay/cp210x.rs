use std::collections::HashMap;
use std::io::Write;
use std::sync::{Arc, Mutex};

use serialport::{self, SerialPort};

// ==============================
// ====== RELAY ACTION LOGIC ====
// ==============================

pub fn trigger_cp210x_action(
    connections: &Arc<Mutex<HashMap<String, Box<dyn SerialPort + Send>>>>,
    port_name: &str,
    action: &str,
    channel: u8,
) -> Result<(), String> {
    let mut connections_guard = connections.lock().unwrap();
    if !connections_guard.contains_key(port_name) {
        let port = serialport::new(port_name, 9600)
            .timeout(std::time::Duration::from_millis(500))
            .open()
            .map_err(|e| format!("Failed to open serial port '{}': {}", port_name, e))?;
        connections_guard.insert(port_name.to_string(), port);
        // Wait for the serial device to initialize
        std::thread::sleep(std::time::Duration::from_millis(200)); 
    }

    let serial_port = connections_guard.get_mut(port_name).unwrap();
    
    let action_val = if action == "on" { 1 } else { 0 };
    let cmd_str = format!("AT+CH{}={}\r\n", channel, action_val);
    let command = cmd_str.as_bytes();

    match serial_port.write_all(command) {
        Ok(_) => Ok(()),
        Err(e) => {
            // Connection is likely stale. Remove it from the cache
            // so the next attempt will try to reconnect.
            connections_guard.remove(port_name);
            Err(format!(
                "Failed to write to serial port '{}': {}. It may have been disconnected.",
                port_name, e
            ))
        }
    }
}
