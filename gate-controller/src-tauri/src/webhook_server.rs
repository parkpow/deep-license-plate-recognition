use tiny_http::{Server, Response, Request, Header, Method};
use tauri::{AppHandle, Manager, State, Emitter};
use std::io::{Cursor, Read};
use serde_json::json;
use chrono::Utc;

use crate::config;
use crate::relay::{self, ConnectionManager, RelayActionPayload};

#[derive(Clone, serde::Serialize)]
struct WebhookLog {
    timestamp: String,
    success: bool,
    details: String,
    error_message: Option<String>,
}

#[derive(serde::Deserialize)]
struct WebhookPayload {
    id: String,
    action: String,
    channel: Option<u8>,
    toggle: Option<bool>,
    period: Option<u64>,
}

fn handle_request(req: &mut Request, app_handle: &AppHandle) -> Response<Cursor<Vec<u8>>> {
    let log_and_emit = |success: bool, details: String, error_message: Option<String>| {
        let log_entry = WebhookLog {
            timestamp: Utc::now().to_rfc3339(),
            success,
            details: details.clone(),
            error_message,
        };

        // Emit event to frontend
        if let Err(e) = app_handle.emit("webhook-log", &log_entry) {
            eprintln!("Failed to emit event: {}", e);
        }

        // Append to log file
        if let Err(e) = config::append_to_log(app_handle, &format!(
            "{} - Success: {} - Details: {} - Error: {}",
            log_entry.timestamp,
            log_entry.success,
            log_entry.details,
            log_entry.error_message.as_deref().unwrap_or("N/A")
        )) {
            eprintln!("Failed to write to log file: {}", e);
        }
    };

    let json_error = |status_code: i32, message: &str, details: String| {
        log_and_emit(false, details, Some(message.to_string()));
        let response_json = json!({
            "status": "error",
            "message": message
        });
        let response_body = serde_json::to_string(&response_json).unwrap_or_default();
        let mut response = Response::from_string(response_body).with_status_code(status_code);
        let json_header = Header::from_bytes(b"Content-Type", b"application/json").unwrap();
        response.add_header(json_header);
        response
    };

    // --- Auth Check ---
    let config = match config::load_config(app_handle) {
        Ok(c) => c,
        Err(e) => return json_error(500, "Failed to load configuration", e),
    };

    let stored_token = match config.webhook_token {
        Some(token) if !token.is_empty() => token,
        _ => {
            return json_error(
                401,
                "Unauthorized: Webhook token not configured",
                "Authentication failed".to_string(),
            );
        }
    };

    let auth_header = req.headers().iter().find(|h| h.field.equiv("Authorization"));
    if let Some(header) = auth_header {
        let header_val = header.value.as_str();
        if header_val.starts_with("Bearer ") {
            let token = &header_val[7..];
            if token != stored_token.as_str() {
                return json_error(
                    401,
                    "Unauthorized: Invalid token",
                    "Authentication failed".to_string(),
                );
            }
        } else {
            return json_error(
                401,
                "Unauthorized: Invalid auth header format",
                "Authentication failed".to_string(),
            );
        }
    } else {
        return json_error(
            401,
            "Unauthorized: Missing Authorization header",
            "Authentication failed".to_string(),
        );
    }

    // --- POS Health Check ---
    // Convert the URL to lowercase for case-insensitive checking.
    if req.url().to_lowercase().contains("?check=true") {
        log_and_emit(true, "Health check successful".to_string(), None);
        let response_json = json!({
            "status": "ok",
            "message": "Webhook server is running and token is valid."
        });
        let response_body = serde_json::to_string(&response_json).unwrap_or_default();
        let mut response = Response::from_string(response_body).with_status_code(200);
        let json_header = Header::from_bytes(b"Content-Type", b"application/json").unwrap();
        response.add_header(json_header);
        return response;
    }

    // --- Request Handling ---
    // Get only the part of the URL before '?' for validation.
    let path = req.url().split('?').next().unwrap_or("");
    if req.method() != &Method::Post || path != "/webhook" {
        return json_error(
            404,
            "Not Found: Expected POST /webhook",
            format!("Invalid request: {} {}", req.method(), req.url()),
        );
    }

    let mut content = String::new();
    if let Err(e) = req.as_reader().read_to_string(&mut content) {
        return json_error(
            400,
            &format!("Bad Request: Failed to read body: {}", e),
            "Request body error".to_string(),
        );
    }

    let payload: WebhookPayload = match serde_json::from_str(&content) {
        Ok(p) => p,
        Err(e) => return json_error(400, &format!("Bad Request: Invalid JSON: {}", e), content),
    };

    let details = format!(
        "Trigger relay '{}', action '{}', channel {:?}, toggle {:?}, period {:?}",
        payload.id, payload.action, payload.channel, payload.toggle, payload.period
    );

    // --- Relay Trigger ---
    let connections_state: State<ConnectionManager> = app_handle.state();
    let relay_payload = RelayActionPayload {
        id: payload.id.clone(),
        action: payload.action.clone(),
        channel: payload.channel,
        toggle: payload.toggle,
        period: payload.period,
    };

    match relay::trigger_relay_action(app_handle.clone(), connections_state, relay_payload) {
        Ok(_) => {
            log_and_emit(true, details, None);
            let response_json = json!({
                "status": "success",
                "id": payload.id,
                "action": payload.action
            });
            let response_body = serde_json::to_string(&response_json).unwrap_or_default();
            let mut response = Response::from_string(response_body);
            let json_header = Header::from_bytes(b"Content-Type", b"application/json").unwrap();
            response.add_header(json_header);
            response
        }
        Err(e) => json_error(500, &e, details),
    }
}

pub fn start_server(app_handle: AppHandle) {
    std::thread::spawn(move || {
        let server = match Server::http("0.0.0.0:4848") {
            Ok(s) => s,
            Err(e) => {
                eprintln!("Failed to start webhook server: {}", e);
                return;
            }
        };
        println!("Webhook server started on http://0.0.0.0:4848");

        for mut request in server.incoming_requests() {
            let response = handle_request(&mut request, &app_handle);
            if let Err(e) = request.respond(response) {
                eprintln!("Failed to send response: {}", e);
            }
        }
    });
}
