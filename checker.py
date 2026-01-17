import socket
import json
import os

# --- CONFIGURATION ---
# YOUR SPECIFIC SERVER
SERVERS = [
    {"ip": "16.24.95.100", "port": 26001, "name": "DON CLAN IGI2"}
]
# ---------------------

def parse_igi2_response(raw_data):
    # Decode the weird IGI 2 text format
    decoded = raw_data.decode('latin-1', errors='replace')
    parts = decoded.split('\\')
    data_map = {}
    
    # Create a dictionary from the raw list
    for i in range(1, len(parts)-1, 2):
        data_map[parts[i]] = parts[i+1]

    # 1. Extract Global Info
    server_info = {
        "hostname": data_map.get("hostname", "Unknown"),
        "mapname": data_map.get("mapname", "Unknown"),
        "players_count": f"{data_map.get('numplayers', 0)}/{data_map.get('maxplayers', 0)}",
        "timeleft": data_map.get("timeleft", "00:00"),
        "score_igi": data_map.get("score_t0", "0"),
        "score_con": data_map.get("score_t1", "0"),
        "team_igi_players": [],
        "team_con_players": []
    }

    # 2. Extract Players (The hard part)
    for key, name in data_map.items():
        if key.startswith("player_"):
            player_id = key.split("_")[1] # Get ID like '11' or '7'
            
            p_stats = {
                "name": name,
                "frags": data_map.get(f"frags_{player_id}", "0"),
                "deaths": data_map.get(f"deaths_{player_id}", "0"),
                "ping": data_map.get(f"ping_{player_id}", "0"),
                "team": data_map.get(f"team_{player_id}", "0") # 0=IGI, 1=CON
            }
            
            # Sort players into Blue (IGI) or Red (CON) teams
            if p_stats["team"] == "0":
                server_info["team_igi_players"].append(p_stats)
            else:
                server_info["team_con_players"].append(p_stats)

    return server_info

def check_servers():
    output = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3.0) # 3 second timeout

    for srv in SERVERS:
        try:
            # Send the magic query
            sock.sendto(b'\\status\\', (srv["ip"], srv["port"]))
            data, _ = sock.recvfrom(8192)
            
            # Parse response
            parsed_data = parse_igi2_response(data)
            parsed_data["status"] = "Online"
            output.append(parsed_data)
        except:
            # If server is down/timeout
            output.append({
                "hostname": srv["name"], 
                "status": "Offline",
                "mapname": "-",
                "timeleft": "--:--",
                "score_igi": 0, "score_con": 0,
                "team_igi_players": [], "team_con_players": []
            })
    
    sock.close()
    
    # Save results to 'status.json'
    with open("status.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    check_servers()
