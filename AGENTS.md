# Projektregeln

## agent-lessons

Dieses Projekt führt seine Tickets mit agent-lessons. Board, Rollen, Regeln und
Lessons liest und schreibst du über den MCP-Server `agent-lessons`, nicht von Hand
in `_tickets/`.

- **Zuerst `next`:** In jedem Durchlauf sagt `next`, was deine Rolle jetzt tut.
- **Stand:** `get_status`, die Spalten mit `get_tickets`, ein Ticket mit `get_ticket`.
- **Regeln und Lessons:** `get_config` nennt Regeln und Guards mit Summary
  (Volltext mit `get_rule`, `get_guard`), `get_lessons` die Lessons.
- **Rollen:** Eine Sitzung mit Rolle startet der Mensch mit `al start ROLLE`
  (implementer, reviewer, observer). Ohne Rolle arbeitest du nur auf ausdrücklichen
  Auftrag.
- **Fragen und Notizen an den Menschen:** `ask_user` bzw. `add_note`, nicht im
  eigenen Gedächtnis.
