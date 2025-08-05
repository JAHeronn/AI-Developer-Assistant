# AI Developer Assistant – Screenshot Debugging with GPT-4o

A multimodal AI assistant that analyses screenshots of coding errors and provides structured, actionable debugging help.

---

## Live Demo

- Try it on Hugging Face Spaces - https://huggingface.co/spaces/JAHeronn/AI-Developer-Assistant
- Uses your own OpenAI API key (kept 100% in-browser)

---

## What It Does

- Accepts screenshots from IDEs like VS Code, IntelliJ, or Jupyter  
- Uses GPT-4o to extract error context, language, and development environment  
- Returns structured JSON describing:
  - Error type (e.g. runtime, syntax, test failure)  
  - Programming language  
  - IDE detected  
  - Suggested fix (if possible)  
- Includes follow-up chat interface for debugging assistance

---

## How to Use

1. Get your OpenAI API key at [platform.openai.com](https://platform.openai.com)  
2. Enter your API key in the input field (it’s never stored, only kept in memory)  
3. Upload a screenshot of your coding environment or error
4. Add context in the prompt input  
5. Get instant structured analysis + start chatting with the AI


## 📝 Licence

This project is licensed under the MIT Licence. See [LICENCE](./LICENCE) for details.




