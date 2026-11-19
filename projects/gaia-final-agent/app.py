"""Gradio UI for manual evaluation and separate explicit GAIA submission."""
import os

import gradio as gr

from agent import GAIAAgent
from benchmark import evaluate, submit


def run_evaluation(profile: gr.OAuthProfile | None):
    if os.environ.get("AGENT_BACKEND", "ollama") == "hf" and (
            profile is None or not profile.username):
        return "Sign in with Hugging Face before live provider evaluation.", []
    try:
        results = evaluate(GAIAAgent())
    except Exception as error:
        return f"Evaluation stopped: {type(error).__name__}", []
    success = sum(bool(item["submitted_answer"]) for item in results)
    return (f"Generated {success}/{len(results)} answers. This is not a score. "
            "Review before submitting."), results


def submit_answers(code_url: str, results: list[dict], profile: gr.OAuthProfile | None):
    if profile is None or not profile.username:
        return "Sign in with Hugging Face before submission."
    try:
        return str(submit(profile.username, code_url, results))
    except ValueError as error:
        return str(error)
    except Exception as error:
        return f"Submission failed: {type(error).__name__}"


with gr.Blocks() as demo:
    gr.Markdown("# Hugging Face Agents Course — GAIA Unit 4")
    gr.LoginButton()
    gr.Markdown(
        "Local Ollama is the default inference backend. Set AGENT_BACKEND=hf, "
        "HF_TOKEN and HF_LIVE_INFERENCE=1 to opt into Hugging Face provider "
        "inference, which may use credits. Evaluation and submission are separate actions."
    )
    code_url = gr.Textbox(label="Public Space code URL (ends in /tree/main)")
    run = gr.Button("Run 20-question evaluation")
    status = gr.Textbox(label="Run status")
    results_state = gr.State([])
    answers = gr.JSON(label="Answers for review")
    run.click(run_evaluation, outputs=[status, results_state]).then(
        lambda results: results, inputs=[results_state], outputs=[answers]
    )
    send = gr.Button("Submit reviewed answers to official leaderboard")
    submission = gr.Textbox(label="Official scoring response")
    send.click(submit_answers, inputs=[code_url, results_state], outputs=[submission])


if __name__ == "__main__":
    demo.launch()
