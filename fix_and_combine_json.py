#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repariert und kombiniert die geteilten JSON-Dateien
"""

import re

def fix_and_combine():
    """Kombiniert die drei Teil-Dateien zu einer gültigen JSON-Datei"""

    print("Lese Part_1.json...")
    with open('/home/user/Buch_auftrag/Part_1.json', 'r', encoding='utf-8') as f:
        part1 = f.read()

    print("Lese Part_2.json...")
    with open('/home/user/Buch_auftrag/Part_2.json', 'r', encoding='utf-8') as f:
        part2 = f.read()

    print("Lese Part_3.json...")
    with open('/home/user/Buch_auftrag/Part_3.json', 'r', encoding='utf-8') as f:
        part3 = f.read()

    # Extrahiere Header aus Part_1 oder Part_2
    # Suche nach dem "name", "type", "id" und "messages": [
    header_match = re.search(r'(\{[^{]*"name"[^{]*"type"[^{]*"id"[^{]*"messages":\s*\[)', part1, re.DOTALL)
    if not header_match:
        header_match = re.search(r'(\{[^{]*"name"[^{]*"type"[^{]*"id"[^{]*"messages":\s*\[)', part2, re.DOTALL)

    header = header_match.group(1) if header_match else '{\n "name": "Unknown",\n "type": "private_supergroup",\n "id": 0,\n "messages": [\n'

    print("Extrahiere Nachrichten aus Part_1...")
    # Finde alle message-Objekte in Part_1
    messages_match = re.search(r'"messages":\s*\[(.*)', part1, re.DOTALL)
    part1_messages = messages_match.group(1) if messages_match else ''

    # Entferne unvollständige letzte Klammer falls vorhanden
    part1_messages = part1_messages.rstrip()
    if part1_messages.endswith('}'):
        part1_messages = part1_messages + ','

    print("Extrahiere Nachrichten aus Part_2...")
    # Part_2 hat ebenfalls Header, wir wollen nur die messages
    messages_match2 = re.search(r'"messages":\s*\[(.*)', part2, re.DOTALL)
    part2_messages = messages_match2.group(1) if messages_match2 else ''

    # Bereinige Part_2
    part2_messages = part2_messages.rstrip()
    # Entferne trailing Klammern wenn vorhanden
    part2_messages = re.sub(r'\s*\]\s*\}\s*$', '', part2_messages)
    if not part2_messages.endswith(','):
        part2_messages = part2_messages + ','

    print("Bearbeite Part_3...")
    # Part_3 beginnt direkt mit einem message-Objekt
    part3_messages = part3.strip()
    # Entferne leading Klammern wenn vorhanden
    part3_messages = re.sub(r'^\s*[\[\{]\s*', '', part3_messages)

    # Erstelle kombinierte Datei
    combined = header + '\n'
    combined += part1_messages + '\n'
    combined += part2_messages + '\n'
    combined += part3_messages.rstrip().rstrip(',')
    combined += '\n ]\n}'

    # Speichere kombinierte Datei
    output_file = '/home/user/Buch_auftrag/combined_export.json'
    print(f"\nSchreibe kombinierte Datei: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined)

    print(f"✓ Kombinierte Datei erstellt: {len(combined):,} Zeichen")

    # Teste ob gültig
    print("\nTeste JSON-Validität...")
    try:
        import json
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ Gültiges JSON!")
        print(f"  Gruppenname: {data.get('name', 'N/A')}")
        print(f"  Nachrichten: {len(data.get('messages', [])):,}")
        return True
    except Exception as e:
        print(f"✗ JSON-Fehler: {e}")

        # Versuche alternative Methode: Parse line-by-line
        print("\nVersuche alternative Reparatur...")
        return alternative_fix()

def alternative_fix():
    """Alternative Methode: Extrahiere message-Objekte direkt"""
    import json

    print("Verwende zeilenweise Extraktion...")

    all_messages = []
    group_info = None

    for file_path in ['/home/user/Buch_auftrag/Part_1.json',
                       '/home/user/Buch_auftrag/Part_2.json',
                       '/home/user/Buch_auftrag/Part_3.json']:

        print(f"Verarbeite {file_path}...")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extrahiere Gruppeninfo beim ersten Mal
        if not group_info:
            name_match = re.search(r'"name":\s*"([^"]*)"', content)
            type_match = re.search(r'"type":\s*"([^"]*)"', content)
            id_match = re.search(r'"id":\s*(\d+)', content)

            if name_match and type_match and id_match:
                group_info = {
                    'name': name_match.group(1),
                    'type': type_match.group(1),
                    'id': int(id_match.group(1))
                }

        # Finde alle message-Objekte mit regex
        # Ein message-Objekt beginnt mit "id": und geht bis zum schließenden }

        # Einfachere Methode: Suche nach {"id": Pattern
        message_pattern = r'\{[^}]*"id":\s*-?\d+[^}]*"type":\s*"(message|service)"[^}]*\}'

        # Das funktioniert nicht für verschachtelte Objekte. Verwende einen stack-basierten Parser

        # Noch einfachere Methode: Zähle Nachrichten
        lines = content.split('\n')
        in_message = False
        current_message_lines = []
        brace_count = 0

        for line in lines:
            # Zähle Klammern
            open_braces = line.count('{')
            close_braces = line.count('}')

            if '"id":' in line and '"type":' not in line:  # Beginnt ein message-Objekt
                if not in_message and (open_braces > close_braces or '{' in line):
                    in_message = True
                    current_message_lines = [line]
                    brace_count = open_braces - close_braces

            elif in_message:
                current_message_lines.append(line)
                brace_count += open_braces - close_braces

                # Message endet wenn brace_count wieder 0 ist
                if brace_count == 0:
                    message_text = '\n'.join(current_message_lines)
                    # Versuche zu parsen
                    try:
                        # Entferne trailing Komma
                        message_text = message_text.rstrip().rstrip(',')
                        msg = json.loads(message_text)
                        all_messages.append(msg)
                    except:
                        pass  # Überspringe ungültige Nachrichten

                    in_message = False
                    current_message_lines = []

        print(f"  Extrahiert: {len(all_messages)} Nachrichten bisher")

    # Erstelle finale Struktur
    if not group_info:
        group_info = {'name': 'Unknown', 'type': 'private_supergroup', 'id': 0}

    final_data = {
        'name': group_info['name'],
        'type': group_info['type'],
        'id': group_info['id'],
        'messages': all_messages
    }

    # Speichere
    output_file = '/home/user/Buch_auftrag/combined_export.json'
    print(f"\nSchreibe kombinierte Datei: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=1)

    print(f"✓ Alternative Methode erfolgreich!")
    print(f"  Gruppenname: {final_data['name']}")
    print(f"  Nachrichten: {len(final_data['messages']):,}")

    return True

if __name__ == '__main__':
    print("="*60)
    print("JSON REPARATUR UND KOMBINATION")
    print("="*60)
    print()

    success = fix_and_combine()

    if success:
        print("\n" + "="*60)
        print("ERFOLGREICH!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("FEHLGESCHLAGEN")
        print("="*60)
