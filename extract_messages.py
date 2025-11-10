#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robuster Message-Extraktor für JSON-Export
"""

import json
import re

def extract_group_info(content):
    """Extrahiert Gruppenfunktionen aus dem JSON"""
    name_match = re.search(r'"name":\s*"([^"]*)"', content)
    type_match = re.search(r'"type":\s*"([^"]*)"', content)
    id_match = re.search(r'"id":\s*(\d+)', content)

    return {
        'name': name_match.group(1) if name_match else 'Unknown',
        'type': type_match.group(1) if type_match else 'private_supergroup',
        'id': int(id_match.group(1)) if id_match else 0
    }

def extract_messages_from_file(file_path):
    """Extrahiert alle message-Objekte aus einer Datei mit Klammer-Zählung"""
    print(f"\nVerarbeite: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    messages = []
    i = 0
    in_string = False
    escape = False

    while i < len(content):
        # Suche nach Beginn eines Objekts mit "id":
        if content[i:i+10].find('"id":') == 0 or (
            content[i:i+20].find('{\n   "id":') >= 0 and content[i] == '{'):

            # Gehe zurück zum letzten {
            start = i
            while start > 0 and content[start] != '{':
                start -= 1

            # Jetzt haben wir den Start. Finde das Ende mit Klammer-Zählung
            brace_count = 0
            j = start
            in_string = False
            escape = False
            obj_start = start

            while j < len(content):
                char = content[j]

                # String-Handling
                if char == '\\' and not escape:
                    escape = True
                    j += 1
                    continue

                if char == '"' and not escape:
                    in_string = not in_string

                escape = False

                # Nur Klammern außerhalb von Strings zählen
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1

                        # Wenn wir wieder bei 0 sind, haben wir das Objekt komplett
                        if brace_count == 0:
                            obj_text = content[obj_start:j+1]

                            # Versuche zu parsen
                            try:
                                obj = json.loads(obj_text)

                                # Prüfe ob es ein message-Objekt ist
                                if 'id' in obj and 'type' in obj:
                                    messages.append(obj)

                            except json.JSONDecodeError:
                                pass  # Überspringe ungültige Objekte

                            # Springe zum Ende dieses Objekts
                            i = j + 1
                            break

                j += 1

            # Falls wir hier ankommen ohne match, gehe zum nächsten Zeichen
            if j >= len(content):
                i += 1

        else:
            i += 1

    print(f"  Gefunden: {len(messages)} Nachrichten")
    return messages

def main():
    """Hauptfunktion"""
    print("="*60)
    print("MESSAGE EXTRAKTOR")
    print("="*60)

    file_paths = [
        '/home/user/Buch_auftrag/Part_1.json',
        '/home/user/Buch_auftrag/Part_2.json',
        '/home/user/Buch_auftrag/Part_3.json'
    ]

    all_messages = []
    group_info = None

    for file_path in file_paths:
        # Extrahiere Gruppeninfo beim ersten Mal
        if not group_info:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(10000)  # Erste 10KB sollten reichen
            group_info = extract_group_info(content)

        # Extrahiere Nachrichten
        messages = extract_messages_from_file(file_path)
        all_messages.extend(messages)

    print(f"\n{'='*60}")
    print(f"GESAMT: {len(all_messages)} Nachrichten extrahiert")
    print(f"Gruppe: {group_info['name']}")
    print(f"{'='*60}")

    # Erstelle finales JSON
    final_data = {
        'name': group_info['name'],
        'type': group_info['type'],
        'id': group_info['id'],
        'messages': all_messages
    }

    # Speichere
    output_file = '/home/user/Buch_auftrag/combined_export.json'
    print(f"\nSchreibe: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=1)

    print("✓ Erfolgreich gespeichert!")

    # Validiere
    print("\nValidiere...")
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"✓ Gültiges JSON mit {len(data['messages']):,} Nachrichten")

if __name__ == '__main__':
    main()
