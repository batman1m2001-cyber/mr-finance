"""The signed inbox (BRD-RULE-ZONE-02/03, LC-04, SEC-07, FR-307 inbox mode; BRD completion F6, F-D7).

The AI zone (``zone/``, another process with its own database) writes result packages here and reads nothing
back. Every 10 minutes the ``inbox_import`` job takes each READY package through the same checks a live run
passes and either imports it — an event, a view waiting for the CIO, the challenge and the run's trace — or
rejects it with the error, changing nothing.
"""
