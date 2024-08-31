import reflex as rx
import requests
import mimetypes
import os
import time
import logging
from openai import OpenAI
import json

LaTeX = ""

def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5):
        while True:
            try:
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
                if run.completed_at:
                    elapsed_time = run.completed_at - run.created_at
                    formatted_elapsed_time = time.strftime(
                        "%H:%M:%S", time.gmtime(elapsed_time)
                    )
                    # print(f"Run completed in {formatted_elapsed_time}")
                    logging.info(f"Run completed in {formatted_elapsed_time}")
                    # Get messages here once Run is completed!
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    last_message = messages.data[0]
                    response = last_message.content[0].text.value
                    print(f"{response}")
                    LaTeX = f"{response}"
                    break
            except Exception as e:
                logging.error(f"An error occurred while retrieving the run: {e}")
                break
            logging.info("Waiting for run to complete...")
            time.sleep(sleep_interval)

def text_to_latex(text):
    message = text
    # Define your OpenAI API key directly
    api_key = "___"

    # Create an OpenAI client with the API key
    client = OpenAI(api_key=api_key)


    thread_id = "thread_nxgLyathgYSnRQHJHKZWczQG"
    assistant_id = "asst_mE1PhOgATRi7GgfAvqTSoZH6"
    message = client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=message
    )
    run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id="asst_mE1PhOgATRi7GgfAvqTSoZH6"
    )
    # === Run ===
    wait_for_run_completion(client=client, thread_id=thread_id, run_id=run.id)



def speech_to_text(filepath):
    url = "https://api.monsterapi.ai/v1/generate/whisper"
    API_Key = "___"
    payload = {"diarize": "true", "language": "en"}

    file_name = os.path.basename(filepath)

    files = {
        "file": (file_name, open(filepath,
                                "rb"), mimetypes.guess_type(filepath)[0])
    }
    headers = {"accept": "application/json", "authorization": f"Bearer {API_Key}"}
    

    response = requests.post(url, data=payload, files=files, headers=headers)
    # FETCHING!!!
    
    process_id = (response.json())["process_id"]
    url = f"https://api.monsterapi.ai/v1/status/{process_id}"

    headers = {
        "accept": "application/json",
        "authorization": "Bearer ___"
    }

    status = "IN_PROGRESS"

    while status != "COMPLETED":
        response = requests.get(url, headers=headers)
        status = response.json()["status"]

    speakers = (response.json()["result"]["text"])['Sequence']
    text = ""
    for speaker in speakers:
        text += speaker['transcription']
    print(text)
    text_to_latex(text)


class State(rx.State):
    """The app state."""
    img: list[str] = []
    text_result: str = ""

    async def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            upload_data = await file.read()
            outfile = f".web/public/{file.filename}"

            # Save the file.
            with open(outfile, "wb") as file_object:
                file_object.write(upload_data)

            # Update the img var.
            self.img.append(file.filename)
            #!!!
            result = speech_to_text(outfile)
            self.text_result = result

def index():
    """The main view."""
    return rx.vstack(
        rx.text_area(LaTeX),
        rx.upload(
            rx.vstack(
                rx.button("Select File", color="rgb(107,99,246)", bg="white", border="1px solid rgb(107,99,246)"),
                rx.text("Drag and drop files here or click to select files"),
            ),
            multiple=False,
            accept={
                "audio/mpeg": [".mp3"],
                "video/mp4": [".mp4"]
            },
            max_files=1,
            disabled=False,
            on_keyboard=True,
            border="1px dotted rgb(107,99,246)",
            padding="5em",
        ),
        rx.button(
            "Upload",
            on_click=lambda: State.handle_upload(rx.upload_files()),
        ),
        rx.text(State.text_result),  # Display the speech-to-text result
        rx.chakra.responsive_grid(
            rx.foreach(
                State.img,
                lambda img: rx.vstack(
                    rx.image(src=img),
                    rx.text(img),
                ),
            ),
            columns=[2],
            spacing="5px",
        ),
        padding="5em",
    )

app = rx.App()
app.add_page(index)
app.compile()
