from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

# this prompt acts as our critic: review output and criticize it
reflection_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You're a viral twitter influencer grading a tweet. Generating critique and recommendations for the user's tweet."
            "Always provide detailed recommendation, including requests for lengths, virality, style, etc.",
        ),
        MessagesPlaceholder(variable_name="messages"),
        # these are history messages that our agent is going to invoke, criticise and get recommendation over and over again
    ]
)


# this prompt generates the tweet that are going to be reviewed over and over again after the feedback we get from reflection_prompt
generation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You're a twitter techie influencer assistant tasked with writing excellent twitter posts."
            "Generate the best twitter post possible for the user's request."
            "If the user provide critique, respond with a revised version of your previous attempts.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)


llm = ChatOpenAI(model="gpt-4.1-mini")

generate_chain = generation_prompt | llm

reflection_chain = reflection_prompt | llm
