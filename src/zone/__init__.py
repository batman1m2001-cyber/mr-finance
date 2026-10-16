"""The AI zone (BRD §5, ZONE-01…06; F-D7): a second process (app/zone.py, ``MF_ZONE=on``) with its own SQLite file.
It holds public news it fetches itself, the research TCB released and the catalogues TCB approved — never a customer
or a member of staff. TCB pushes it those (``sync``, received by ``mirror``); it runs the CIO agent on its own news
(``agent``) and pushes each result to TCB's write-only inbox, signed, reading nothing back."""
