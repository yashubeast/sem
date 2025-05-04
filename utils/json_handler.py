import json, os

predefined_json_paths = {
	"config": "assets/config.json",
	"server": "assets/server.json",
	"sticky": "assets/sticky.json"
}

def resolve_json_path(json_path):
	return predefined_json_paths.get(json_path, json_path)

def ensure_json(json_path):
	os.makedirs(os.path.dirname(json_path), exist_ok=True)
	if not os.path.isfile(json_path):
		with open(json_path, "w", encoding="utf-8") as f:
			json.dump({}, f, indent=4)

def json_load(json_path):
	json_path = resolve_json_path(json_path)
	ensure_json(json_path)
	with open(json_path, "r", encoding="utf-8") as f:
		return json.load(f)

def json_save(json_path, data):
	json_path = resolve_json_path(json_path)
	ensure_json(json_path)
	with open(json_path, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=4)