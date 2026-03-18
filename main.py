# main.py
from src.agents.supervisor import SamuraiSupervisor
from rich.console import Console
from rich.panel import Panel

console = Console()


def start_mission():
    boss = SamuraiSupervisor()

    console.print(
        Panel.fit(
            "[bold cyan]AMPTUDIX RESEARCH SUITE v1.0[/bold cyan]\n"
            "[italic]Ready for your command, My Lord.[/italic]",
            border_style="cyan",
        )
    )

    while True:
        try:
            user_input = console.input("\n[bold green]Command > [/bold green]")
            if user_input.lower() in ["exit", "quit", "q"]:
                break

            # The Supervisor takes control of the whole team here
            boss.run(user_input)

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    start_mission()
