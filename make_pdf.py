import os
from fpdf import FPDF

class EnvironmentPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'OpenEnv Solution Architecture (SentinelSOC)', 0, 0, 'C')
        self.ln(20)

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, label, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 8, body)
        self.ln()

def generate_doc():
    pdf = EnvironmentPDF()
    pdf.add_page()

    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'SentinelSOC: Autonomous Cyber-Defense Console', 0, 1, 'C')
    pdf.ln(10)

    pdf.chapter_title('1. Project Overview')
    overview = (
        "This project is 'SentinelSOC', an elite reinforcement learning (RL) "
        "environment for autonomous cyber-security incident response. It is built on "
        "the Meta PyTorch OpenEnv framework. It simulates a SOC Command Center where an "
        "AI analyst (SentinelAI) must autonomously triage incoming high-stakes security incidents, "
        "search a Threat Intelligence playbooks database, update incident parameters (severity, unit), "
        "and draft executive reports for the CISO."
    )
    pdf.chapter_body(overview)

    pdf.chapter_title('2. Key Agentic Capabilities')
    capabilities = (
        "- Investigate: Search and analyze threat intelligence logs and playbooks.\n"
        "- Mitigate: Route incidents to units (security, network, hr) and update severity levels.\n"
        "- Report: Autonomously draft technical incident summaries.\n"
        "- Submit: Close and finalize missions after neutralization."
    )
    pdf.chapter_body(capabilities)

    pdf.chapter_title('3. Reward Function Design')
    reward_logic = (
        "The environment uses a potential-based reward function (Phi). It computes the 'delta' "
        "between the current state and a perfect solution. Rewards are scaled strictly within (0.01, 0.99) "
        "to comply with Phase 2 OpenEnv requirements. Each tactical cycle costs 0.005, forcing "
        "the agent to prioritize speed and precision over brute-force exploration."
    )
    pdf.chapter_body(reward_logic)

    pdf.chapter_title('4. Codebase Architecture')
    body_text = (
        "1. models.py:\n"
        "Defines strict Pydantic schemas (SentinelAction, SentinelObservation). "
        "This provides the 'Uplink Contract' for the agent communication.\n\n"
        "2. server/sentinel_env.py:\n"
        "The core tactical engine. It inherits from OpenEnv's Environment interface. It manages state transitions, "
        "MITRE ATT&CK tactics mapping, and reward evaluation.\n\n"
        "3. server/app.py:\n"
        "The Command Center UI. A Gradio dashboard showcasing tactical threat maps, integrity health, and agent reasoning.\n\n"
        "4. inference.py:\n"
        "The Autonomous SOC Analyst agent logic using large language models (LLMs)."
    )
    pdf.chapter_body(body_text)

    # Save to file
    out_path = "architecture_overview.pdf"
    pdf.output(out_path)
    print(f"Documentation generated: {out_path}")

if __name__ == "__main__":
    generate_doc()
