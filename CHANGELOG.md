# Changelog

## [4.0] - 2026-04-23

Part of **Lince Investor Suite v4.0** coordinated release.

### Changed
- Depends on `lynx-investor-core>=4.0` and uses its new URL-safety
  helpers for every RSS-sourced URL.

All notable changes to **Lynx Fundamental Analysis** are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0] - 2026-04-22

Part of **Lince Investor Suite v3.0** coordinated release.

### Added
- Uniform PageUp / PageDown navigation across every UI mode (GUI, TUI,
  interactive, console). Scrolling never goes above the current output
  in interactive and console mode; Shift+PageUp / Shift+PageDown remain
  reserved for the terminal emulator's own scrollback.

### Changed
- TUI wires `lynx_investor_core.pager.PagingAppMixin` and
  `tui_paging_bindings()` into the main application.
- Graphical mode binds `<Prior>` / `<Next>` / `<Control-Home>` /
  `<Control-End>` via `bind_tk_paging()`.
- Interactive mode pages long output through `console_pager()` /
  `paged_print()`.
- New dependency on `lynx-investor-core>=2.0` for the shared pager module.

---

## [v2.0] — 2026-04-19

Major release — **Lince Investor Suite v2.0** unified release.

### Changed
- **Unified suite**: All Lince Investor projects now share consistent
  version numbering, logos, keybindings, CLI patterns, export styling,
  installation instructions, and documentation structure.
- **Documentation**: Standardized installation section with clone + pip
  install steps and dependency table matching other suite projects.

---

## [v1.0] — 2026-04-15

First production-stable major release.

- Full fundamental analysis for value investing
- 40+ financial metrics across 7 sections
- Tier-aware analysis (Mega/Large/Mid/Small/Micro/Nano Cap)
- Traditional moat detection + survival analysis for micro caps
- Five intrinsic value methods (DCF, Graham, NCAV, Lynch, Asset-Based)
- SEC filing download + news aggregation
- Four interfaces: CLI, Interactive, TUI, GUI
- Export formats: TXT, HTML, PDF
- BSD 3-Clause License
