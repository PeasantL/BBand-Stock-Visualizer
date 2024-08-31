import json

def open_json(file_name):
    try:
        with open(file_name, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    
def save_json(file_name, file_data):
    with open(file_name, 'w') as file:
        json.dump(file_data, file)