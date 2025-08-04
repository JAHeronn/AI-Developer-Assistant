# MIT Licence
# Copyright (c) 2025 Joseph Heron
# See the LICENCE file in the root directory for full license text.

from openai import OpenAI
import base64
import json
import gradio as gr

MODEL_GPT = 'gpt-4o'

# function to encode image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# function for analysing the screenshot (JSON response)
def analyse_screenshots(user_prompt, uploaded_files, api_key):
    """Providing a screenshot and image, then getting an analysis/response in JSON"""

    if not uploaded_files or len(uploaded_files) == 0:
        return "Please upload at least one screenshot to analyse.", None

    if not api_key or not api_key.startswith('sk-'):
        return "**Invalid API Key**: Please enter a valid OpenAI API key starting with 'sk-'", None

    image_content = []
    screenshot_info = []

    for i, file in enumerate(uploaded_files):
        if file is not None:
            image_data_url = f"data:image/jpeg;base64,{encode_image(file.name)}"
            image_content.append({
                "type": "image_url",
                "image_url": {"url": image_data_url}
            })
            screenshot_info.append(f"Screenshot {i + 1}: {file.name}")

    system_message = f"""You are a helpful software and code debugging assistant. Analyse the {len(uploaded_files)} screenshot(s) and text description, then respond 
    with a JSON object containing: 
        {{
        "screenshots_analysed": {len(uploaded_files)},
        "extracted_text": "main error messages and code snippets visible across all screenshots which likely relate to the issue",
        "error_analysis": {{
            "error_type": "syntax|runtime|compilation|network|linting|other",
            "severity": "critical|warning|info", 
            "location": "file and line information if visible across screenshots",
            "language": "the detected programming language used in the screenshots"
        }},
        "environment": {{
            "ide": "IDE type if recognisable (VS Code, PyCharm, etc.)",
            "framework": "detected framework/library (React, Flask, Spring Boot, etc.)"
        }},
        "screenshot_breakdown": {{
            "screenshot_1": "brief description of what this screenshot shows",
            "screenshot_2": "brief description of what this screenshot shows (if applicable)",
            "screenshot_3": "brief description of what this screenshot shows (if applicable)"
        }},
        "solution": "step-by-step debugging advice considering information from all screenshots. Provide each step on a new line (use actual line breaks between numbered steps)",
        "confidence": "a 0.0-1.0 confidence score for this analysis"
    }}

    When analysing multiple screenshots, look for connections between them 
    (e.g., code in one screenshot causing error in another). If no text description is given, look out for lines of the code where there are 
    visible errors (red, yellow lines etc) or clear descriptions of the error from a terminal/console if shown. Make sure to be honest 
    in your confidence score. Be as specific as possible in your solution. Always return valid JSON only."""

    user_content = [{"type": "text", "text": user_prompt}] + image_content

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_content}
    ]

    try:
        openai = OpenAI(api_key=api_key)

        response = openai.chat.completions.create(
            model=MODEL_GPT,
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        response_text = response.choices[0].message.content

        try:
            parsed_data = json.loads(response_text)

            formatted_analysis = format_json_for_display(parsed_data)
            return formatted_analysis, parsed_data

        except json.JSONDecodeError:
            return f"Error parsing response. Raw output:\n{response_text}", None

    except Exception as e:
        if "API key" in str(e):
            return "**Connection Error**: Please check your OpenAI API key is valid and has sufficient credits.", None
        elif "rate limit" in str(e).lower():
            return "**Rate Limit Error**: Too many requests. Please wait a moment and try again.", None
        else:
            return f"Analysis failed: {str(e)}. Please try again with another screenshot", None


# function for formatting the display of the JSON for the UI
def format_json_for_display(data):
    """Format JSON data for UI display"""
    try:
        severity_emoji = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "🔵"
        }

        error_analysis = data.get("error_analysis", {})
        environment = data.get("environment", {})
        screenshot_breakdown = data.get("screenshot_breakdown", {})

        severity = error_analysis.get("severity", "unknown")
        severity_emoji = severity_emoji.get(severity, "⚪")

        screenshot_section = ""
        if screenshot_breakdown:
            screenshot_section = "\n## Screenshot Analysis\n\n"
            for key, description in screenshot_breakdown.items():
                if description:
                    screenshot_num = key.replace("screenshot_", "").replace("_", " ").title()
                    screenshot_section += f"**Screenshot {screenshot_num}:** {description}  \n"

        formatted_text = f"""## {severity_emoji} Error Analysis

**Type:** {error_analysis.get("error_type", "Unknown").title()} Error  
**Severity:** {severity.title()}  
**Location:** {error_analysis.get("location", "Not specified")}  
**Language:** {error_analysis.get("language", "Not detected")}  
**Screenshots Analysed:** {data.get("screenshots_analysed", 1)}

## 🖥️ Environment

**IDE:** {environment.get("ide", "Not detected")}  
**Framework:** {environment.get("framework", "Not detected")}

{screenshot_section}

## 📝 Extracted Text

{data.get("extracted_text", "No text extracted")}

## 💡 Solution

{data.get("solution", "No solution provided")}

**Confidence:** {float(data.get("confidence", 0)) * 100:.0f}%"""

        return formatted_text

    except Exception as e:
        return f"Error formatting the display: {str(e)}"


# function for follow-up questions/additional conversation
def followup_conversation(user_question, conversation_history, analysis_data, api_key):
    """Conversation for follow-up questions"""
    if not user_question.strip():
        return conversation_history, "Please ask a question."

    if not api_key or not api_key.startswith('sk-'):
        return conversation_history, "Please enter a valid OpenAI API key above."

    # Build context from previous analysis
    if analysis_data:
        screenshots_count = analysis_data.get("screenshots_analysed", 1)
        context = f"""Previous screenshot analysis context ({screenshots_count} screenshot(s) analysed):

        {json.dumps(analysis_data, indent=2)}

        This analysis was performed on the user's screenshot(s). Reference this context when answeing the follow-up questions."""
    else:
        context = "No previous screenshot analysis available. Please analyse screenshot(s) first in the other tab."

    system_message = f"""You are a helpful software and code debugging assistant. The user is asking a follow-up question about a previous code 
    analysis:

    {context}

    previous conversation:

    {conversation_history}

    Provide natural, conversational responses. Be helpful and detailed but don't repeat information unnecessarily. If referring to the 
    previous analysis, be specific about what you're referencing."""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_question}
    ]

    try:
        openai = OpenAI(api_key=api_key)

        response = openai.chat.completions.create(
            model=MODEL_GPT,
            messages=messages,
            temperature=0.7
        )

        assistant_response = response.choices[0].message.content

        new_exchange = f"**You:** {user_question}\n\n**Assistant:** {assistant_response}"

        if conversation_history == "Your conversation will appear here after you start asking questions...":
            updated_conversation = new_exchange
        elif conversation_history.strip():
            updated_conversation = conversation_history + "\n\n" + new_exchange
        else:
            updated_conversation = new_exchange

        return updated_conversation, ""

    except Exception as e:
        if "API key" in str(e):
            error_message = f"**Assistant:** I'm having trouble connecting to the AI service. Please check your API key."
        elif "rate limit" in str(e).lower():
            error_message = f"**Assistant:** I'm receiving too many requests. Please wait a moment and try again."
        else:
            error_message = f"**Assistant:** Sorry, I encountered an error: {str(e)}. Please try again."

        return conversation_history, error_message


# Gradio interface with tabs
with gr.Blocks(title="Multimodal AI Developer Assistant") as interface:
    gr.Markdown("# Multimodal AI Developer Assistant")
    gr.Markdown("Upload screenshots of your code errors and get quick debugging help.")

    with gr.Row():
        api_key_input = gr.Textbox(
            label="OpenAI API Key",
            type="password",
            placeholder="sk-...",
            info="Enter your OpenAI API key. It's only used for this session and not stored anywhere.",
            scale=3
        )
        with gr.Column(scale=1, min_width=200):
            gr.Markdown("**Need an API key?** Get one at [platform.openai.com](https://platform.openai.com)")

    # Storing analysis data across tabs
    analysis_json = gr.State(None)

    with gr.Tabs():
        with gr.TabItem("Analyse Screenshots"):

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Upload screenshots and describe your issue")
                    gr.Markdown("Example screenshots: code, terminal error, browser console")
                    gr.Markdown("For the best results, show your code and any error messages")

                    prompt_input = gr.Textbox(
                        lines=4,
                        label="Describe your issue",
                        placeholder="What were you trying to do when this error occurred? Any additional context might help..."
                    )
                    image_input = gr.File(
                        file_count="multiple",
                        type="filepath",
                        file_types=[".png", ".jpg", ".jpeg"],
                        label="Upload Screenshots (1-3 recommended)"
                    )
                    analyse_btn = gr.Button("Analyse Screenshots", variant="primary")

                with gr.Column(scale=2):
                    analysis_output = gr.Markdown(label="Analysis Results")


            def analyse_with_loading(prompt, files, api_key):
                # Showing loading message immediately
                if not api_key or not api_key.startswith('sk-'):
                    yield "**Please enter a valid OpenAI API key above**", None
                    return
                yield "\n\n**Analysing...**\n\nPlease wait while I identify the issue.", None

                result, data = analyse_screenshots(prompt, files, api_key)
                yield result, data


            analyse_btn.click(
                fn=analyse_with_loading,
                inputs=[prompt_input, image_input, api_key_input],
                outputs=[analysis_output, analysis_json],
            )

        with gr.TabItem("Ask Follow-up Questions"):
            gr.Markdown("### Continue the conversation about your analysis")

            conversation_history = gr.Markdown(
                label="Conversation History",
                value="Your conversation will appear here after you start asking questions..."
            )

            with gr.Row():
                question_input = gr.Textbox(
                    lines=2,
                    label="Ask a follow-up question",
                    placeholder="Can you explain this in more detail? How do I prevent this error in the future?"
                )
                submit_btn = gr.Button("Submit", variant="primary")


            def followup_with_api_key(user_question, conversation_history, analysis_data, api_key):
                if not api_key or not api_key.startswith('sk-'):
                    return conversation_history, "Please enter a valid OpenAI API key above."

                return followup_conversation(user_question, conversation_history, analysis_data, api_key)


            submit_btn.click(
                fn=followup_with_api_key,
                inputs=[question_input, conversation_history, analysis_json, api_key_input],
                outputs=[conversation_history, question_input]
            )



if __name__ == "__main__":
    try:
        interface.launch()
    except Exception as e:
        print(f"Failed to launch the app: {e}")
