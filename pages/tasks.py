import gradio as gr
from gradio_toggle import Toggle

# === Placeholder for tag button logic ===
def tag_clicked(tag_label):
    print(f"[Tag clicked]: {tag_label}")
    return

# === Show/hide the prompt block ===
def toggle_task(enabled):
    return gr.update(visible=enabled)

# === Logic for Add Prompt button ===
def add_prompt(count):
    if count < 3:
        return count + 1, *[
            gr.update(visible=(j <= count)) for j in range(3)
        ]
    return count, *[gr.update() for _ in range(3)]

# === UI render function ===
def render():
    gr.HTML("""
    <style>
        #task-header-full {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-left: 40px;
            padding-right: 40px;
            margin-bottom: 15px;
        }

        #task-buttons {
            display: flex;
            gap: 10px;
        }

        #task-heading {
            font-size: 18px;
            font-weight: 600;
        }

        .task-wrapper {
            max-width: 800px;
            padding-left: 40px;
            padding-right: 20px;
        }

        .task-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            background: #fff;
        }

        .light-prompt-box textarea {
            background-color: #f5f5f5;
            border: none;
            border-radius: 6px;
            padding: 10px;
            font-size: 14px;
        }

        .add-prompt-btn button {
            background: none;
            border: none;
            color: #1a73e8;
            font-weight: 500;
            font-size: 14px;
            padding-left: 0;
        }

        #save-draft-btn {
            background-color: white;
            border: 1px solid #dadce0;
            color: #3c4043;
            font-weight: 500;
        }

        #publish-btn {
            background-color: #1a73e8;
            color: white;
            font-weight: 500;
        }

        #publish-btn:hover {
            background-color: #1558b0;
        }

        #save-draft-btn:hover {
            background-color: #f1f3f4;
        }

        /* Hide footer */
        footer, .svelte-13f7f5i, .svelte-1ipelgc {
            display: none !important;
        }

        /* Hide settings panel button (gear icon) */
        #component-0 .absolute.top-4.right-4 {
            display: none !important;
        }
    </style>
    """)

    # === Top Heading + Buttons in Full Width ===
    with gr.Row(elem_id="task-header-full"):
        gr.Markdown("### Configure the tasks the agent will perform", elem_id="task-heading")
        with gr.Row(elem_id="task-buttons"):
            publish_btn = gr.Button("Publish", elem_id="publish-btn", variant="primary")
            save_btn = gr.Button("Save as draft", elem_id="save-draft-btn")

    # === Dummy handlers
    publish_btn.click(lambda: print("Published"), outputs=[])
    save_btn.click(lambda: print("Saved as draft"), outputs=[])

    # === Main task section
    with gr.Column(elem_classes=["task-wrapper"]):
        task_data = [
            ("Suggest content from business specific post ideas", "Post ideas"),
            ("Suggest content for upcoming holidays", "Holiday ideas"),
            ("Suggest content from my own top performing posts", "My posts"),
            ("Suggest content from my competitor's top performing posts", "Competitor posts"),
            ("Suggest content from trending topics, relevant to your business", "Trending")
        ]

        for i, (title, tag) in enumerate(task_data, start=1):
            with gr.Column(elem_classes=["task-card"]):
                with gr.Row():
                    with gr.Column(scale=11):
                        gr.Markdown(f"**{i}. {title}**")
                    with gr.Column(scale=1, min_width=80):
                        toggle = Toggle(value=True, color="blue", label="")

                with gr.Column(visible=True) as content_block:
                    with gr.Row():
                        main_prompt = gr.Textbox(
                            value=f"Identify {title.lower()} using",
                            interactive=True,
                            show_label=False,
                            lines=1,
                            elem_classes=["light-prompt-box"],
                            scale=8
                        )
                        tag_btn = gr.Button(f"⚙️ {tag}", size="sm", scale=2)
                        tag_btn.click(fn=lambda t=tag: tag_clicked(t), outputs=[])

                    prompt_count = gr.State(0)
                    extra_prompts = [
                        gr.Textbox(
                            placeholder="New prompt...",
                            visible=False,
                            interactive=True,
                            show_label=False,
                            elem_classes=["light-prompt-box"]
                        ) for _ in range(3)
                    ]

                    add_btn = gr.Button("➕ Add prompt", size="sm", elem_classes=["add-prompt-btn"])
                    add_btn.click(
                        add_prompt,
                        inputs=[prompt_count],
                        outputs=[prompt_count] + extra_prompts
                    )

                toggle.change(
                    fn=toggle_task,
                    inputs=[toggle],
                    outputs=[content_block]
                )
