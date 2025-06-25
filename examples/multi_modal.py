#!/usr/bin/env python3
"""
Multi-modal AI examples using vision capabilities.

This example demonstrates how to use the AI library with images.
"""

import ai
from ai import ImageInput

# Configure API keys if needed
# ai.configure(openai_api_key="your-key-here")


def basic_image_analysis():
    """Basic image analysis with a single image."""
    print("=== Basic Image Analysis ===")
    
    # Using a file path
    response = ai.ask([
        "What's in this image? Describe what you see.",
        ImageInput("examples/sample_image.jpg")
    ], model="gpt-4-vision-preview")
    
    print(f"Response: {response}")
    print(f"Model used: {response.model}")
    print(f"Time taken: {response.time:.2f}s\n")


def image_from_url():
    """Analyze an image from a URL."""
    print("=== Image from URL ===")
    
    response = ai.ask([
        "What breed of dog is this?",
        ImageInput("https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/YellowLabradorLooking_new.jpg/640px-YellowLabradorLooking_new.jpg")
    ], model="gpt-4-vision-preview")
    
    print(f"Response: {response}\n")


def multiple_images():
    """Compare multiple images."""
    print("=== Multiple Images ===")
    
    response = ai.ask([
        "Compare these two images. What are the main differences?",
        ImageInput("examples/image1.png"),
        ImageInput("examples/image2.png")
    ], backend="cloud")  # Will auto-select vision model
    
    print(f"Response: {response}\n")


def streaming_with_image():
    """Stream a response for image analysis."""
    print("=== Streaming with Image ===")
    
    print("Analysis: ", end="", flush=True)
    for chunk in ai.stream([
        "Write a detailed analysis of this image, including colors, composition, and mood.",
        ImageInput("examples/artwork.jpg")
    ], model="gpt-4-vision-preview"):
        print(chunk, end="", flush=True)
    print("\n")


def chat_with_images():
    """Use images in a chat session."""
    print("=== Chat with Images ===")
    
    with ai.chat(model="gpt-4-vision-preview") as session:
        # First message with image
        response1 = session.ask([
            "Look at this chart and tell me what it shows.",
            ImageInput("examples/chart.png")
        ])
        print(f"AI: {response1}")
        
        # Follow-up without image
        response2 = session.ask("What's the trend over the last 3 months?")
        print(f"AI: {response2}\n")


def image_with_bytes():
    """Use image from raw bytes."""
    print("=== Image from Bytes ===")
    
    # Read image as bytes
    with open("examples/photo.jpg", "rb") as f:
        image_bytes = f.read()
    
    response = ai.ask([
        "What's the main subject of this photo?",
        ImageInput(image_bytes, mime_type="image/jpeg")
    ], model="gpt-4-vision-preview")
    
    print(f"Response: {response}\n")


def mixed_content():
    """Complex multi-modal prompt with multiple text and image parts."""
    print("=== Mixed Content ===")
    
    response = ai.ask([
        "I'm planning a presentation. Here's my current slide:",
        ImageInput("examples/slide1.png"),
        "And here's what I want to change it to:",
        ImageInput("examples/slide2.png"), 
        "Can you help me write transition notes and suggest improvements?"
    ], quality=True)  # Prefer quality for complex analysis
    
    print(f"Response: {response}\n")


def error_handling():
    """Demonstrate error handling for vision requests."""
    print("=== Error Handling ===")
    
    # Try local backend (will fail with images)
    response = ai.ask([
        "What's in this image?",
        ImageInput("examples/test.jpg")
    ], backend="local")
    
    if response.failed:
        print(f"Error: {response.error}")
        print("Retrying with cloud backend...")
        
        response = ai.ask([
            "What's in this image?",
            ImageInput("examples/test.jpg")
        ], backend="cloud")
        
        print(f"Success: {response}\n")


def vision_model_selection():
    """Show different vision models."""
    print("=== Vision Model Selection ===")
    
    # List available vision models
    vision_models = []
    for model_name in ai.model_registry.list_models():
        model_info = ai.model_registry.get_model(model_name)
        if model_info and "vision" in model_info.capabilities:
            vision_models.append(model_name)
    
    print(f"Available vision models: {vision_models}")
    
    # Try different models
    for model in ["gpt-4-vision-preview", "gemini-pro-vision"]:
        try:
            response = ai.ask([
                "Describe this image in one sentence.",
                ImageInput("examples/simple.jpg")
            ], model=model)
            print(f"\n{model}: {response}")
        except Exception as e:
            print(f"\n{model}: Failed - {e}")


if __name__ == "__main__":
    # Note: These examples assume you have sample images in the examples/ directory
    # You can replace with your own image paths or URLs
    
    print("Multi-modal AI Examples\n")
    
    # Comment out examples that require specific images
    # basic_image_analysis()
    image_from_url()  # This should work with the Wikipedia URL
    # multiple_images()
    # streaming_with_image()
    # chat_with_images()
    # image_with_bytes()
    # mixed_content()
    error_handling()  # This will show the error message
    vision_model_selection()