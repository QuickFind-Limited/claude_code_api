import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, query, ResultMessage

# Method 1: Using ClaudeSDKClient for persistent conversations
async def multi_turn_conversation() -> str:
    session_id = None
    async with ClaudeSDKClient() as client:
        while True:
            query: str = input("Enter a query: ")
            if query == "exit":
                break
            else:
                await client.query(query)
                async for msg in client.receive_response():
                    print(msg)
                    if isinstance(msg, ResultMessage):
                        session_id = msg.session_id
        return session_id
        # The conversation context is maintained throughout

# Method 2: Using query function with session management
async def resume_session():
    # Resume specific session
    async for message in query(
        prompt=input("Enter a query: "), 
        options=ClaudeCodeOptions(
            resume="21573a4c-872b-4866-96c6-084e8085451d",
            max_turns=3
        )
    ):
        if type(message).__name__ == "ResultMessage":
            print(message.result)

# Run the examples
# session_id = asyncio.run(multi_turn_conversation())
# print(session_id)
# asyncio.run(resume_session())
