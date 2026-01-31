ultrathink First, plan, and create a to-do list of what needs to be done, but do not create any code yet. Please review what is in this folder/ code base, which is a working implementation of the z-image model, but basic and not user friendly. The end goal is to create a beautiful (dont make it look like every other vibe website) web app that is user friendly and allows me to quickly create high quality photos or images using the z-image model. The user should be able to select the style of either anime or realistic and the aspect ratio and resolution, (Default should be 16x9).

It was tested using the @createImage.sh script and seems to be working well, however every time i run it, it reloads the model and is slow to start up.

Context: Look up (https://www.krea.ai/image) and its documentation and figure out how to implement a cut down version of this app. I dont need all the features but i really like the UI and the way it works.

recommended architecture:
The recommended architecture combines a Python backend (FastAPI) for persistent GPU inference with a Svelte/SvelteKit frontend for minimal bundle overhead and real-time updates, using a hybrid HTTP/WebSocket communication pattern. This approach will deliver sub-15-second image generation with a smooth, Krea.ai-inspired interface while keeping the model loaded in memory throughout the session. The M4 Pro with 24GB unified RAM should leverage PyTorch's MPS backend for optimal performance. The critical optimization is using bfloat16 precision (16-bit brain floating point).

I will be running this privately locally on my macbook, and i want it to be fast and responsive. It is a Apple M4 Pro with 24GB of RAM. Macos latest version Tahoe. Although i also want a button that would check for any model updates and allow me to update them. So it can only reach out for model update, but run locally. You can see in @createImage.py where it is getting the model from. 
Model Serving Strategy:
Implement a persistent model loading pattern to eliminate the repeated reload overhead. Load the z-image-turbo model once at server startup and keep it in GPU memory throughout the session.

When you open the app, you'll see a clean interface with a text input field centered at the bottom of the screen. This is where you type your prompts to generate images with z-image.
I am hoping we can upload reference images and use them in the prompt. For example, "here is a image of me, create an image of me in the style of an anime character.".

I want to be able to click on the images that are generated and see them in a full screen view where i can download them, and it will keep the last 20 images in a scrollable list on the right hand side of the screen. I should be able to 

When i see an image that I am happy with, I want to be able to create a new image based on that image, but allow me to enhance the prompt. So it will keep the same style and composition, but change the subject matter.