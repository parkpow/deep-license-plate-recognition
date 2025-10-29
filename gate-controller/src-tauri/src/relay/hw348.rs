use std::process::Command;
use std::path::PathBuf;
#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

// ==============================
// ===== HELPER / DISCOVERY =====
// ==============================

#[derive(serde::Serialize, serde::Deserialize, Debug)]
pub struct UsbRelayInfo {
    pub serial_number: String,
    pub relay_type: String,
}

pub fn list_hw348_relays() -> Result<Vec<UsbRelayInfo>, String> {
    let usbrelay_exe_path = get_usbrelay_path()?;
    let output = Command::new(&usbrelay_exe_path)
        .arg("-list")
        .creation_flags(0x08000000)
        .output()
        .map_err(|e| e.to_string())?;

    if !output.status.success() {
        return Err(format!(
            "usbrelay.exe failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let relays = stdout
        .lines()
        .skip(2)
        .filter(|line| !line.trim().is_empty())
        .filter_map(|line| {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 2 {
                Some(UsbRelayInfo {
                    serial_number: parts[0].to_string(),
                    relay_type: parts[1].to_string(),
                })
            } else {
                None
            }
        })
        .collect();

    Ok(relays)
}

// ==============================
// ====== RELAY ACTION LOGIC ====
// ==============================

pub fn trigger_hw348_action(
    serial_number: &str,
    action: &str,
    channel: u8,
    max_channels: u8,
) -> Result<(), String> {
    if channel == 0 || channel > max_channels {
        return Err(format!(
            "Invalid channel '{}' for relay '{}'. Must be between 1 and {}.",
            channel, serial_number, max_channels
        ));
    }
    match action {
        "on" => run_usbrelay_command(serial_number, "-on", channel),
        "off" => run_usbrelay_command(serial_number, "-off", channel),
        _ => Err("Invalid action for HW348 relay.".to_string()),
    }
}

// ==============================
// ===== USB RELAY HELPERS ======
// ==============================

fn run_usbrelay_command(serial_number: &str, action: &str, channel: u8) -> Result<(), String> {
    let usbrelay_exe_path = get_usbrelay_path()?;
    let output = Command::new(&usbrelay_exe_path)
        .arg("-serial")
        .arg(serial_number)
        .arg(action)
        .arg(channel.to_string())
        .creation_flags(0x08000000)
        .output()
        .map_err(|e| e.to_string())?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_lowercase();
    let stderr = String::from_utf8_lossy(&output.stderr).to_lowercase();

    if !output.status.success() || stderr.contains("error") || stderr.contains("failed") || stdout.contains("error") {
        let full_error = format!("{}{}", stderr.trim(), stdout.trim()).trim().to_string();
        return Err(
            if full_error.is_empty() {
                format!("USB relay command failed with exit code {}.", output.status.code().unwrap_or(-1))
            } else {
                full_error
            },
        );
    }

    Ok(())
}

// ==============================
// ===== PATH HELPERS ============
// ==============================

fn get_usbrelay_path() -> Result<PathBuf, String> {
    let mut path = std::env::current_exe().map_err(|e| e.to_string())?;
    path.pop(); // remove exe itself
    path.push("usbrelay");
    path.push("usbrelay.exe");

    if !path.exists() {
        return Err(format!("usbrelay.exe not found at {:?}", path));
    }

    Ok(path)
}
