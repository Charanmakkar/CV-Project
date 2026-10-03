"""Generate a presentation-ready Word proposal from PROJECT_PROPOSAL.md."""

from pathlib import Path

from generate_report import build_document

ROOT = Path(__file__).resolve().parents[1]


def main() -> Path:
    return build_document(
        ROOT / "docs" / "PROJECT_PROPOSAL.md",
        ROOT / "Computer_Vision_Autonomous_Patrol_Project_Proposal.docx",
        cover_title="Computer Vision\nAutonomous Patrol Simulator",
        subtitle_text="Project proposal for academic presentation",
        header_text="CV PROJECT  /  PROJECT PROPOSAL",
        strapline="Problem · Concept · Computer vision method · Evaluation · Demonstration",
        metadata_line="3 October 2026  |  Working software prototype",
        document_subject="Project concept, proposed validation, expected outcomes and presentation plan",
    )


if __name__ == "__main__":
    print(main())
