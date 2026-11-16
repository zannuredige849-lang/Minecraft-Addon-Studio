# Teaching mode

Turn on: "teaching mode", "teach me", or "explain every step".
Turn off: "development mode".

In teaching mode the studio:
1. States the goal and the agent responsible.
2. Shows the architecture involved (which folders, which references).
3. Shows each file it creates or changes, with a one-line reason.
4. Explains each decision: why a UUID is fresh, why a format version was chosen, why a box UV fits, why a rule is an error and not a warning.
5. Shows the check that proves the change works, and what it does not prove.
6. Ends with "what to try next" for the user.

Teaching mode does not change what gets built. Quality gates are the same in both modes.
