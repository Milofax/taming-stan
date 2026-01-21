# UniFi Network MCP Server

> **Stand:** Januar 2026

Vollständige Referenz für den UniFi Network MCP Server - Netzwerk-Management und -Monitoring.

## MCP-Funnel Aktivierung

```
discover_tools_by_words("unifi", enable=true)
```

## Überblick

Der UniFi Network MCP Server ermöglicht vollständige Kontrolle über UniFi Network Controller. Er bietet Tools für Firewall, Traffic-Routes, Port-Forwards, QoS, VPN, WLANs, Geräte, Clients und Statistiken.

**Wichtig:** Alle state-ändernden Tools erfordern `confirm=true`!

## Tool-Kategorien

### Firewall

| Tool | Beschreibung |
|------|-------------|
| `unifi_list_firewall_policies` | Firewall-Regeln auflisten |
| `unifi_get_firewall_policy_details` | Regel-Details abrufen |
| `unifi_toggle_firewall_policy` | Regel aktivieren/deaktivieren |
| `unifi_create_firewall_policy` | Neue Regel erstellen |
| `unifi_update_firewall_policy` | Regel aktualisieren |
| `unifi_list_firewall_zones` | Firewall-Zonen auflisten |
| `unifi_list_ip_groups` | IP-Gruppen auflisten |

### Traffic Routes

| Tool | Beschreibung |
|------|-------------|
| `unifi_list_traffic_routes` | Traffic-Routen auflisten |
| `unifi_get_traffic_route_details` | Route-Details abrufen |
| `unifi_toggle_traffic_route` | Route aktivieren/deaktivieren |
| `unifi_create_traffic_route` | Neue Route erstellen |

### Port Forwarding

| Tool | Beschreibung |
|------|-------------|
| `unifi_list_port_forwards` | Port-Forwards auflisten |
| `unifi_get_port_forward` | Forward-Details abrufen |
| `unifi_toggle_port_forward` | Forward aktivieren/deaktivieren |
| `unifi_create_port_forward` | Neuen Forward erstellen |

### QoS / Traffic Shaping

| Tool | Beschreibung |
|------|-------------|
| `unifi_list_qos_rules` | QoS-Regeln auflisten |
| `unifi_get_qos_rule_details` | Regel-Details |
| `unifi_toggle_qos_rule_enabled` | Regel aktivieren/deaktivieren |
| `unifi_create_qos_rule` | Neue QoS-Regel |

### Networks & WLANs

| Tool | Beschreibung |
|------|-------------|
| `unifi_list_networks` | Netzwerke auflisten |
| `unifi_get_network_details` | Netzwerk-Details |
| `unifi_create_network` | Neues Netzwerk (disabled by default!) |
| `unifi_list_wlans` | WLANs auflisten |
| `unifi_get_wlan_details` | WLAN-Details |
| `unifi_create_wlan` | Neues WLAN (disabled by default!) |

### VPN

| Tool | Beschreibung |
|------|-------------|
| `unifi_list_vpn_clients` | VPN-Clients auflisten |
| `unifi_get_vpn_client_details` | Client-Details |
| `unifi_update_vpn_client_state` | Client aktivieren/deaktivieren |
| `unifi_list_vpn_servers` | VPN-Server auflisten |

### Devices

| Tool | Beschreibung |
|------|-------------|
| `unifi_list_devices` | Alle Geräte auflisten |
| `unifi_get_device_details` | Geräte-Details |
| `unifi_reboot_device` | Gerät neustarten (disabled by default!) |
| `unifi_rename_device` | Gerät umbenennen |
| `unifi_adopt_device` | Gerät adoptieren (disabled by default!) |
| `unifi_upgrade_device` | Firmware upgraden (disabled by default!) |

### Clients

| Tool | Beschreibung |
|------|-------------|
| `unifi_list_clients` | Verbundene Clients |
| `unifi_get_client_details` | Client-Details |
| `unifi_list_blocked_clients` | Blockierte Clients |
| `unifi_block_client` | Client blockieren (disabled by default!) |
| `unifi_unblock_client` | Client entblockieren |
| `unifi_rename_client` | Client umbenennen |
| `unifi_force_reconnect_client` | Client neu verbinden |
| `unifi_authorize_guest` | Gast autorisieren (disabled by default!) |

### Statistics & System

| Tool | Beschreibung |
|------|-------------|
| `unifi_get_network_stats` | Netzwerk-Statistiken |
| `unifi_get_client_stats` | Client-Statistiken |
| `unifi_get_device_stats` | Geräte-Statistiken |
| `unifi_get_top_clients` | Top-Clients nach Traffic |
| `unifi_get_dpi_stats` | Deep Packet Inspection Stats |
| `unifi_get_alerts` | Alerts abrufen |
| `unifi_get_system_info` | System-Informationen |
| `unifi_get_network_health` | Netzwerk-Gesundheit |

### Meta-Tools

| Tool | Beschreibung |
|------|-------------|
| `unifi_tool_index` | Alle Tools mit Schemas auflisten |
| `unifi_async_start` | Async-Job starten |
| `unifi_async_status` | Job-Status prüfen |

## Kernkonzepte

### Tool Registration Mode (Lazy Loading)

Standardmäßig werden nur 3 Meta-Tools registriert (~200 Tokens):
- `unifi_tool_index`
- `unifi_async_start`
- `unifi_async_status`

Weitere Tools werden **lazy** bei Bedarf geladen (96% Token-Ersparnis!).

**Eager Mode aktivieren:**
```bash
UNIFI_TOOL_REGISTRATION_MODE=eager
```

### Permission System

Viele Tools sind standardmäßig deaktiviert:

**Deaktiviert (High-Risk):**
- Network/WLAN create/modify
- Device reboot/adopt/upgrade
- Client block/authorize

**Aktivieren via Environment:**
```bash
UNIFI_PERMISSIONS_NETWORKS_CREATE=true
UNIFI_PERMISSIONS_DEVICES_UPDATE=true
UNIFI_PERMISSIONS_CLIENTS_UPDATE=true
```

### Confirmation Required

Alle state-ändernden Operationen erfordern:
```json
{
  "confirm": true
}
```

## Beispiel-Workflows

### Netzwerk-Übersicht abrufen

```
1. unifi_get_system_info
   → Controller-Version, Site-Info

2. unifi_get_network_health
   → Gesamtstatus des Netzwerks

3. unifi_list_devices
   → Alle APs, Switches, Router

4. unifi_list_clients
   → Alle verbundenen Geräte
```

### Traffic-Analyse

```
1. unifi_get_top_clients (limit: 10)
   → Top 10 Clients nach Bandbreite

2. unifi_get_dpi_stats
   → Traffic nach Kategorien (Gaming, Streaming, etc.)

3. unifi_get_client_stats (mac_address: "xx:xx:xx:xx:xx:xx")
   → Details für spezifischen Client
```

### Firewall-Regel erstellen

```
1. unifi_list_firewall_zones
   → Verfügbare Zonen abrufen

2. unifi_list_ip_groups
   → Verfügbare IP-Gruppen

3. unifi_create_simple_firewall_policy
   - name: "Block IoT to LAN"
   - source_zone: "IoT"
   - destination_zone: "LAN"
   - action: "drop"
   - confirm: true
```

### Port-Forward einrichten

```
unifi_create_simple_port_forward
- name: "Minecraft Server"
- external_port: 25565
- internal_ip: "192.168.1.100"
- internal_port: 25565
- protocol: "tcp"
- confirm: true
```

### Client troubleshooten

```
1. unifi_get_client_details (mac_address)
   → Verbindungsdetails, Signal-Stärke

2. unifi_get_client_stats (mac_address)
   → Traffic-Historie

3. unifi_force_reconnect_client (mac_address, confirm: true)
   → Neu verbinden erzwingen
```

## Async Operations

Für lange Operationen (Upgrades, Bulk-Änderungen):

```json
// Job starten
{
  "name": "unifi_async_start",
  "arguments": {
    "tool": "unifi_upgrade_device",
    "arguments": {"mac_address": "xx:xx:xx", "confirm": true}
  }
}
→ {"jobId": "abc123"}

// Status prüfen
{
  "name": "unifi_async_status",
  "arguments": {"jobId": "abc123"}
}
→ {"status": "running"} oder {"status": "done", "result": {...}}
```

## Controller-Erkennung

Der Server erkennt automatisch den Controller-Typ:
- **UniFi OS** (UDM, Cloud Gateway): `/proxy/network/api/...`
- **Standalone Controller**: `/api/...`

Manual Override:
```bash
UNIFI_CONTROLLER_TYPE=proxy  # oder "direct"
```

## Sicherheitshinweise

1. **Lokaler Zugriff empfohlen** - Kein Cloud-Hosting ohne sichere Proxy
2. **Permissions einschränken** - Nur benötigte Tools aktivieren
3. **confirm=true** - Schützt vor versehentlichen Änderungen
4. **Credentials sicher speichern** - .env oder Secrets Manager
5. **Read-Only für Cloud LLMs** - Write-Ops nur mit lokalen LLMs

## Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| 404 Not Found | Falscher Controller-Typ | UNIFI_CONTROLLER_TYPE setzen |
| Permission denied | Tool deaktiviert | Environment-Variable setzen |
| confirm required | confirm: true fehlt | Parameter hinzufügen |
| Timeout | Lange Operation | async_start verwenden |

## Referenzen

- [UniFi Network MCP GitHub](https://github.com/sirkirby/unifi-network-mcp)
- [UniFi API Dokumentation](https://ubntwiki.com/products/software/unifi-controller/api)
- [Permissions Dokumentation](https://github.com/sirkirby/unifi-network-mcp/blob/main/docs/permissions.md)
