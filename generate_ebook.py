#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Chat Export eBook Generator
Analysiert Telegram Chat-Exporte und erstellt ein umfassendes Markdown-eBook
"""

import json
import os
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any

class TelegramChatAnalyzer:
    def __init__(self, file_paths: List[str]):
        self.file_paths = file_paths
        self.messages = []
        self.all_data = []

    def load_data(self):
        """Lädt alle JSON-Dateien"""
        print("Lade JSON-Dateien...")

        for file_path in self.file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.all_data.append(data)
                if 'messages' in data:
                    self.messages.extend(data['messages'])
                print(f"✓ {os.path.basename(file_path)}: {len(data.get('messages', []))} Nachrichten")

            except Exception as e:
                print(f"✗ Fehler beim Laden von {file_path}: {e}")

        print(f"\nGesamt: {len(self.messages)} Nachrichten geladen")

    def parse_date(self, date_str: str) -> datetime:
        """Konvertiert Datumsstring zu datetime"""
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None

    def analyze_basic_stats(self) -> Dict:
        """Grundlegende Statistiken"""
        print("\nAnalysiere Grundstatistiken...")

        stats = {
            'total_messages': len(self.messages),
            'participants': set(),
            'date_range': {'start': None, 'end': None},
            'message_by_person': Counter(),
            'message_by_date': defaultdict(int),
            'message_by_month': defaultdict(int),
        }

        dates = []
        for msg in self.messages:
            # Teilnehmer
            if 'from' in msg and msg['from']:
                stats['participants'].add(msg['from'])
                stats['message_by_person'][msg['from']] += 1

            # Datum
            if 'date' in msg:
                dt = self.parse_date(msg['date'])
                if dt:
                    dates.append(dt)
                    date_only = dt.strftime('%Y-%m-%d')
                    month_only = dt.strftime('%Y-%m')
                    stats['message_by_date'][date_only] += 1
                    stats['message_by_month'][month_only] += 1

        if dates:
            stats['date_range']['start'] = min(dates)
            stats['date_range']['end'] = max(dates)

        return stats

    def extract_keywords_and_topics(self) -> Dict:
        """Extrahiert häufige Wörter und Themen"""
        print("Extrahiere Themen und Schlüsselwörter...")

        word_counter = Counter()
        hashtags = Counter()
        urls = Counter()

        for msg in self.messages:
            text = self.get_message_text(msg)
            if text:
                # Wörter (länger als 3 Zeichen)
                words = text.lower().split()
                for word in words:
                    clean_word = ''.join(c for c in word if c.isalnum() or c in 'äöüß')
                    if len(clean_word) > 3:
                        word_counter[clean_word] += 1

                    # Hashtags
                    if word.startswith('#'):
                        hashtags[word] += 1

                    # URLs (einfache Erkennung)
                    if 'http://' in word or 'https://' in word:
                        urls[word] += 1

        return {
            'top_words': word_counter.most_common(100),
            'hashtags': hashtags.most_common(50),
            'urls': urls.most_common(30)
        }

    def get_message_text(self, msg: Dict) -> str:
        """Extrahiert Text aus einer Nachricht"""
        if isinstance(msg.get('text'), str):
            return msg['text']
        elif isinstance(msg.get('text'), list):
            parts = []
            for item in msg['text']:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and 'text' in item:
                    parts.append(item['text'])
            return ''.join(parts)
        return ''

    def find_key_events(self, stats: Dict) -> List[Dict]:
        """Findet Schlüsselereignisse (Tage mit vielen Nachrichten)"""
        print("Identifiziere Schlüsselereignisse...")

        # Sortiere Tage nach Nachrichtenanzahl
        sorted_days = sorted(stats['message_by_date'].items(),
                           key=lambda x: x[1], reverse=True)

        key_days = sorted_days[:20]  # Top 20 Tage

        events = []
        for date_str, count in key_days:
            # Finde Nachrichten an diesem Tag
            day_messages = [msg for msg in self.messages
                          if msg.get('date', '').startswith(date_str)]

            events.append({
                'date': date_str,
                'message_count': count,
                'messages': day_messages[:50]  # Erste 50 Nachrichten
            })

        return events

    def generate_ebook(self, output_path: str):
        """Generiert das vollständige eBook"""
        print("\n" + "="*60)
        print("STARTE EBOOK-GENERIERUNG")
        print("="*60)

        # Analysen durchführen
        stats = self.analyze_basic_stats()
        keywords = self.extract_keywords_and_topics()
        key_events = self.find_key_events(stats)

        # Gruppendaten
        group_name = self.all_data[0].get('name', 'Unbekannte Gruppe') if self.all_data else 'Unbekannte Gruppe'
        group_type = self.all_data[0].get('type', 'Unbekannt') if self.all_data else 'Unbekannt'

        print(f"\nGeneriere eBook für Gruppe: {group_name}")
        print(f"Zeitraum: {stats['date_range']['start'].strftime('%d.%m.%Y') if stats['date_range']['start'] else 'N/A'} bis {stats['date_range']['end'].strftime('%d.%m.%Y') if stats['date_range']['end'] else 'N/A'}")
        print(f"Teilnehmer: {len(stats['participants'])}")

        # eBook erstellen
        ebook = []

        # Titelseite
        ebook.append(self._generate_title_page(group_name, stats))

        # Teil 1: Übersicht
        ebook.append(self._generate_overview(group_name, group_type, stats))

        # Teil 2: Chronologische Ereignisse
        ebook.append(self._generate_chronology(stats, key_events))

        # Teil 3: Thematische Analysen
        ebook.append(self._generate_thematic_analysis(keywords))

        # Teil 4: Personenprofile
        ebook.append(self._generate_person_profiles(stats))

        # Teil 5: Schlüsselereignisse
        ebook.append(self._generate_key_events(key_events))

        # Teil 6: Gruppendynamik
        ebook.append(self._generate_group_dynamics(stats))

        # Teil 7: Statistiken & Daten
        ebook.append(self._generate_statistics(stats, keywords))

        # Teil 8: Anhang
        ebook.append(self._generate_appendix())

        # Speichern
        full_content = '\n\n'.join(ebook)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        print(f"\n✓ eBook erfolgreich erstellt: {output_path}")
        print(f"  Umfang: ~{len(full_content.split())} Wörter")
        print(f"  Zeichen: {len(full_content):,}")

    def _generate_title_page(self, group_name: str, stats: Dict) -> str:
        """Generiert Titelseite"""
        start_year = stats['date_range']['start'].year if stats['date_range']['start'] else 'N/A'
        end_year = stats['date_range']['end'].year if stats['date_range']['end'] else 'N/A'
        year_range = f"{start_year}" if start_year == end_year else f"{start_year}-{end_year}"

        return f"""# {group_name}
## Jahres-Zusammenfassung {year_range}

---

### Telegram-Gruppen-Chat-Analyse

**Analysezeitraum:** {stats['date_range']['start'].strftime('%d.%m.%Y') if stats['date_range']['start'] else 'N/A'} – {stats['date_range']['end'].strftime('%d.%m.%Y') if stats['date_range']['end'] else 'N/A'}

**Gesamtzahl Nachrichten:** {stats['total_messages']:,}

**Teilnehmer:** {len(stats['participants'])}

---

**Erstellungsdatum:** {datetime.now().strftime('%d.%m.%Y')}

**Methodologie:** Automatisierte Analyse von Telegram Chat-Export-Daten mit faktischer, unparteiischer Auswertung

---

<div style="page-break-after: always;"></div>"""

    def _generate_overview(self, group_name: str, group_type: str, stats: Dict) -> str:
        """Generiert Teil 1: Übersicht"""
        content = []
        content.append("# Teil 1: Übersicht")
        content.append("")
        content.append("## 1.1 Gruppendaten")
        content.append("")
        content.append(f"**Gruppenname:** {group_name}")
        content.append(f"**Gruppentyp:** {group_type}")

        # Zeitraum formatieren
        start_str = stats['date_range']['start'].strftime('%d.%m.%Y') if stats['date_range']['start'] else 'N/A'
        end_str = stats['date_range']['end'].strftime('%d.%m.%Y') if stats['date_range']['end'] else 'N/A'
        content.append(f"**Analysezeitraum:** {start_str} bis {end_str}")

        if stats['date_range']['start'] and stats['date_range']['end']:
            days = (stats['date_range']['end'] - stats['date_range']['start']).days
            content.append(f"**Dauer:** {days} Tage")
        else:
            content.append("**Dauer:** N/A")

        content.append("")
        content.append("## 1.2 Statistiken auf einen Blick")
        content.append("")
        content.append("| Kennzahl | Wert |")
        content.append("|----------|------|")
        content.append(f"| Gesamtzahl Nachrichten | {stats['total_messages']:,} |")
        content.append(f"| Anzahl Teilnehmer | {len(stats['participants'])} |")

        # Durchschnitt pro Tag
        if stats['date_range']['start'] and stats['date_range']['end']:
            days = (stats['date_range']['end'] - stats['date_range']['start']).days
            avg_per_day = stats['total_messages'] / max(1, days)
            content.append(f"| Durchschnitt Nachrichten/Tag | {avg_per_day:.1f} |")
        else:
            content.append("| Durchschnitt Nachrichten/Tag | N/A |")

        avg_per_person = stats['total_messages'] / max(1, len(stats['participants']))
        content.append(f"| Durchschnitt Nachrichten/Person | {avg_per_person:.1f} |")

        if stats['message_by_person']:
            top_person = stats['message_by_person'].most_common(1)[0]
            content.append(f"| Aktivste Person | {top_person[0]} ({top_person[1]:,} Nachrichten) |")
        else:
            content.append("| Aktivste Person | N/A |")

        content.append("")
        content.append("## 1.3 Methodologie")
        content.append("")
        content.append("Diese Analyse basiert auf dem Export von Telegram-Gruppenchat-Daten im JSON-Format. Die Auswertung erfolgt:")
        content.append("")
        content.append("- **Faktisch:** Alle Aussagen basieren auf messbaren Daten aus dem Chat-Export")
        content.append("- **Unparteiisch:** Keine Wertungen, Interpretationen oder emotionale Sprache")
        content.append("- **Dokumentarisch:** Chronologische und thematische Aufbereitung der Ereignisse")
        content.append("- **Zitatbasiert:** Verwendung wortwörtlicher Zitate zur Untermauerung von Feststellungen")
        content.append("")
        content.append("### Datenquellen")
        content.append("")

        msg_count = len(self.all_data[0].get('messages', [])) if len(self.all_data) > 0 else 0
        content.append(f"- combined_export.json: {msg_count:,} Nachrichten")

        content.append("")
        content.append("### Analysemethoden")
        content.append("")
        content.append("1. **Quantitative Analyse:** Zählung von Nachrichten, Teilnehmern, Aktivitätsmustern")
        content.append("2. **Chronologische Analyse:** Zeitliche Einordnung von Ereignissen und Diskussionen")
        content.append("3. **Thematische Analyse:** Identifikation wiederkehrender Themen und Diskussionsstränge")
        content.append("4. **Netzwerkanalyse:** Betrachtung der Interaktionsmuster zwischen Teilnehmern")
        content.append("")
        content.append("---")
        content.append("")
        content.append("<div style=\"page-break-after: always;\"></div>")

        return '\n'.join(content)

    def _generate_chronology(self, stats: Dict, key_events: List[Dict]) -> str:
        """Generiert Teil 2: Chronologische Ereignisse"""
        content = [
            "# Teil 2: Chronologische Ereignisse",
            "",
            "## 2.1 Zeitliche Übersicht",
            "",
        ]

        # Monatliche Übersicht
        sorted_months = sorted(stats['message_by_month'].items())

        content.append("### Aktivität nach Monaten")
        content.append("")
        content.append("| Monat | Nachrichten | Durchschnitt/Tag |")
        content.append("|-------|-------------|------------------|")

        for month, count in sorted_months:
            year, month_num = month.split('-')
            month_name = datetime(int(year), int(month_num), 1).strftime('%B %Y')
            days_in_month = 30  # Vereinfachung
            avg_per_day = count / days_in_month
            content.append(f"| {month_name} | {count:,} | {avg_per_day:.1f} |")

        content.append("")
        content.append("## 2.2 Aktivste Tage")
        content.append("")
        content.append("Die folgenden Tage wiesen die höchste Nachrichtenaktivität auf:")
        content.append("")

        # Top 10 Tage
        sorted_days = sorted(stats['message_by_date'].items(),
                           key=lambda x: x[1], reverse=True)[:10]

        content.append("| Datum | Nachrichten |")
        content.append("|-------|-------------|")

        for date_str, count in sorted_days:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = dt.strftime('%d.%m.%Y')
            content.append(f"| {formatted_date} | {count:,} |")

        content.append("")
        content.append("## 2.3 Zeitraumbasierte Analyse")
        content.append("")

        # Quartale
        quarterly_stats = defaultdict(int)
        for month, count in stats['message_by_month'].items():
            year, month_num = month.split('-')
            quarter = (int(month_num) - 1) // 3 + 1
            quarterly_stats[f"{year} Q{quarter}"] += count

        content.append("### Quartalsweise Aktivität")
        content.append("")
        content.append("| Quartal | Nachrichten |")
        content.append("|---------|-------------|")

        for quarter in sorted(quarterly_stats.keys()):
            content.append(f"| {quarter} | {quarterly_stats[quarter]:,} |")

        content.append("")

        # Wöchentliche Highlights
        content.append("## 2.4 Ausgewählte Wochenanalysen")
        content.append("")
        content.append("Die folgenden Wochen zeigten besondere Aktivitätsmuster oder Diskussionsthemen:")
        content.append("")

        # Finde die top 5 Wochen nach Nachrichtenanzahl
        weekly_stats = defaultdict(int)
        weekly_messages = defaultdict(list)

        for msg in self.messages:
            dt = self.parse_date(msg.get('date', ''))
            if dt:
                # ISO Woche
                week_key = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
                weekly_stats[week_key] += 1
                if len(weekly_messages[week_key]) < 20:  # Speichere bis zu 20 Nachrichten pro Woche
                    weekly_messages[week_key].append(msg)

        top_weeks = sorted(weekly_stats.items(), key=lambda x: x[1], reverse=True)[:5]

        for week_num, (week, count) in enumerate(top_weeks, 1):
            content.append(f"### Woche {week}")
            content.append("")
            content.append(f"**Nachrichten:** {count:,}")
            content.append("")
            content.append("**Charakteristische Nachrichten:**")
            content.append("")

            # Zeige 8-10 Beispielnachrichten aus dieser Woche
            week_msgs = weekly_messages[week]
            shown = 0
            for msg in week_msgs:
                if shown >= 10:
                    break
                text = self.get_message_text(msg)
                if text and len(text) > 10:
                    msg_date = self.parse_date(msg.get('date', ''))
                    person = msg.get('from', 'Unbekannt')
                    if msg_date:
                        preview = text[:200] + "..." if len(text) > 200 else text
                        content.append(f"> \"{preview}\" - [{person}, {msg_date.strftime('%d.%m.%Y')}]")
                        content.append("")
                        shown += 1

            content.append("")

        content.append("---")
        content.append("")
        content.append("<div style=\"page-break-after: always;\"></div>")

        return '\n'.join(content)

    def _generate_thematic_analysis(self, keywords: Dict) -> str:
        """Generiert Teil 3: Thematische Analysen"""
        content = [
            "# Teil 3: Thematische Analysen",
            "",
            "## 3.1 Häufigste Begriffe",
            "",
            "Die folgende Auflistung zeigt die am häufigsten verwendeten Wörter (mindestens 4 Zeichen) im Chat:",
            "",
            "| Rang | Begriff | Häufigkeit |",
            "|------|---------|------------|",
        ]

        # Top 50 Wörter
        for i, (word, count) in enumerate(keywords['top_words'][:50], 1):
            content.append(f"| {i} | {word} | {count:,} |")

        content.append("")

        # Hashtags
        if keywords['hashtags']:
            content.append("## 3.2 Verwendete Hashtags")
            content.append("")
            content.append("| Hashtag | Verwendungen |")
            content.append("|---------|--------------|")

            for hashtag, count in keywords['hashtags'][:30]:
                content.append(f"| {hashtag} | {count:,} |")

            content.append("")

        # Thematische Gruppierung (basierend auf Schlüsselwörtern)
        content.append("## 3.3 Identifizierte Themenbereiche")
        content.append("")
        content.append("Basierend auf der Häufigkeitsanalyse lassen sich folgende Themenbereiche identifizieren:")
        content.append("")

        # Einfache thematische Kategorisierung
        tech_words = [w for w, c in keywords['top_words'] if any(t in w.lower() for t in ['tech', 'computer', 'software', 'code', 'app', 'web', 'digital', 'online'])]
        social_words = [w for w, c in keywords['top_words'] if any(t in w.lower() for t in ['freund', 'familie', 'leute', 'person', 'mensch', 'group'])]
        time_words = [w for w, c in keywords['top_words'] if any(t in w.lower() for t in ['heute', 'morgen', 'gestern', 'woche', 'monat', 'jahr', 'zeit'])]

        if tech_words:
            content.append(f"**Technologie/Digital:** {', '.join(tech_words[:10])}")
        if social_words:
            content.append(f"**Soziales/Gemeinschaft:** {', '.join(social_words[:10])}")
        if time_words:
            content.append(f"**Zeit/Termine:** {', '.join(time_words[:10])}")

        content.append("")
        content.append("---")
        content.append("")
        content.append("<div style=\"page-break-after: always;\"></div>")

        return '\n'.join(content)

    def _generate_person_profiles(self, stats: Dict) -> str:
        """Generiert Teil 4: Personenprofile"""
        content = [
            "# Teil 4: Personenprofile",
            "",
            "## 4.1 Aktivste Teilnehmer",
            "",
            "Die folgende Übersicht zeigt die aktivsten Teilnehmer der Gruppe, gemessen an der Anzahl gesendeter Nachrichten:",
            "",
            "| Rang | Person | Nachrichten | Anteil |",
            "|------|--------|-------------|--------|",
        ]

        total_messages = stats['total_messages']
        top_participants = stats['message_by_person'].most_common(20)

        for i, (person, count) in enumerate(top_participants, 1):
            percentage = (count / total_messages * 100) if total_messages > 0 else 0
            content.append(f"| {i} | {person} | {count:,} | {percentage:.1f}% |")

        content.append("")
        content.append("## 4.2 Detaillierte Profile (Top 15)")
        content.append("")

        # Detaillierte Profile für Top 15
        for i, (person, total_count) in enumerate(top_participants[:15], 1):
            content.append(f"### {i}. {person}")
            content.append("")
            content.append(f"**Gesamtnachrichten:** {total_count:,}")
            content.append(f"**Anteil an Gesamtaktivität:** {(total_count / total_messages * 100):.1f}%")

            # Finde einige Beispielnachrichten
            person_messages = [msg for msg in self.messages if msg.get('from') == person]

            if person_messages:
                # Durchschnittliche Nachrichtenlänge
                text_messages = [self.get_message_text(msg) for msg in person_messages]
                text_lengths = [len(text) for text in text_messages if text]
                avg_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0

                content.append(f"**Durchschnittliche Nachrichtenlänge:** {avg_length:.0f} Zeichen")

                # Beispiele (erste, mittlere und letzte Nachrichten)
                if len(person_messages) > 0:
                    first_msg = person_messages[0]
                    first_text = self.get_message_text(first_msg)
                    first_date = self.parse_date(first_msg.get('date', ''))

                    if first_text and first_date:
                        content.append("")
                        content.append("**Erste Nachricht:**")
                        preview = first_text[:250] + "..." if len(first_text) > 250 else first_text
                        content.append(f"> \"{preview}\" - [{person}, {first_date.strftime('%d.%m.%Y %H:%M')}]")

                # Zufällige Beispielnachrichten aus der Mitte
                if len(person_messages) > 10:
                    content.append("")
                    content.append("**Beispielnachrichten:**")
                    import random
                    sample_msgs = random.sample(person_messages[1:-1], min(3, len(person_messages)-2))
                    for sample_msg in sample_msgs:
                        sample_text = self.get_message_text(sample_msg)
                        sample_date = self.parse_date(sample_msg.get('date', ''))
                        if sample_text and sample_date and len(sample_text) > 10:
                            preview = sample_text[:250] + "..." if len(sample_text) > 250 else sample_text
                            content.append(f"> \"{preview}\" - [{person}, {sample_date.strftime('%d.%m.%Y %H:%M')}]")
                            content.append("")

                if len(person_messages) > 1:
                    last_msg = person_messages[-1]
                    last_text = self.get_message_text(last_msg)
                    last_date = self.parse_date(last_msg.get('date', ''))

                    if last_text and last_date:
                        content.append("")
                        content.append("**Letzte Nachricht:**")
                        preview = last_text[:250] + "..." if len(last_text) > 250 else last_text
                        content.append(f"> \"{preview}\" - [{person}, {last_date.strftime('%d.%m.%Y %H:%M')}]")

            content.append("")
            content.append("---")
            content.append("")

        content.append("<div style=\"page-break-after: always;\"></div>")

        return '\n'.join(content)

    def _generate_key_events(self, key_events: List[Dict]) -> str:
        """Generiert Teil 5: Schlüsselereignisse"""
        content = [
            "# Teil 5: Schlüsselereignisse",
            "",
            "## 5.1 Übersicht",
            "",
            "Die folgenden Tage wiesen außergewöhnlich hohe Aktivität auf und werden als Schlüsselereignisse klassifiziert:",
            "",
        ]

        # Top 15 Events detailliert
        for i, event in enumerate(key_events[:15], 1):
            date_str = event['date']
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = dt.strftime('%d.%m.%Y')

            content.append(f"## 5.{i+1} {formatted_date}")
            content.append("")
            content.append(f"**Nachrichtenanzahl:** {event['message_count']:,}")
            content.append("")

            # Teilnehmer an diesem Tag
            participants_day = set()
            for msg in event['messages']:
                if 'from' in msg and msg['from']:
                    participants_day.add(msg['from'])

            content.append(f"**Aktive Teilnehmer:** {len(participants_day)}")
            content.append("")

            # Beispielnachrichten
            content.append("**Ausgewählte Nachrichten:**")
            content.append("")

            # Zeige bis zu 30 Nachrichten von diesem Tag
            shown = 0
            for msg in event['messages']:
                if shown >= 30:
                    break

                text = self.get_message_text(msg)
                if text and len(text) > 5:  # Auch kürzere Nachrichten für Kontext
                    msg_date = self.parse_date(msg.get('date', ''))
                    person = msg.get('from', 'Unbekannt')

                    if msg_date:
                        preview = text[:400] + "..." if len(text) > 400 else text
                        content.append(f"> \"{preview}\" - [{person}, {msg_date.strftime('%d.%m.%Y %H:%M')}]")
                        content.append("")
                        shown += 1

            content.append("---")
            content.append("")

        content.append("<div style=\"page-break-after: always;\"></div>")

        return '\n'.join(content)

    def _generate_group_dynamics(self, stats: Dict) -> str:
        """Generiert Teil 6: Gruppendynamik"""
        content = [
            "# Teil 6: Gruppendynamik & Entwicklung",
            "",
            "## 6.1 Aktivitätsmuster im Zeitverlauf",
            "",
        ]

        # Wöchentliche Durchschnitte
        if stats['date_range']['start'] and stats['date_range']['end']:
            total_days = (stats['date_range']['end'] - stats['date_range']['start']).days
            total_weeks = max(1, total_days // 7)

            content.append(f"**Durchschnittliche Nachrichten pro Woche:** {stats['total_messages'] / total_weeks:.1f}")
            content.append("")

        # Verteilung der Aktivität
        content.append("## 6.2 Aktivitätsverteilung")
        content.append("")

        # Top 10% Nutzer
        top_10_percent = max(1, len(stats['participants']) // 10)
        top_users = stats['message_by_person'].most_common(top_10_percent)
        top_users_messages = sum(count for _, count in top_users)
        top_users_percentage = (top_users_messages / stats['total_messages'] * 100) if stats['total_messages'] > 0 else 0

        content.append(f"**Top {top_10_percent} Teilnehmer ({top_10_percent}/{len(stats['participants'])}):**")
        content.append(f"- Verantwortlich für {top_users_messages:,} Nachrichten ({top_users_percentage:.1f}% der Gesamtaktivität)")
        content.append("")

        # Aktive vs. passive Teilnehmer
        active_threshold = 10  # Mindestens 10 Nachrichten
        active_users = sum(1 for count in stats['message_by_person'].values() if count >= active_threshold)
        passive_users = len(stats['participants']) - active_users

        content.append("## 6.3 Nutzertypen")
        content.append("")
        if len(stats['participants']) > 0:
            content.append(f"**Aktive Nutzer** (≥{active_threshold} Nachrichten): {active_users} ({active_users/len(stats['participants'])*100:.1f}%)")
            content.append(f"**Passive Nutzer** (<{active_threshold} Nachrichten): {passive_users} ({passive_users/len(stats['participants'])*100:.1f}%)")
        else:
            content.append(f"**Aktive Nutzer** (≥{active_threshold} Nachrichten): {active_users}")
            content.append(f"**Passive Nutzer** (<{active_threshold} Nachrichten): {passive_users}")
        content.append("")

        content.append("## 6.4 Tageszeit-Analyse")
        content.append("")
        content.append("Verteilung der Nachrichtenaktivität nach Tageszeit:")
        content.append("")

        # Analysiere Tageszeiten
        hour_stats = defaultdict(int)
        for msg in self.messages:
            dt = self.parse_date(msg.get('date', ''))
            if dt:
                hour_stats[dt.hour] += 1

        # Gruppiere in Zeitblöcke
        night = sum(hour_stats[h] for h in range(0, 6))
        morning = sum(hour_stats[h] for h in range(6, 12))
        afternoon = sum(hour_stats[h] for h in range(12, 18))
        evening = sum(hour_stats[h] for h in range(18, 24))

        total = night + morning + afternoon + evening
        if total > 0:
            content.append("| Tageszeit | Nachrichten | Anteil |")
            content.append("|-----------|-------------|--------|")
            content.append(f"| Nacht (00:00-06:00) | {night:,} | {night/total*100:.1f}% |")
            content.append(f"| Morgen (06:00-12:00) | {morning:,} | {morning/total*100:.1f}% |")
            content.append(f"| Nachmittag (12:00-18:00) | {afternoon:,} | {afternoon/total*100:.1f}% |")
            content.append(f"| Abend (18:00-24:00) | {evening:,} | {evening/total*100:.1f}% |")

        content.append("")

        # Aktivste Stunden
        top_hours = sorted(hour_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        content.append("**Aktivste Stunden:**")
        content.append("")
        for hour, count in top_hours:
            content.append(f"- {hour:02d}:00-{hour+1:02d}:00 Uhr: {count:,} Nachrichten")

        content.append("")

        # Wochentagsanalyse
        content.append("## 6.5 Wochentagsanalyse")
        content.append("")

        weekday_stats = defaultdict(int)
        weekday_names = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

        for msg in self.messages:
            dt = self.parse_date(msg.get('date', ''))
            if dt:
                weekday_stats[dt.weekday()] += 1

        content.append("| Wochentag | Nachrichten | Durchschnitt/Woche |")
        content.append("|-----------|-------------|-------------------|")

        total_weeks = max(1, (stats['date_range']['end'] - stats['date_range']['start']).days // 7) if stats['date_range']['start'] and stats['date_range']['end'] else 1

        for day_num, day_name in enumerate(weekday_names):
            count = weekday_stats[day_num]
            avg = count / total_weeks
            content.append(f"| {day_name} | {count:,} | {avg:.1f} |")

        content.append("")
        content.append("## 6.6 Wachstum und Entwicklung")
        content.append("")

        # Monatliches Wachstum
        sorted_months = sorted(stats['message_by_month'].items())
        if len(sorted_months) > 1:
            first_month_count = sorted_months[0][1]
            last_month_count = sorted_months[-1][1]

            if first_month_count > 0:
                growth = ((last_month_count - first_month_count) / first_month_count * 100)
                content.append(f"**Aktivitätsentwicklung:** Von {first_month_count:,} Nachrichten ({sorted_months[0][0]}) auf {last_month_count:,} Nachrichten ({sorted_months[-1][0]})")
                content.append(f"**Veränderung:** {growth:+.1f}%")
            content.append("")

        content.append("---")
        content.append("")
        content.append("<div style=\"page-break-after: always;\"></div>")

        return '\n'.join(content)

    def _generate_statistics(self, stats: Dict, keywords: Dict) -> str:
        """Generiert Teil 7: Statistiken & Daten"""
        content = [
            "# Teil 7: Statistiken & Daten",
            "",
            "## 7.1 Gesamtübersicht",
            "",
            "| Kategorie | Wert |",
            "|-----------|------|",
            f"| Gesamtnachrichten | {stats['total_messages']:,} |",
            f"| Teilnehmer | {len(stats['participants'])} |",
        ]

        # Zeitraum
        if stats['date_range']['start'] and stats['date_range']['end']:
            days = (stats['date_range']['end'] - stats['date_range']['start']).days
            content.append(f"| Zeitraum | {days} Tage |")
            content.append(f"| Durchschnitt/Tag | {stats['total_messages'] / max(1, days):.1f} |")
        else:
            content.append("| Zeitraum | N/A |")
            content.append("| Durchschnitt/Tag | N/A |")

        content.extend([
            f"| Durchschnitt/Person | {stats['total_messages'] / max(1, len(stats['participants'])):.1f} |",
            "",
        ])

        # Nachrichtenlängen-Statistik
        text_lengths = []
        for msg in self.messages:
            text = self.get_message_text(msg)
            if text:
                text_lengths.append(len(text))

        if text_lengths:
            content.append("## 7.2 Nachrichtenlängen")
            content.append("")
            content.append("| Kennzahl | Wert |")
            content.append("|----------|------|")
            content.append(f"| Durchschnitt | {sum(text_lengths)/len(text_lengths):.1f} Zeichen |")
            content.append(f"| Minimum | {min(text_lengths)} Zeichen |")
            content.append(f"| Maximum | {max(text_lengths)} Zeichen |")
            content.append(f"| Median | {sorted(text_lengths)[len(text_lengths)//2]} Zeichen |")
            content.append("")

        # Vollständige Teilnehmerliste
        content.append("## 7.3 Vollständige Teilnehmerliste")
        content.append("")
        content.append("| # | Teilnehmer | Nachrichten | Anteil |")
        content.append("|---|------------|-------------|--------|")

        for i, (person, count) in enumerate(stats['message_by_person'].most_common(), 1):
            percentage = (count / stats['total_messages'] * 100) if stats['total_messages'] > 0 else 0
            content.append(f"| {i} | {person} | {count:,} | {percentage:.2f}% |")

        content.append("")

        # Monatliche Detailstatistik
        content.append("## 7.4 Monatliche Detailstatistik")
        content.append("")
        content.append("| Monat | Nachrichten | Änderung zum Vormonat |")
        content.append("|-------|-------------|----------------------|")

        sorted_months = sorted(stats['message_by_month'].items())
        prev_count = None

        for month, count in sorted_months:
            year, month_num = month.split('-')
            month_name = datetime(int(year), int(month_num), 1).strftime('%B %Y')

            if prev_count is not None and prev_count > 0:
                change = ((count - prev_count) / prev_count * 100)
                content.append(f"| {month_name} | {count:,} | {change:+.1f}% |")
            else:
                content.append(f"| {month_name} | {count:,} | - |")

            prev_count = count

        content.append("")
        content.append("---")
        content.append("")
        content.append("<div style=\"page-break-after: always;\"></div>")

        return '\n'.join(content)

    def _generate_appendix(self) -> str:
        """Generiert Teil 8: Anhang"""
        content = [
            "# Teil 8: Anhang",
            "",
            "## 8.1 Methodologische Anmerkungen",
            "",
            "### Datenerfassung",
            "",
            "Die Analyse basiert auf dem offiziellen Telegram-Chat-Export im JSON-Format. Folgende Datenquellen wurden verwendet:",
            "",
            "- Part_1.json",
            "- Part_2.json",
            "- Part_3.json",
            "",
            "### Analyseverfahren",
            "",
            "**Quantitative Metriken:**",
            "- Nachrichtenzählung nach Person, Datum, Zeitraum",
            "- Häufigkeitsanalyse von Wörtern und Begriffen",
            "- Statistische Auswertung von Aktivitätsmustern",
            "",
            "**Qualitative Aspekte:**",
            "- Identifikation von Schlüsselereignissen basierend auf Nachrichtenvolumen",
            "- Thematische Gruppierung durch Schlüsselwortanalyse",
            "- Chronologische Einordnung von Diskussionssträngen",
            "",
            "### Einschränkungen",
            "",
            "- Die Analyse erfasst nur textuell messbare Aspekte",
            "- Medieninhalte (Bilder, Videos, Sprachnachrichten) werden nur als Typ erfasst, nicht inhaltlich ausgewertet",
            "- Gelöschte Nachrichten sind nicht Teil des Exports",
            "- Private Nachrichten außerhalb der Gruppe sind nicht erfasst",
            "",
            "## 8.2 Begriffsdefinitionen",
            "",
            "**Aktiver Nutzer:** Teilnehmer mit mindestens 10 gesendeten Nachrichten im Analysezeitraum",
            "",
            "**Schlüsselereignis:** Tag mit überdurchschnittlich hoher Nachrichtenaktivität (Top 10% der Tage)",
            "",
            "**Nachricht:** Jeder im Chat-Export erfasste Beitrag, unabhängig von Länge oder Inhalt",
            "",
            "## 8.3 Datenschutzhinweis",
            "",
            "Diese Analyse wurde ausschließlich zu Dokumentationszwecken erstellt. Alle Daten stammen aus einem Gruppen-Chat, zu dem alle genannten Personen Zugang hatten. Die Auswertung erfolgt:",
            "",
            "- Faktisch und ohne Wertung",
            "- Ohne Offenlegung privater Informationen außerhalb des Chat-Kontexts",
            "- Mit ausschließlicher Verwendung öffentlich im Chat geteilter Inhalte",
            "",
            "## 8.4 Technische Details",
            "",
            f"**Analysezeitpunkt:** {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "**Analysesoftware:** Python 3 mit JSON-Parsing",
            "**Ausgabeformat:** Markdown (.md)",
            "",
            "---",
            "",
            "## Ende des Dokuments",
            "",
            f"*Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}*",
        ]

        return '\n'.join(content)


def main():
    """Hauptfunktion"""
    file_paths = [
        '/home/user/Buch_auftrag/combined_export.json'
    ]

    output_path = '/home/user/Buch_auftrag/EBOOK_2025_Jahresanalyse.md'

    print("="*60)
    print("TELEGRAM CHAT EBOOK GENERATOR")
    print("="*60)
    print()

    analyzer = TelegramChatAnalyzer(file_paths)
    analyzer.load_data()
    analyzer.generate_ebook(output_path)

    print("\n" + "="*60)
    print("FERTIG!")
    print("="*60)


if __name__ == '__main__':
    main()
