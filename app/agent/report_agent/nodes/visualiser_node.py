import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from app.agent.report_agent.schemas import ReportAgentState
from utils.logger import get_logger

logger = get_logger(__name__)


def visualiser_node(state: ReportAgentState):
    logger.info("[VISUALIZER NODE] Creating charts for your expenses...")

    categories = state["raw_data"]["categories"]

    labels = [c["category"] for c in categories]
    spent = [c["spent"] for c in categories]
    budgets = [c["budget"] or 0.0 for c in categories]

    try:
        pie_bytes = _generate_pie(labels, spent)
        bar_bytes = _generate_bar(labels, spent, budgets)

    except Exception as e:
        logger.error(f"[VISUALISER NODE] Chart generation failed: {e}")
        raise

    return {"chart_image_bytes": {"pie": pie_bytes, "bar": bar_bytes}}


def _generate_pie(labels: list[str], spent: list[float]):
    fig, ax = plt.subplots(figsize=(7, 7))

    if not spent:
        ax.text(
            0.5,
            0.5,
            "No expenses this month",
            ha="center",
            va="center",
            fontsize=12,
            transform=ax.transAxes,
        )
    else:
        wedges, texts, autotexts = ax.pie(
            spent, labels=labels, autopct="%1.1f%%", startangle=140, pctdistance=0.85
        )

    ax.set_title("Spending by Category", fontsize=14, fontweight="bold", pad=20)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.read()


def _generate_bar(labels: list[str], spent: list[float], budgets: list[float]):
    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width / 2, spent, width, label="Spent", color="#E74C3C")
    ax.bar(x + width / 2, budgets, width, label="Budget", color="#2ECC71")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel("Amount (SGD)")
    ax.set_title("Spent vs Budget by Category", fontsize=14, fontweight="bold")
    ax.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf.read()
