from typing import Sequence

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, MessageGraph

from chains import generate_chain, reflection_chain

# keys of langgraph nodes we're going to create
REFLECT = "reflect"  # run reflection chain
GENERATE = "generate"  # run generation chain


def generation_node(state: Sequence[BaseMessage]):
    return generate_chain.invoke({"messages": state})


def reflection_node(messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    res = reflection_chain.invoke({"messages": messages})
    return [
        HumanMessage(content=res.content)
    ]  # frame the content of message with the role of a human
    # why? trick LLM to think that a human is sending this message


# initialize graph object/builder
builder = MessageGraph()
# define 2 nodes: "reflect" and "generate"
builder.add_node(GENERATE, generation_node)
builder.add_node(REFLECT, reflection_node)
# tell langgraph that the starting node is GENERATE node
builder.set_entry_point(GENERATE)


# create a conditional object/edge as a function
def should_continue(state: Sequence[BaseMessage]):
    if len(state) > 6:
        return END
    return REFLECT


# add conditional edge
builder.add_conditional_edges(GENERATE, should_continue, {REFLECT: REFLECT, END: END})


# revise the tweet
builder.add_edge(REFLECT, GENERATE)


# compile graph
graph = builder.compile()


# generate graph mermaid drawing
graph.get_graph().draw_mermaid_png(output_file_path="reflection_agent.png")


# entry point
if __name__ == "__main__":
    print("Hello LangGraph!")

    inputs = HumanMessage(
        content="""Make this tweet better:"
                                    @LangChainAI
            — newly Tool Calling feature is seriously underrated.

            After a long wait, it's  here- making the implementation of agents across different models with function calling - super easy.

            Made a video covering their newest blog post

                                  """
    )
    response = graph.invoke(inputs)
