import requests
import json
import gradio as gr
import time

url = "http://localhost:11434/api/generate"

headers = {
    'Content-Type': 'application/json'
}

history = []

def generate_response_stream(prompt):
    """Streaming response generator to prevent timeouts"""
    history.append(prompt)
    final_prompt = "\n".join(history)
    
    data = {
        "model": "codenova-ai",
        "prompt": final_prompt,
        "stream": True  # Enable streaming
    }
    
    try:
        response = requests.post(url=url, headers=headers, data=json.dumps(data), stream=True)
        
        if response.status_code == 200:
            collected_response = ""
            
            # Stream the response line by line
            for line in response.iter_lines():
                if line:
                    try:
                        decoded_line = line.decode('utf-8')
                        data_chunk = json.loads(decoded_line)
                        
                        if 'response' in data_chunk:
                            chunk = data_chunk['response']
                            collected_response += chunk
                            yield collected_response  # Yield partial response
                            
                        if data_chunk.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
            # Add final response to history
            if collected_response:
                history.append(collected_response)
                
        else:
            error_msg = f"Error {response.status_code}: {response.text}"
            yield error_msg
            
    except Exception as e:
        yield f"Connection Error: {str(e)}"

def clear_history():
    global history
    history = []
    return "", ""


# ============================================= UI =================================================
# Updated CSS with better colors - Dark Forest/Emerald theme
custom_css = """
/* Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Main container styling - Dark Forest Theme */
.gradio-container {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    font-family: 'Inter', 'Segoe UI', sans-serif;
    min-height: 100vh;
}

/* Header styling */
.header-container {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 25px;
    margin-bottom: 25px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    text-align: center;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.app-title {
    color: #ffffff;
    font-size: 2.8em;
    font-weight: 700;
    margin-bottom: 10px;
    text-shadow: 2px 2px 8px rgba(0,0,0,0.4);
    background: linear-gradient(45deg, #4ecdc4, #44a08d);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.app-subtitle {
    color: #b8f2e6;
    font-size: 1.2em;
    margin-bottom: 8px;
    font-weight: 500;
}

.creator-info {
    color: #95d5c8;
    font-size: 0.95em;
    opacity: 0.9;
}

/* Input panel styling - Warm emerald tones */
.input-panel {
    background: rgba(78, 205, 196, 0.1);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 25px;
    border: 1px solid rgba(78, 205, 196, 0.2);
    box-shadow: 0 12px 40px rgba(78, 205, 196, 0.1);
}

/* Output panel styling - Cool teal tones */
.output-panel {
    background: rgba(68, 160, 141, 0.08);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 25px;
    border: 1px solid rgba(68, 160, 141, 0.15);
    box-shadow: 0 12px 40px rgba(68, 160, 141, 0.1);
}

/* Input textbox styling */
.query-input textarea {
    background: rgba(255, 255, 255, 0.95) !important;
    border: 2px solid rgba(78, 205, 196, 0.3) !important;
    border-radius: 15px !important;
    color: #2c3e50 !important;
    font-size: 16px !important;
    padding: 15px !important;
    transition: all 0.3s ease !important;
    line-height: 1.6 !important;
}

.query-input textarea:focus {
    border-color: #4ecdc4 !important;
    box-shadow: 0 0 25px rgba(78, 205, 196, 0.3) !important;
    background: rgba(255, 255, 255, 1) !important;
}

/* Output textbox styling - Terminal-like appearance */
.code-output textarea {
    background: rgba(15, 32, 39, 0.9) !important;
    border: 2px solid rgba(78, 205, 196, 0.2) !important;
    border-radius: 15px !important;
    color: #4ecdc4 !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
    padding: 20px !important;
}

/* Button styling - Emerald gradient */
.generate-btn {
    background: linear-gradient(45deg, #4ecdc4, #44a08d) !important;
    border: none !important;
    border-radius: 15px !important;
    color: white !important;
    padding: 15px 30px !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 6px 20px rgba(78, 205, 196, 0.3) !important;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2) !important;
}

.generate-btn:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 30px rgba(78, 205, 196, 0.4) !important;
    background: linear-gradient(45deg, #52e5d7, #4aa697) !important;
}

.clear-btn {
    background: linear-gradient(45deg, #ff7675, #fd79a8) !important;
    border: none !important;
    border-radius: 15px !important;
    color: white !important;
    transition: all 0.3s ease !important;
    padding: 12px 20px !important;
    font-weight: 600 !important;
}

.clear-btn:hover {
    background: linear-gradient(45deg, #ff6b6b, #ff8a95) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(255, 118, 117, 0.3) !important;
}

/* Info panel styling */
.info-panel {
    background: rgba(78, 205, 196, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 18px;
    margin-top: 18px;
    border: 1px solid rgba(78, 205, 196, 0.1);
}

.info-text {
    color: #b8f2e6;
    font-size: 0.9em;
    line-height: 1.6;
}

/* Section headers */
.section-header {
    color: #4ecdc4 !important;
    text-shadow: 1px 1px 3px rgba(0,0,0,0.3) !important;
    font-weight: 600 !important;
    margin-bottom: 15px !important;
}

/* Scrollbar styling */
.code-output textarea::-webkit-scrollbar {
    width: 8px;
}

.code-output textarea::-webkit-scrollbar-track {
    background: rgba(78, 205, 196, 0.1);
    border-radius: 4px;
}

.code-output textarea::-webkit-scrollbar-thumb {
    background: rgba(78, 205, 196, 0.3);
    border-radius: 4px;
}

.code-output textarea::-webkit-scrollbar-thumb:hover {
    background: rgba(78, 205, 196, 0.5);
}
"""

# Create the Gradio interface with custom theme
with gr.Blocks(
    theme=gr.themes.Soft(
        primary_hue=gr.themes.colors.emerald,
        secondary_hue=gr.themes.colors.teal,
        neutral_hue=gr.themes.colors.slate,
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "Consolas", "monospace"],
    ).set(
        body_background_fill="#0f2027",
        button_primary_background_fill="#4ecdc4",
        button_primary_background_fill_hover="#44a08d",
    ),
    css=custom_css,
    title="CodeNova-AI | AI Code Teaching Assistant",
    head="<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap' rel='stylesheet'>"
) as demo:
    
    # Header section
    with gr.Row(elem_classes="header-container"):
        gr.HTML("""
            <div class="app-title">🚀 CodeNova-AI</div>
            <div class="app-subtitle">AI-Powered Code Teaching Assistant</div>
            <div class="creator-info">Created by Ayush Gautam | IIT Kanpur Graduate | AI Innovation Expert</div>
        """)
    
    # Main content area with two columns
    with gr.Row(equal_height=True):
        # Left column - User Input
        with gr.Column(scale=1, elem_classes="input-panel"):
            gr.HTML("<h3 class='section-header'>💬 Ask Your Coding Question</h3>")
            
            user_query = gr.Textbox(
                placeholder="🔥 Enter your coding question here...\n\nExamples:\n• How do I create a Python function to sort a list?\n• Explain recursion with examples\n• Show me how to handle exceptions in Python\n• What's the difference between lists and tuples?",
                lines=10,
                label="Your Question",
                elem_classes="query-input",
                show_label=False,
                max_lines=15
            )
            
            with gr.Row():
                generate_btn = gr.Button(
                    "✨ Generate Code Explanation",
                    elem_classes="generate-btn",
                    variant="primary",
                    size="lg"
                )
                clear_btn = gr.Button(
                    "🗑️ Clear Chat",
                    elem_classes="clear-btn",
                    size="sm"
                )
            
            # Enhanced info panel
            gr.HTML("""
                <div class="info-panel">
                    <div class="info-text">
                        <strong>💡 Tips for Best Results:</strong><br>
                        • 🎯 Be specific about programming language<br>
                        • 📝 Describe your goal clearly<br>
                        • ⚡ Ask about specific concepts or errors<br>
                        • 🔄 Build on previous responses<br><br>
                        <strong>🚀 Streaming Enabled:</strong> Real-time response generation!
                    </div>
                </div>
            """)
        
        # Right column - Code Output
        with gr.Column(scale=1, elem_classes="output-panel"):
            gr.HTML("<h3 class='section-header'>🤖 AI Assistant Response</h3>")
            
            code_output = gr.Textbox(
                label="Generated Code & Explanation",
                lines=22,
                elem_classes="code-output",
                show_label=False,
                placeholder="🎯 Your AI-generated response will appear here in real-time...\n\n🔥 CodeNova-AI will provide:\n\n📚 Step-by-step explanations\n💻 Working code examples  \n⭐ Best practices & tips\n🚀 Performance insights\n🔧 Common pitfalls to avoid\n\n✨ Responses stream live - no more waiting!",
                interactive=False,
                max_lines=25
            )
            
            # Enhanced status panel
            gr.HTML("""
                <div class="info-panel">
                    <div class="info-text">
                        <strong>🔧 Model:</strong> CodeNova-AI (CodeLlama-7B-Instruct)<br>
                        <strong>🎯 Specialty:</strong> Code Teaching & Step-by-Step Learning<br>
                        <strong>📊 Status:</strong> <span style="color: #4ecdc4;">● Online & Streaming</span><br>
                        <strong>⚡ Mode:</strong> Real-time Response Generation<br>
                        <strong>🎓 Creator:</strong> Ayush Gautam, IIT Kanpur
                    </div>
                </div>
            """)
    
    # Enhanced footer
    with gr.Row():
        gr.HTML("""
            <div style="text-align: center; margin-top: 25px; padding: 20px; background: rgba(78, 205, 196, 0.08); border-radius: 15px; color: white !important; border: 1px solid rgba(78, 205, 196, 0.15);">
                <p style="margin: 0; font-size: 1em; line-height: 1.6; color: white !important;">
                    🎓 <strong style="color: white !important;">Powered by Advanced AI Technology</strong> | Built with ❤️ by <strong style="color: white !important;">Ayush Gautam</strong>, IIT Kanpur Graduate<br>
                    🚀 <strong style="color: white !important;">CodeNova-AI</strong> - Making coding education accessible, interactive, and engaging for everyone worldwide
                </p>
            </div>
        """)

    
    # Event handlers with streaming support
    generate_btn.click(
        fn=generate_response_stream,  # Use streaming function
        inputs=user_query,
        outputs=code_output,
        show_progress=True
    )
    
    clear_btn.click(
        fn=clear_history,
        inputs=None,
        outputs=[user_query, code_output]
    )
    
    # Allow Enter key to submit with streaming
    user_query.submit(
        fn=generate_response_stream,  # Use streaming function
        inputs=user_query,
        outputs=code_output,  
        show_progress=True
    )

# Launch with optimized settings
if __name__ == "__main__":
    demo.queue(max_size=20)  # Enable queue for better performance
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
        show_error=True,
        max_threads=10  # Handle multiple users
    )
