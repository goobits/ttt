#!/usr/bin/env python3
"""
Persistent chat session examples.

This example demonstrates how to save and load chat sessions,
maintaining conversation history across program runs.
"""

import ai
from ai import PersistentChatSession
from pathlib import Path


def basic_persistence():
    """Basic save and load example."""
    print("=== Basic Persistence ===")

    # Create a persistent session
    with ai.chat(persist=True, system="You are a helpful assistant") as session:
        # Have a conversation
        session.ask("My name is Alice and I love Python programming.")
        session.ask("I'm working on a web scraping project.")

        # Save the session
        session.save("alice_session.json")
        print("Session saved to alice_session.json")

        # Get session summary
        summary = session.get_summary()
        print(f"Messages: {summary['message_count']}")
        print(f"Duration: {summary['duration']}")

    # Load and resume the session
    print("\nLoading saved session...")
    session = PersistentChatSession.load("alice_session.json")

    # Continue the conversation
    response = session.ask("What's my name and what am I working on?")
    print(f"AI: {response}")

    # Clean up
    Path("alice_session.json").unlink()


def session_management():
    """Advanced session management."""
    print("\n=== Session Management ===")

    # Create session with custom ID
    session = PersistentChatSession(
        session_id="project_helper_001", system="You are a project management assistant"
    )

    # Build conversation
    session.ask(
        "I need to plan a software project with these phases: design, implementation, testing"
    )
    session.ask("The deadline is in 6 weeks")
    session.ask("We have 3 developers available")

    # Save in different formats
    session.save("project_plan.json", format="json")
    session.save("project_plan.pkl", format="pickle")

    # Export conversation
    print("\nConversation export (Markdown):")
    print(session.export_messages(format="markdown"))

    # Get detailed summary
    summary = session.get_summary()
    print(f"\nSession Summary:")
    print(f"  ID: {summary['session_id']}")
    print(f"  Messages: {summary['message_count']}")
    print(
        f"  Tokens used: {summary['total_tokens_in']} in, {summary['total_tokens_out']} out"
    )
    print(f"  Cost: ${summary['total_cost']:.4f}")

    # Clean up
    Path("project_plan.json").unlink()
    Path("project_plan.pkl").unlink()


def multi_session_tracking():
    """Track multiple sessions for different purposes."""
    print("\n=== Multi-Session Tracking ===")

    sessions_dir = Path("chat_sessions")
    sessions_dir.mkdir(exist_ok=True)

    # Create different sessions for different purposes
    sessions = {
        "coding": PersistentChatSession(
            system="You are an expert Python developer", session_id="coding_helper"
        ),
        "writing": PersistentChatSession(
            system="You are a creative writing assistant", session_id="writing_helper"
        ),
        "learning": PersistentChatSession(
            system="You are a patient teacher", session_id="learning_helper"
        ),
    }

    # Use different sessions
    sessions["coding"].ask("How do I implement a binary search tree?")
    sessions["writing"].ask("Help me write a haiku about programming")
    sessions["learning"].ask("Explain quantum computing like I'm 5")

    # Save all sessions
    for name, session in sessions.items():
        path = sessions_dir / f"{name}_session.json"
        session.save(path)
        print(f"Saved {name} session to {path}")

    # Load and display summaries
    print("\nSession Summaries:")
    for name in sessions:
        path = sessions_dir / f"{name}_session.json"
        loaded_session = PersistentChatSession.load(path)
        summary = loaded_session.get_summary()
        print(f"  {name}: {summary['message_count']} messages")

    # Clean up
    import shutil

    shutil.rmtree(sessions_dir)


def incremental_conversation():
    """Build a conversation incrementally across runs."""
    print("\n=== Incremental Conversation ===")

    session_file = Path("incremental_chat.json")

    # Load existing session or create new one
    if session_file.exists():
        print("Resuming existing conversation...")
        session = PersistentChatSession.load(session_file)
        print(f"Loaded {len(session.history)} previous messages")
    else:
        print("Starting new conversation...")
        session = PersistentChatSession(
            system="You are a helpful coding tutor", session_id="learning_python"
        )

    # Add to the conversation
    topics = [
        "What should I learn after mastering Python basics?",
        "Tell me about decorators",
        "Show me an example of a context manager",
    ]

    # Pick next topic based on conversation length
    topic_index = len([m for m in session.history if m["role"] == "user"])
    if topic_index < len(topics):
        response = session.ask(topics[topic_index])
        print(f"\nQ: {topics[topic_index]}")
        print(f"A: {response}")

        # Save progress
        session.save(session_file)
        print(f"\nProgress saved. Run again to continue learning!")
    else:
        print("\nAll topics covered! Here's what we discussed:")
        print(session.export_messages(format="text"))

        # Clean up completed session
        session_file.unlink()
        print("\nSession completed and cleaned up.")


def session_with_images():
    """Persistent session with multi-modal content."""
    print("\n=== Session with Images ===")

    with ai.chat(persist=True, model="gpt-4-vision-preview") as session:
        # First interaction with image
        session.ask(
            [
                "I'm going to show you some images for analysis.",
                "Here's the first one:",
                ai.ImageInput(
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/200px-Python-logo-notext.svg.png"
                ),
            ]
        )

        # Follow-up without image
        response = session.ask("What programming language is this logo for?")
        print(f"AI: {response}")

        # Save the multi-modal session
        session.save("multimodal_session.json")
        print("\nMulti-modal session saved!")

    # Load and continue
    loaded = PersistentChatSession.load("multimodal_session.json")
    response = loaded.ask("What colors are in that logo?")
    print(f"AI (from loaded session): {response}")

    # Clean up
    Path("multimodal_session.json").unlink()


def cost_tracking():
    """Track costs across sessions."""
    print("\n=== Cost Tracking ===")

    # Create a session for cost tracking
    with ai.chat(persist=True, model="gpt-3.5-turbo") as session:
        # Simulate some API calls
        session.ask("Write a 100-word story")
        session.ask("Translate it to French")
        session.ask("Now to Spanish")

        # Get cost summary
        summary = session.get_summary()
        print(f"\nSession Cost Summary:")
        print(f"  Total tokens in: {summary['total_tokens_in']}")
        print(f"  Total tokens out: {summary['total_tokens_out']}")
        print(f"  Estimated cost: ${summary['total_cost']:.4f}")

        # Model usage breakdown
        print(f"\nModel Usage:")
        for model, usage in summary["model_usage"].items():
            print(f"  {model}:")
            print(f"    Calls: {usage['count']}")
            print(f"    Tokens: {usage['tokens_in']} in, {usage['tokens_out']} out")
            print(f"    Cost: ${usage['cost']:.4f}")

        # Save for record keeping
        session.save("usage_report.json")

    # Clean up
    Path("usage_report.json").unlink()


if __name__ == "__main__":
    print("Persistent Chat Examples\n")

    # Run examples
    basic_persistence()
    session_management()
    multi_session_tracking()
    incremental_conversation()
    session_with_images()
    cost_tracking()

    print("\nAll examples completed!")
