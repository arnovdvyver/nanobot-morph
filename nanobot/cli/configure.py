"""Interactive CLI wizard for configuring nanobot's soul, behavior, and model settings."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from nanobot import __logo__
from nanobot.config.loader import load_config, save_config
from nanobot.config.schema import Config

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ask(prompt: str, default: str = "") -> str:
    """Prompt the user for input with an optional default."""
    return typer.prompt(prompt, default=default, show_default=bool(default))


def _ask_optional(prompt: str, hint: str = "") -> str:
    """Prompt the user for optional input (empty string accepted)."""
    suffix = f" ({hint})" if hint else ""
    result = typer.prompt(f"{prompt}{suffix}", default="", show_default=False)
    return result.strip()


def _choose(prompt: str, options: list[str], default: int = 1) -> str:
    """Present numbered choices and return the selected option."""
    console.print(f"\n[bold]{prompt}[/bold]")
    for i, opt in enumerate(options, 1):
        marker = "[cyan]>[/cyan] " if i == default else "  "
        console.print(f"  {marker}{i}. {opt}")

    while True:
        raw = typer.prompt("Choice", default=str(default))
        try:
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        except ValueError:
            pass
        console.print(f"[red]Please enter a number between 1 and {len(options)}[/red]")


def _ask_list(prompt: str, defaults: list[str] | None = None) -> list[str]:
    """Prompt for a comma-separated list of items."""
    default_str = ", ".join(defaults) if defaults else ""
    raw = _ask(prompt + " (comma-separated)", default=default_str)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _section(title: str) -> None:
    """Print a section header."""
    console.print()
    console.print(Panel(Text(title, style="bold cyan"), expand=False))


# ---------------------------------------------------------------------------
# Section: Model settings
# ---------------------------------------------------------------------------


def _configure_model(config: Config) -> Config:
    """Walk through model and agent parameter configuration."""
    _section("Model Settings")

    defaults = config.agents.defaults

    console.print(f"  Current model: [cyan]{defaults.model}[/cyan]")
    console.print("  [dim]Examples: anthropic/claude-sonnet-4-20250514, openrouter/google/gemini-2.5-pro,")
    console.print("  deepseek/deepseek-chat, openai/gpt-4o, gemini/gemini-2.5-flash[/dim]\n")

    model = _ask("Model identifier", default=defaults.model)

    temp_str = _ask("Temperature (0.0-2.0, higher = more creative)", default=str(defaults.temperature))
    try:
        temperature = float(temp_str)
        temperature = max(0.0, min(2.0, temperature))
    except ValueError:
        temperature = defaults.temperature

    max_tokens_str = _ask("Max tokens per response", default=str(defaults.max_tokens))
    try:
        max_tokens = int(max_tokens_str)
    except ValueError:
        max_tokens = defaults.max_tokens

    max_iter_str = _ask("Max tool iterations", default=str(defaults.max_tool_iterations))
    try:
        max_tool_iterations = int(max_iter_str)
    except ValueError:
        max_tool_iterations = defaults.max_tool_iterations

    mem_str = _ask("Memory window (messages in context)", default=str(defaults.memory_window))
    try:
        memory_window = int(mem_str)
    except ValueError:
        memory_window = defaults.memory_window

    config.agents.defaults.model = model
    config.agents.defaults.temperature = temperature
    config.agents.defaults.max_tokens = max_tokens
    config.agents.defaults.max_tool_iterations = max_tool_iterations
    config.agents.defaults.memory_window = memory_window

    return config


# ---------------------------------------------------------------------------
# Section: Soul
# ---------------------------------------------------------------------------

_DEFAULT_PERSONALITY = [
    "Helpful and friendly",
    "Concise and to the point",
    "Curious and eager to learn",
]
_DEFAULT_VALUES = [
    "Accuracy over speed",
    "User privacy and safety",
    "Transparency in actions",
]
_DEFAULT_COMM_STYLE = [
    "Be clear and direct",
    "Explain reasoning when helpful",
    "Ask clarifying questions when needed",
]


def _configure_soul(workspace: Path) -> None:
    """Walk through soul/personality configuration and write SOUL.md."""
    _section("Soul & Personality")

    # Read existing soul if present
    soul_path = workspace / "SOUL.md"
    existing_name = "nanobot"
    existing_personality = _DEFAULT_PERSONALITY
    existing_values = _DEFAULT_VALUES
    existing_style = _DEFAULT_COMM_STYLE

    if soul_path.exists():
        content = soul_path.read_text()
        # Try to extract existing name from "I am <name>"
        for line in content.splitlines():
            if line.strip().lower().startswith("i am"):
                parts = line.strip().split("I am", 1)
                if len(parts) == 2:
                    name = parts[1].strip().rstrip(".,!").split(",")[0].strip()
                    if name:
                        existing_name = name
                break

    bot_name = _ask("Bot name", default=existing_name)
    personality = _ask_list("Personality traits", defaults=existing_personality)
    values = _ask_list("Core values", defaults=existing_values)
    comm_style = _ask_list("Communication style guidelines", defaults=existing_style)

    # Build SOUL.md
    lines = [
        "# Soul",
        "",
        f"I am {bot_name}, a personal AI assistant.",
        "",
        "## Personality",
        "",
    ]
    for trait in personality:
        lines.append(f"- {trait}")

    lines += ["", "## Values", ""]
    for val in values:
        lines.append(f"- {val}")

    lines += ["", "## Communication Style", ""]
    for style in comm_style:
        lines.append(f"- {style}")

    lines.append("")
    soul_path.write_text("\n".join(lines))
    console.print(f"  [green]\u2713[/green] Saved [cyan]SOUL.md[/cyan]")


# ---------------------------------------------------------------------------
# Section: User profile
# ---------------------------------------------------------------------------


def _configure_user(workspace: Path) -> None:
    """Walk through user profile configuration and write USER.md."""
    _section("User Profile")

    name = _ask_optional("Your name", hint="press Enter to skip")
    timezone = _ask_optional("Your timezone", hint="e.g. UTC+8, America/New_York")
    language = _ask("Preferred language", default="English")

    comm_pref = _choose(
        "Communication style preference?",
        ["Casual", "Professional", "Technical"],
        default=1,
    )

    response_len = _choose(
        "Preferred response length?",
        ["Brief and concise", "Detailed explanations", "Adaptive based on question"],
        default=3,
    )

    tech_level = _choose(
        "Technical level?",
        ["Beginner", "Intermediate", "Expert"],
        default=2,
    )

    role = _ask_optional("Primary role", hint="e.g. developer, researcher, student")
    projects = _ask_optional("Main projects you're working on")
    tools = _ask_optional("Tools you use", hint="e.g. VS Code, Python, React")
    interests = _ask_optional("Topics of interest", hint="comma-separated")
    special = _ask_optional("Special instructions for the bot")

    # Build USER.md
    lines = [
        "# User Profile",
        "",
        "Information about the user to help personalize interactions.",
        "",
        "## Basic Information",
        "",
        f"- **Name**: {name or '(not set)'}",
        f"- **Timezone**: {timezone or '(not set)'}",
        f"- **Language**: {language}",
        "",
        "## Preferences",
        "",
        f"- **Communication Style**: {comm_pref}",
        f"- **Response Length**: {response_len}",
        f"- **Technical Level**: {tech_level}",
        "",
        "## Work Context",
        "",
        f"- **Primary Role**: {role or '(not set)'}",
        f"- **Main Projects**: {projects or '(not set)'}",
        f"- **Tools You Use**: {tools or '(not set)'}",
        "",
    ]

    if interests:
        lines += ["## Topics of Interest", ""]
        for topic in [t.strip() for t in interests.split(",") if t.strip()]:
            lines.append(f"- {topic}")
        lines.append("")

    if special:
        lines += ["## Special Instructions", "", special, ""]

    user_path = workspace / "USER.md"
    user_path.write_text("\n".join(lines))
    console.print(f"  [green]\u2713[/green] Saved [cyan]USER.md[/cyan]")


# ---------------------------------------------------------------------------
# Section: Agent behavior
# ---------------------------------------------------------------------------

_DEFAULT_GUIDELINES = [
    "Always explain what you're doing before taking actions",
    "Ask for clarification when the request is ambiguous",
    "Use tools to help accomplish tasks",
    "Remember important information in memory files",
]


def _configure_agent(workspace: Path) -> None:
    """Walk through agent behavior configuration and write AGENTS.md."""
    _section("Agent Behavior")

    console.print("  Define how your agent should behave.\n")

    agent_desc = _ask(
        "Short agent description",
        default="You are a helpful AI assistant. Be concise, accurate, and friendly.",
    )

    guidelines = _ask_list("Agent guidelines", defaults=_DEFAULT_GUIDELINES)

    # Build AGENTS.md - preserve the tool/memory/heartbeat reference sections
    lines = [
        "# Agent Instructions",
        "",
        agent_desc,
        "",
        "## Guidelines",
        "",
    ]
    for g in guidelines:
        lines.append(f"- {g}")

    lines += [
        "",
        "## Tools Available",
        "",
        "You have access to:",
        "- File operations (read, write, edit, list)",
        "- Shell commands (exec)",
        "- Web access (search, fetch)",
        "- Messaging (message)",
        "- Background tasks (spawn)",
        "",
        "## Memory",
        "",
        "- `memory/MEMORY.md` \u2014 long-term facts (preferences, context, relationships)",
        "- `memory/HISTORY.md` \u2014 append-only event log, search with grep to recall past events",
        "",
        "## Scheduled Reminders",
        "",
        "When user asks for a reminder at a specific time, use `exec` to run:",
        "```",
        'nanobot cron add --name "reminder" --message "Your message" --at "YYYY-MM-DDTHH:MM:SS" --deliver --to "USER_ID" --channel "CHANNEL"',
        "```",
        "Get USER_ID and CHANNEL from the current session.",
        "",
        "**Do NOT just write reminders to MEMORY.md** \u2014 that won't trigger actual notifications.",
        "",
        "## Heartbeat Tasks",
        "",
        "`HEARTBEAT.md` is checked every 30 minutes. Manage periodic tasks by editing this file.",
        "",
    ]

    agents_path = workspace / "AGENTS.md"
    agents_path.write_text("\n".join(lines))
    console.print(f"  [green]\u2713[/green] Saved [cyan]AGENTS.md[/cyan]")


# ---------------------------------------------------------------------------
# Main wizard entry point
# ---------------------------------------------------------------------------


def run_configure_wizard() -> None:
    """Run the full interactive configuration wizard."""
    console.print(
        Panel(
            f"{__logo__} [bold]nanobot Configuration Wizard[/bold]\n\n"
            "Configure your nanobot's model, personality, and behavior\n"
            "through an interactive guided setup.\n\n"
            "[dim]Press Enter to accept defaults shown in brackets.[/dim]",
            expand=False,
        )
    )

    config = load_config()
    workspace = config.workspace_path
    workspace.mkdir(parents=True, exist_ok=True)

    # Ask which sections to configure
    console.print()
    console.print("[bold]Which sections would you like to configure?[/bold]")
    console.print("  1. Everything (full setup)")
    console.print("  2. Model settings only")
    console.print("  3. Soul & personality only")
    console.print("  4. User profile only")
    console.print("  5. Agent behavior only")

    while True:
        raw = typer.prompt("Choice", default="1")
        try:
            choice = int(raw)
            if 1 <= choice <= 5:
                break
        except ValueError:
            pass
        console.print("[red]Please enter a number between 1 and 5[/red]")

    if choice in (1, 2):
        config = _configure_model(config)
        save_config(config)
        console.print(f"  [green]\u2713[/green] Saved model settings to [cyan]~/.nanobot/config.json[/cyan]")

    if choice in (1, 3):
        _configure_soul(workspace)

    if choice in (1, 4):
        _configure_user(workspace)

    if choice in (1, 5):
        _configure_agent(workspace)

    # Summary
    console.print()
    console.print(Panel(
        f"[green bold]\u2713 Configuration complete![/green bold]\n\n"
        f"  Config:    [cyan]~/.nanobot/config.json[/cyan]\n"
        f"  Workspace: [cyan]{workspace}[/cyan]\n\n"
        f"  Start chatting: [bold]nanobot agent[/bold]",
        title=f"{__logo__} Done",
        expand=False,
    ))
