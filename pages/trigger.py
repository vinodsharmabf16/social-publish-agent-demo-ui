import gradio as gr

def render():
    with gr.Row():
        # === Left Side ===
        with gr.Column(scale=2):
            gr.Markdown("### When should this agent run?")

            trigger_type = gr.Radio(
                ["Specify using AI prompt", "Specify using rules", "On set schedule"],
                value="Specify using AI prompt",
                label=""
            )

            # --- AI Prompt Section ---
            ai_prompt_box = gr.Textbox(
                label="When:",
                value="Competitor's post receives more than 100 engagements",
                lines=1,
                visible=True,
                interactive=True
            )

            # Extra prompt boxes (up to 3)
            extra_ai_prompts = [
                gr.Textbox(placeholder="New prompt...", lines=1, visible=False, interactive=True, show_label=False)
                for _ in range(3)
            ]

            # Keep track of how many are shown
            ai_prompt_count = gr.State(0)

            # Add prompt button
            add_prompt_btn = gr.Button("➕ Add prompt", visible=True)

            # Show one prompt at a time
            def add_ai_prompt(count):
                if count < len(extra_ai_prompts):
                    updates = [gr.update(visible=(i <= count)) for i in range(len(extra_ai_prompts))]
                    return count + 1, *updates
                return count, *[gr.update() for _ in extra_ai_prompts]

            add_prompt_btn.click(
                add_ai_prompt,
                inputs=[ai_prompt_count],
                outputs=[ai_prompt_count] + extra_ai_prompts
            )

            # --- Rules Section (Dummy UI) ---
            rule_type = gr.Dropdown(
                ["Engagement > 100", "Post contains keyword", "Followers > 10k"],
                label="Rule type",
                visible=False,
                interactive=True
            )

            rule_value = gr.Textbox(
                label="Value:",
                placeholder="Enter rule value...",
                visible=False,
                interactive=True
            )


            # --- Schedule Section (Dummy UI) ---
            # --- Schedule Section (Dummy UI) ---
            schedule_days = gr.CheckboxGroup(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                label="Days to run",
                visible=False,
                interactive=True
            )
            schedule_time = gr.Textbox(
                label="Time (24h format, e.g. 14:00):",
                placeholder="HH:MM",
                visible=False,
                interactive=True
            )


        # === Right Side ===
        with gr.Column(scale=1):
            gr.Markdown("### Preview")
            gr.Markdown("See how often your agent would run and what actions it would perform")

            with gr.Group():
                gr.Markdown("**Trigger**")
                gr.Markdown("""
📅 In the last 30 days, the agent would have run **2 times** based on your trigger settings  
🗓️ **March 30 and March 27, 2025**  
💡 Reasoning: Competitor's post received more than 100 engagements
                """)

            with gr.Group():
                gr.Markdown("**Task**")
                gr.Markdown("""
✅ 1. Analyze top performing posts  
✅ 2. Analyze competitor posts  
✅ 3. Identify trending topics  
✅ 4. Generate Post Ideas  
✅ 5. Schedule Posts
                """)

            gr.Button("▶️ Run test")

    # === Logic to Show/Hide Sections ===
    def update_trigger_ui(choice):
        return (
            # AI prompt
            gr.update(visible=choice == "Specify using AI prompt"),
            gr.update(visible=choice == "Specify using AI prompt"),

            # Rules
            gr.update(visible=choice == "Specify using rules"),
            gr.update(visible=choice == "Specify using rules"),

            # Schedule
            gr.update(visible=choice == "On set schedule"),
            gr.update(visible=choice == "On set schedule")
        )

    trigger_type.change(
        update_trigger_ui,
        inputs=[trigger_type],
        outputs=[
            ai_prompt_box, add_prompt_btn,
            *extra_ai_prompts,
            rule_type, rule_value,
            schedule_days, schedule_time
        ]

    )
