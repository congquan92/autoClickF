# Audit fixes

The user requested implementation of all ten findings in the repository audit.
Keep the existing Windows GUI/CLI and dependencies. Fix the current code rather
than replacing its architecture. Work on `codex/audit-fixes`; leave the user's
existing skills changes untouched. No commit or publication is required.

## Approach

Validate the game by its executable (`GenshinImpact.exe` / `YuanShen.exe`),
using a process handle with limited query access; deny input if identity cannot
be checked. Recheck foreground HWND and run/stop state before each input.
Always release a pressed key/button. Preserve client origin with manual sizes.
Use one targeted click for a detected answer, preferring the lowest matching row.
F12 closes the GUI through its existing queue and cannot be rebound.

Validate config both when loading and before saving. Invalid saved settings fall
back with warnings; invalid UI changes are rejected without changing the active
config. Start/pause must differ and cannot use confirm, Space (narrative input),
or F12. Burst accepts 1..5, including 1 in Extreme. Dimensions must be positive.
Keep config writes serialized and replace the file only after a complete write.

Use standard-library unittest with OS input mocked, temporary config files and
pixel fixtures. Do not send real input or start global hooks in tests. Remove
unused code and tracked bytecode; document the fixes and test command.

## Boundaries

Executable identity and foreground checks reduce unintended input; switching
focus between the last check and an OS input call cannot be made atomic here.
Pixel accuracy, game acceptance of injected input, and practical CPS still need
manual testing inside the game.
