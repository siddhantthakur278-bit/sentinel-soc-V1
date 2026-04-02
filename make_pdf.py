from fpdf import FPDF
class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'Support Ticket Triage - AI Environment Documentation', border=False, ln=True, align='C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')
    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, border=False, ln=True, fill=True)
        self.ln(4)
    def chapter_body(self, body):
        self.set_font('Helvetica', '', 11)
        self.multi_cell(0, 7, body)
        self.ln()
def create_pdf():
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title('1. What is this Project?')
    pdf.chapter_body(
        "This project is 'Support Ticket Triage', an advanced reinforcement learning (RL) "
        "environment built on top of the Meta PyTorch OpenEnv framework. It simulates a "
        "Helpdesk or IT Level-1 Support workflow where an AI agent must autonomously "
        "interact with incoming customer complaints, search a corporate Knowledge Base (KB), "
        "assign appropriate routing parameters (like 'priority' and 'team'), and correctly "
        "draft resolution messages."
    )
    pdf.chapter_title('2. What Technologies Does It Use?')
    pdf.chapter_body(
        "- OpenEnv: Meta's open-source framework for building extensible AI environments.\n"
        "- Python & Pydantic: Serves as the backbone, utilizing strict typing and JSON "
        "schemas for defining exact agent Observation and Action spaces.\n"
        "- Uvicorn / FastAPI (Background): Exposes the environment concurrently over HTTP.\n"
        "- Docker: Ensures 100% reproducibility and instant Hugging Face Space deployability.\n"
        "- OpenAI GPT-4o-mini (Baseline): Included as a proof-of-concept AI agent leveraging "
        "function-calling to solve the tasks."
    )
    pdf.chapter_title('3. Relevancy to the Hackathon & Real World')
    pdf.chapter_body(
        "The Meta PyTorch Hackathon seeks infrastructural environments that provide genuine "
        "training value. Most submissions are simplistic 'toy' games. This project targets "
        "the highly pervasive Enterprise issue of 'Alert Fatigue'. By implementing dynamic "
        "ticket generation, semantic knowledge base searches, and Potential-Based "
        "Reward Shaping (giving dense incremental rewards rather than sparse binary rewards), we "
        "provide a production-grade benchmark. Agents scoring highly here can be directly deployed "
        "in real SaaS customer support pipelines."
    )
    pdf.chapter_title('4. Codebase Architecture (What each file means)')
    body_text = (
        "1. models.py:\n"
        "Defines strict Pydantic schemas (SupportTicketTriageAction, SupportTicketTriageObservation). "
        "This provides the strict 'contract' dictating exactly what inputs the agent receives and exactly "
        "what actions (search_kb, update_ticket, reply) it is allowed to take via the OpenEnv API.\n\n"
        "2. server/support_ticket_triage_environment.py:\n"
        "The core logic engine. It inherits from OpenEnv's Environment interface. It manages state transitions (step), "
        "enforces penalties (subtracting -0.01 per step to encourage fast solutions), limits episode length, "
        "handles the search algorithm for the knowledge base, and computes state potentials for rewards.\n\n"
        "3. server/tickets.json & server/kb.json:\n"
        "Dynamic mock data payloads. Loading from these variables ensures the environment scales dynamically "
        "and prevents under-trained Agents from 'overfitting' or memorizing hardcoded ticket strings.\n\n"
        "4. baseline.py:\n"
        "A functioning inference script proving the environment is solvable. It creates an iterative Chain-of-Thought "
        "loop connecting OpenAI's GPT models natively to the environment tools via the OpenEnv REST API."
    )
    pdf.chapter_body(body_text)
    pdf.output('presentation_panel.pdf')
    print("PDF generated successfully as 'presentation_panel.pdf'")
if __name__ == "__main__":
    create_pdf()
