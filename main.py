from typing import Sequence

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, MessageGraph

from chains import generate_chain, reflection_chain



from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich import print


# keys of langgraph nodes we're going to create
REFLECT = "reflect"  # run reflection chain
GENERATE = "generate"  # run generation chain


def generation_node(state: Sequence[BaseMessage]):
    """Run the generation chain and return its response."""
    return generate_chain.invoke({"messages": state})


def reflection_node(messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    """Run the reflection chain, then wrap the content as *HumanMessage*.

    Pretending the feedback comes from a human reliably nudges the LLM to
    use the critique as genuine instructions for improvement.
    """
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
    """Stop after 3 generate+reflect cycles (6 messages after the prompt)."""
    if len(state) > 6:
        return END # should end after 6 turns, save API cost :D
    return REFLECT


# add conditional edge
builder.add_conditional_edges(GENERATE, should_continue, {REFLECT: REFLECT, END: END})


# revise the tweet
builder.add_edge(REFLECT, GENERATE)


# compile graph
graph = builder.compile()


# generate graph mermaid drawing
graph.get_graph().draw_mermaid_png(output_file_path="reflection_agent.png")



# Pretty‑print helpers
# ────────────────────────────────────────────────────────────────
console = Console(record=True)

from langchain_core.messages import AIMessage

def print_transcript(messages: Sequence[BaseMessage]) -> None:
    """Render the full reflection dialogue to the terminal."""

    # the first message is always the user prompt
    console.rule("[bold]🟢 Prompt")
    console.print(Markdown(messages[0].content.strip()))

    draft_i, critique_i = 0, 0
    for msg in messages[1:]:
        if isinstance(msg, AIMessage):  # ← only AI turns are drafts
            draft_i += 1
            console.rule(f"[cyan]📝 Draft {draft_i}")
            console.print(Markdown(msg.content.strip()))
        elif isinstance(msg, HumanMessage):  # ← reflection turns
            critique_i += 1
            console.rule(f"[yellow]💡 Critique {critique_i}")
            console.print(Markdown(msg.content.strip()))
        else:  # just in case
            console.rule("[red]❓ Unknown message type")
            console.print(repr(msg))

    console.rule("[bold green]✅ Final tweet")
    console.print(Panel(messages[-1].content.strip(), style="bold green"))
# ────────────────────────────────────────────────────────────────



# entry point
if __name__ == "__main__":
    print("[bold magenta]Hello LangGraph![/]")

    inputs = HumanMessage(
        content="""Make this tweet better:"
        
                                    @LangChainAI
            — newly Tool Calling feature is seriously underrated.
            After a long wait, it's  here- making the implementation of agents across different models with function calling - super easy.
            Made a video covering their newest blog post
            
                                  """
    )
    response = graph.invoke(inputs)

    for i, m in enumerate(response, 1):
        print(i, type(m))

    print_transcript(response)

    # after the graph finishes
    md_path = console.save_text("transcript.md", clear=False)
    console.print(f"[green]📄 Saved → {md_path}[/]")



