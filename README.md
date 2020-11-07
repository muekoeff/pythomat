Pythomat
========

Pythomat ist der ideale Helfer für (faule) Studenten. Wer die Flut an Skript-Versionen, Übungsblättern und Vorlesungsmitschnitten kennt, weiß, wie nervig es sein kann, seine digitale Kopie davon immer auf dem neusten Stand zu halten, sodass er auch in Bus, Bahn oder dem Saarland darauf zugreifen kann, ohne sich mit langsamen Mobilverbindungen herum zu schlagen.

Die Dateien als geteilten Ordner in der [Nextcloud-Instanz der Fachrichtung](https://oc.cs.uni-saarland.de/) zur Verfügung zu stellen ist ja anscheinend leider zu krasse Computermagie.

Der Pythomat ist leicht erweiterbar, klein und (relativ) schnell installiert. Er ist in Python geschrieben, weil Cehmat, Javamat oder Essemelmat einfach dumm klingt. Und, weil Python plattformunabhängig ist. Und, weil der Autor es noch nicht konnte, als er das Skript begonnen hat.

# Voraussetzungen
Python 3, sowie das Paket Mechanize, und bei Verwendung des Moduls [*cms*](#cms-1) bzw. [*moodle*](#moodle-1) BeautifulSoup4 und Keyring, werden benötigt.

# Installation
- [Python 3](https://python.org/) installieren.
- [pip](https://pip.pypa.io/en/stable/installing/) installieren. Dies dient zum einfachen Installieren der Abhängigkeiten.
- In der Konsole `git clone https://github.com/muekoeff/pythomat.git && cd pythomat` eingeben; oder dieses Repo [herunterladen](https://github.com/muekoeff/pythomat/archive/master.zip) und in ein Verzeichnis entpacken.
- Um serverseitige Änderungen an der *pythomat.ini* zu ignorieren, empfiehlt es sich, diese Datei von Git ignorieren zu lassen. Dies ist beispielsweise durch Ausführen des Befehls `echo "pythomat.ini" >> "$(git rev-parse --show-toplevel)/.git/info/exclude"` im lokalen Git-Repository-Verzeichnis möglich.
- Mit `pip3 install .` Abhängigkeiten installieren. Dies ist auch manuell möglich, siehe den [folgenden Abschnitt](#manuelle-installation).
- Sollte der Modus [*youtube*](#youtube) genutzt werden:
  - [*youtube-dl*](https://ytdl-org.github.io/youtube-dl/) über den Paketmanager installieren.
  - Oder *youtube-dl* herunterladen, dann die heruntergeladene Datei ins erstellte Verzeichnis verschieben.

## Manuelle Installation
- In der Konsole `pip3 install mechanize` eingeben.
- Sollte das Modul [*cms*](#cms-1) bzw. [*moodle*](#moodle-1) genutzt werden:
  - In der Konsole `pip3 install beautifulsoup4 keyring --upgrade keyrings.alt` eingeben.

## Updaten
Zum Updaten kann Git verwendet werden. Einen automatisierten Mechanismus zum Updaten oder Überprüfen auf Updates gibt es nicht. Bei Bedarf kann das Projekt auf GitHub beobachtet werden.
- Ins Pythomat-Verzeichnis wechseln.
- Sicherstellen, dass mittels `echo "pythomat.ini" >> "$(git rev-parse --show-toplevel)/.git/info/exclude"` die *pythomat.ini* von Updates ausgeschlossen wird (Nicht notwendig, falls diese unverändert ist).
- `git pull`

# Ausführung
- Im Terminal `python3 pythomat.py` eintippen und <kbd>Enter</kbd> drücken.
- Optional kann als Argument eine alternative \*.ini-Datei übergeben werden. Standardmäßig wird die *pythomat.ini* im Arbeitsverzeichnis eingelesen.

## Argumente
| Parameter			| Beschreibung |
| -----------------	| ------------ |
| `--createdirs`	| Legt automatisch fehlende Verzeichnisse an, in die heruntergeladen werden soll. |
| `-h`, `--help`	| Zeigt eine Liste aller unterstützten Argumente an. |
| `-l`, `--list`	| Zeigt eine Liste aller vom Benutzer definierten Regeln an. |
| `--log <Pfad>`	| Speichert eine Historie heruntergeladener Dateien im spezifizierten Pfad ab. |
| `-r`, `--rules`	| Führt nur die mit Komma getrennt aufgezählten Regeln aus. Nicht aufgezählte Regeln werden ausgelassen. Mit dem Wert `all` werden alle Regeln ausgeführt, auch solche die normalerweise mit `skip` ausgelassen werden. |
| `--version`		| Zeigt einen Link zum GitHub-Repository an. |

# Konfiguration
Pythomat benutzt die Standard-Bibliothek ConfigParser zum Parsen von ini-Dateien. Standardmäßig wird *pythomat.ini* verwendet.

Hier eine Beispieldatei, die ein einzelnes Skript herunterlädt. Der Name des Abschnitts, angegeben in einer separaten Zeile in eckigen Klammern, kann frei gewählt werden.

	[VorlesungsSkript]
	mode = single
	uri = http://www.vorlesung.de/skript.pdf
	saveto = /irgendein/Pfad/

## Modi
Mit dem Parameter `mode` kann zwischen den zur Verfügung stehenden Modi gewechselt werden. Folgende Modi stehen zur Verfügung: [`batch`](#batch), [`cms`](#cms), [`module`](#module), [`moodle`](#moodle), [`single`](#single), [`youtube`](#youtube)

### `batch`
Durchsucht eine Seite nach Links und lädt alle diese Dateien herunter.

#### Parameter
| Parameter		| Beschreibung |
| ---------		| ------------ |
| `uri`			| URL, die nach Links durchsucht werden soll. |
| `saveto`		| Verzeichnis, in welches die Dateien heruntergeladen werden sollen. |
| `pattern`		| Regulärer Ausdruck, den der Link erfüllen muss, damit er heruntergeladen wird. |
| `username`	| *optional:* Benutzername für HTTP-Authentifizierung. Nur zusammen mit `password` zu verwenden. |
| `password`	| *optional:* Kennwort für HTTP-Authentifizierung. Nur zusammen mit `username` zu verwenden. |
| `overwrite`	| *optional:* Ob eine bereits existierende Datei unter dem gleichen Pfad überschrieben werden darf. 1 entspricht ja, 0 entspricht nein. Falls nicht angegeben, 1. |
| `skip`		| *optional:* Wenn auf 1 gesetzt, wird diese Regel ausschließlich dann ausgeführt, wenn sie im `--rules`-Argument aufgelistet ist. |

### `cms`
Kurzform für einen Modulaufruf mit *cms* als Modul. Siehe [entsprechenden Abschnitt](#cms-1).

### `moodle`
Kurzform für einen Modulaufruf mit *moodle* als Modul. Siehe [entsprechenden Abschnitt](#moodle-1).

### `module`
Lädt `<module>.py` und führt `<module>.start(section, items, pythomat)` aus. `section` ist dabei der Name der aktuellen Konfiguration als String, `items` ein Dictionary, welches die Einstellungen enthält, und `pythomat` eine Referenz auf das `Pythomat`-Objekt.
Über die `pythomat`-Referenz sollte `reportFailed(section, filename)` und `reportFinished(section, filename)` aufgerufen werden, um im abschließenden Report aufgelistet zu werden. ([Auflistung der Module](#module-1))

#### Parameter
| Parameter	| Beschreibung |
| ---------	| ------------ |
| `module`	| Name des zu ladenden Moduls. (entspricht Dateinamen ohne `.py`-Dateiendung) |
| `skip`	| *optional:* Wenn auf 1 gesetzt, wird diese Regel ausschließlich dann ausgeführt, wenn sie im `--rules`-Argument aufgelistet ist. |
| *Abhängig von Modul*	| Module können weitere Parameter einführen.

### `single`
Lädt eine einzelne Datei herunter, falls sie auf dem Server geändert wurde.

| Parameter		| Beschreibung |
| ---------		| ------------ |
| `uri`			| URL der zu herunterzuladenden Datei. |
| `saveto`		| Verzeichnis, in welches die Datei heruntergeladen werden soll. |
| `filename`	| *optional:* Dateiname für die heruntergeladene Datei. Falls nicht angegeben, wird der Dateiname aus `uri` entnommen. |
| `username`	| *optional:* Benutzername für HTTP-Authentifizierung. Nur zusammen mit `password` zu verwenden. |
| `password`	| *optional:* Kennwort für HTTP-Authentifizierung. Nur zusammen mit `username` zu verwenden. |
| `overwrite`	| *optional:* Ob eine bereits existierende Datei unter dem gleichen Pfad überschrieben werden darf. 1 entspricht ja, 0 entspricht nein. Falls nicht angegeben, 1. |
| `skip`		| *optional:* Wenn auf 1 gesetzt, wird diese Regel ausschließlich dann ausgeführt, wenn sie im `--rules`-Argument aufgelistet ist. |

### `youtube`
**Legacy.** Lädt ein einzelnes YouTube-Video der gegebenen id herunter.

| Parameter		| Beschreibung |
| ---------		| ------------ |
| `uri`			|  |
| `saveto`		|  |
| `overwrite`	| *optional:* Ob eine bereits existierende Datei unter dem gleichen Pfad überschrieben werden darf. 1 entspricht ja, 0 entspricht nein. Falls nicht angegeben, 1. |

## Module
Module werden mit dem Modus `mode = module` verwendet. Dazu muss in `module` der Name des zu ladenden Modus eingetragen werden. Weitere Module lassen sich schnell selbst erstellen. Folgendes Modul stehen zur Verfügung: [`cms`](#cms-1), [`moodle`](#moodle-1).

### `cms`
Unterstützung für CakeCMS-Materialseiten.

| Parameter		| Beschreibung |
| ---------		| ------------ |
| `uri`			| URL der Hauptseite des CMS. |
| `saveto`		| Verzeichnis, in welches die Dateien heruntergeladen werden sollen. |
| `username`	| Benutzername im CMS. |
| `password`	| *alternativ zu `keyring_id`* <br> Kennwort zum in `username` angegebenen Benutzer in Klartext. |
| `keyring_id`	| *alternativ zu `password`* <br> Kennung, welche zum Service `pythomat.<keyring_id>` zusammengesetzt wird. |Sollte unter der Kennung kein Kennwort im System-Keyring vorhanden sein, so wird der Benutzer dazu aufgefordert eins einzugeben. Dieses wird im Keyring abgespeichert. |
| `fileext_whitelist`	| *optional:* Mit Leerzeichen getrennte Auflistung an Dateiendungen, die heruntergeladen werden sollen. |
| `fileext_blacklist`	| *optional:* Mit Leerzeichen getrennte Auflistung an Dateiendungen, die nicht heruntergeladen werden sollen. |
| `overwrite`	| *optional:* Ob eine bereits existierende Datei unter dem gleichen Pfad überschrieben werden darf. 1 entspricht ja, 0 entspricht nein. Falls nicht angegeben, 0. |

### `moodle`
Unterstützung für Moodle-Instanzen.

| Parameter		| Beschreibung |
| ---------		| ------------ |
| `uri`			| URL der Hauptseite der Veranstaltung auf Moodle. |
| `saveto`		| Verzeichnis, in welches die Dateien heruntergeladen werden sollen. |
| `username`	| Benutzername in der Moodle-Instanz. |
| `password`	| *alternativ zu `keyring_id`* <br> Kennwort zum in `username` angegebenen Benutzer in Klartext. |
| `keyring_id`	| *alternativ zu `password`* <br> Kennung, welche zum Service `pythomat.<keyring_id>` zusammengesetzt wird. |Sollte unter der Kennung kein Kennwort im System-Keyring vorhanden sein, so wird der Benutzer dazu aufgefordert eins einzugeben. Dieses wird im Keyring abgespeichert. |
| `fileext_whitelist`	| Mit Leerzeichen getrennte Auflistung an Dateiendungen, die heruntergeladen werden sollen. Für mp4 ist zu beachten, dass `mpeg mp4` in die Auflistung aufgenommen werden muss. |
| `overwrite`	| *optional:* Ob eine bereits existierende Datei unter dem gleichen Pfad überschrieben werden darf. 1 entspricht ja, 0 entspricht nein. Falls nicht angegeben, 0. |
