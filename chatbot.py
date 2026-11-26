"""Command-line version of the IBU BITLoft chatbot.

For the web interface run:  python app.py

Created by the BITLoft Team, International Balkan University.
"""

from rag import FAREWELL_REPLY, Chatbot, is_farewell


def main():
    print("IBU BITLoft Chatbot")
    print("=" * 40)

    try:
        bot = Chatbot()
    except Exception as exc:
        print(f"Could not start the chatbot: {exc}")
        return

    history = []
    print("\nChatbot ready! Type your question (or 'bye' to exit)\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\nBot: {FAREWELL_REPLY}")
            break

        if not user_input:
            continue
        if is_farewell(user_input):
            print(f"Bot: {FAREWELL_REPLY}")
            break

        try:
            result = bot.ask(user_input, history)
        except Exception as exc:
            print(f"Bot: Sorry, something went wrong while answering: {exc}\n")
            continue

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": result["answer"]})
        print(f"Bot: {result['answer']}")
        if result["sources"]:
            print(f"     Sources: {', '.join(result['sources'])}")
        print()


if __name__ == "__main__":
    main()
