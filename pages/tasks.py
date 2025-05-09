import gradio as gr
from gradio_toggle import Toggle

def render():
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### Configure the tasks the agent will perform")

            task_data = [
                ("Suggest content from business specific post ideas", "Post ideas"),
                ("Suggest content for upcoming holidays", "Holiday ideas"),
                ("Suggest content from my own top performing posts", "My posts"),
                ("Suggest content from my competitor's top performing posts", "Competitor posts"),
                ("Suggest content from trending topics, relevant to your business", "Trending")
            ]

            for i, (title, tag) in enumerate(task_data, start=1):
                with gr.Group():
                    # === Top Row: Title + Toggle ===
                    with gr.Row():
                        with gr.Column(scale=10):
                            gr.Markdown(f"**{i}. {title}**")
                        with gr.Column(scale=1, min_width=50):
                            toggle = Toggle(value=True, color="blue", label="")


                    # === Main Prompt + Pill Button ===
                    with gr.Row():
                        main_prompt = gr.Textbox(
                            value=f"Identify {title.lower()} using",
                            interactive=True,
                            show_label=False,
                            scale=8
                        )
                        tag_btn = gr.Button(tag, interactive=False, scale=2)

                    # === Add Prompt Button ===
                    add_btn = gr.Button("➕ Add prompt", visible=True)

                    # === Extra Prompt Fields ===
                    extra_prompts = [
                        gr.Textbox(
                            placeholder="New prompt...",
                            visible=False,
                            interactive=True,
                            show_label=False
                        ) for _ in range(3)
                    ]
                    prompt_count = gr.State(0)

                    # === Add prompt click logic ===
                    def add_prompt(count):
                        if count < len(extra_prompts):
                            updates = [gr.update(visible=(j <= count)) for j in range(len(extra_prompts))]
                            return count + 1, *updates
                        return count, *[gr.update() for _ in extra_prompts]

                    add_btn.click(
                        add_prompt,
                        inputs=[prompt_count],
                        outputs=[prompt_count] + extra_prompts
                    )

                    # === Toggle hides all prompts/buttons ===
                    def toggle_task(enabled):
                        v = gr.update(visible=enabled)
                        return v, v, *[v for _ in extra_prompts]

                    toggle.change(
                        toggle_task,
                        inputs=[toggle],
                        outputs=[main_prompt, add_btn] + extra_prompts
                    )

        # === Right Column: Preview (no changes here) ===
        with gr.Column(scale=1):
            gr.Markdown("### Preview")
            gr.Markdown("See how your agent would run and what actions it would perform")

            with gr.Accordion("1. Analyze top performing posts", open=True):
                gr.Markdown("Identified recurring themes from [24 top posts](#)")
                gr.Markdown("`Product tips (42%)` `Industry news (28%)` `Customer stories (18%)`")

            with gr.Accordion("2. Analyze competitor posts", open=True):
                gr.Markdown("Analyzed [18 competitor posts](#) with high engagement")
                gr.Markdown("`New feature announcement` `Pricing promotions` `Case studies`")

            with gr.Accordion("3. Identify trending topics", open=True):
                gr.Markdown("Identified trending hashtags relevant to your industry:")
                gr.Markdown("#AIProductivity #RemoteWorkTools #2025TechTrends")

            with gr.Accordion("4. Generate Post Ideas", open=True):
                gr.Markdown("Generated 5 content ideas based on trend and engagement analysis")

            gr.Button("▶️ Run test")
