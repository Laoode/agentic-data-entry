Source: https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/

# Hierarchical Agent Teams

In our previous example (Agent Supervisor</a>), we introduced the concept of a single [supervisor node](https://langchain-ai.github.io/langgraph/concepts/multi_agent/#supervisor) to route work between different worker nodes.

But what if the job for a single worker becomes too complex? What if the number of workers becomes too large?

For some applications, the system may be more effective if work is distributed _hierarchically_.

You can do this by composing different subgraphs and creating a top-level supervisor, along with mid-level supervisors.

To do this, let's build a simple research assistant! The graph will look something like the following:

This notebook is inspired by the paper [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation](https://arxiv.org/abs/2308.08155), by Wu, et. al. In the rest of this notebook, you will:

1. Define the agents' tools to access the web and write files
2. Define some utilities to help create the graph and agents
3. Create and define each team (web research + doc writing)
4. Compose everything together.

## Setup

First, let's install our required packages and set our API keys


```shell
pip install -U langgraph langchain_community langchain_anthropic langchain-tavily langchain_experimental
```


```python
import getpass
import os


def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")


_set_if_undefined("OPENAI_API_KEY")
_set_if_undefined("TAVILY_API_KEY")
```


    Set up LangSmith</a> for LangGraph development</p>
    
        Sign up for LangSmith to quickly spot issues and improve the performance of your LangGraph projects. LangSmith lets you use trace data to debug, test, and monitor your LLM apps built with LangGraph — read more about how to get started here</a>. 
    </p>
</div>

## Create Tools

Each team will be composed of one or more agents each with one or more tools. Below, define all the tools to be used by your different teams.

We'll start with the research team.

**ResearchTeam tools**

The research team can use a search engine and url scraper to find information on the web. Feel free to add additional functionality below to boost the team performance!


API Reference: WebBaseLoader</a> | TavilySearch</a> | tool</a></i></sup>

```python
from typing import Annotated, List

from langchain_community.document_loaders import WebBaseLoader
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

tavily_tool = TavilySearch(max_results=5)


@tool
def scrape_webpages(urls: List[str]) -> str:
    """Use requests and bs4 to scrape the provided web pages for detailed information."""
    loader = WebBaseLoader(urls)
    docs = loader.load()
    return "\n\n".join(
        [
            f'\n{doc.page_content}\n</Document>'
            for doc in docs
        ]
    )
```

**Document writing team tools**

Next up, we will give some tools for the doc writing team to use.
We define some bare-bones file-access tools below.

Note that this gives the agents access to your file-system, which can be unsafe. We also haven't optimized the tool descriptions for performance.


API Reference: PythonREPL</a></i></sup>

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Optional

from langchain_experimental.utilities import PythonREPL
from typing_extensions import TypedDict

_TEMP_DIRECTORY = TemporaryDirectory()
WORKING_DIRECTORY = Path(_TEMP_DIRECTORY.name)


@tool
def create_outline(
    points: Annotated[List[str], "List of main points or sections."],
    file_name: Annotated[str, "File path to save the outline."],
) -> Annotated[str, "Path of the saved outline file."]:
    """Create and save an outline."""
    with (WORKING_DIRECTORY / file_name).open("w") as file:
        for i, point in enumerate(points):
            file.write(f"{i + 1}. {point}\n")
    return f"Outline saved to {file_name}"


@tool
def read_document(
    file_name: Annotated[str, "File path to read the document from."],
    start: Annotated[Optional[int], "The start line. Default is 0"] = None,
    end: Annotated[Optional[int], "The end line. Default is None"] = None,
) -> str:
    """Read the specified document."""
    with (WORKING_DIRECTORY / file_name).open("r") as file:
        lines = file.readlines()
    if start is None:
        start = 0
    return "\n".join(lines[start:end])


@tool
def write_document(
    content: Annotated[str, "Text content to be written into the document."],
    file_name: Annotated[str, "File path to save the document."],
) -> Annotated[str, "Path of the saved document file."]:
    """Create and save a text document."""
    with (WORKING_DIRECTORY / file_name).open("w") as file:
        file.write(content)
    return f"Document saved to {file_name}"


@tool
def edit_document(
    file_name: Annotated[str, "Path of the document to be edited."],
    inserts: Annotated[
        Dict[int, str],
        "Dictionary where key is the line number (1-indexed) and value is the text to be inserted at that line.",
    ],
) -> Annotated[str, "Path of the edited document file."]:
    """Edit a document by inserting text at specific line numbers."""

    with (WORKING_DIRECTORY / file_name).open("r") as file:
        lines = file.readlines()

    sorted_inserts = sorted(inserts.items())

    for line_number, text in sorted_inserts:
        if 1 <= line_number <= len(lines) + 1:
            lines.insert(line_number - 1, text + "\n")
        else:
            return f"Error: Line number {line_number} is out of range."

    with (WORKING_DIRECTORY / file_name).open("w") as file:
        file.writelines(lines)

    return f"Document edited and saved to {file_name}"


# Warning: This executes code locally, which can be unsafe when not sandboxed

repl = PythonREPL()


@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"
```

## Helper Utilities

We are going to create a few utility functions to make it more concise when we want to:

1. Create a worker agent.
2. Create a supervisor for the sub-graph.

These will simplify the graph compositional code at the end for us so it's easier to see what's going on.


API Reference: BaseChatModel</a> | StateGraph</a> | START</a> | END</a> | Command</a> | HumanMessage</a> | trim_messages</a></i></sup>

```python
from typing import List, Optional, Literal
from langchain_core.language_models.chat_models import BaseChatModel

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, trim_messages


class State(MessagesState):
    next: str


def make_supervisor_node(llm: BaseChatModel, members: list[str]) -> str:
    options = ["FINISH"] + members
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers: {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )

    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""

        next: Literal[*options]

    def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
        """An LLM-based router."""
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(goto=goto, update={"next": goto})

    return supervisor_node
```

## Define Agent Teams

Now we can get to define our hierarchical teams. "Choose your player!"

### Research Team

The research team will have a search agent and a web scraping "research_agent" as the two worker nodes. Let's create those, as well as the team supervisor.


API Reference: HumanMessage</a> | ChatOpenAI</a> | create_react_agent</a></i></sup>

```python
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(model="gpt-4o")

search_agent = create_react_agent(llm, tools=[tavily_tool])


def search_node(state: State) -> Command[Literal["supervisor"]]:
    result = search_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="search")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )


web_scraper_agent = create_react_agent(llm, tools=[scrape_webpages])


def web_scraper_node(state: State) -> Command[Literal["supervisor"]]:
    result = web_scraper_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="web_scraper")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )


research_supervisor_node = make_supervisor_node(llm, ["search", "web_scraper"])
```

Now that we've created the necessary components, defining their interactions is easy. Add the nodes to the team graph, and define the edges, which determine the transition criteria.


```python
research_builder = StateGraph(State)
research_builder.add_node("supervisor", research_supervisor_node)
research_builder.add_node("search", search_node)
research_builder.add_node("web_scraper", web_scraper_node)

research_builder.add_edge(START, "supervisor")
research_graph = research_builder.compile()
```


```python
from IPython.display import Image, display

display(Image(research_graph.get_graph().draw_mermaid_png()))
```



</p>

We can give this team work directly. Try it out below.


```python
for s in research_graph.stream(
    {"messages": [("user", "when is Taylor Swift's next tour?")]},
    {"recursion_limit": 100},
):
    print(s)
    print("---")
```
```output
{'supervisor': {'next': 'search'}}
---
{'search': {'messages': [HumanMessage(content="Taylor Swift's next tour is The Eras Tour, which includes both U.S. and international dates. She announced additional U.S. dates for 2024. You can find more details about the tour and ticket information on platforms like Ticketmaster and official announcements.", additional_kwargs={}, response_metadata={}, name='search', id='4df8687b-50a8-4342-aad5-680732c4a10f')]}}
---
{'supervisor': {'next': 'web_scraper'}}
---
{'web_scraper': {'messages': [HumanMessage(content='Taylor Swift\'s next tour is "The Eras Tour." Here are some of the upcoming international dates for 2024 that were listed on Ticketmaster:\n\n1. **Toronto, ON, Canada** at Rogers Centre\n   - November 21, 2024\n   - November 22, 2024\n   - November 23, 2024\n\n2. **Vancouver, BC, Canada** at BC Place\n   - December 6, 2024\n   - December 7, 2024\n   - December 8, 2024\n\nFor the most current information and additional dates, you can check platforms like Ticketmaster or Taylor Swift\'s [official website](https://www.taylorswift.com/events).', additional_kwargs={}, response_metadata={}, name='web_scraper', id='27524ebc-d179-4733-831d-ee10a58a2528')]}}
---
{'supervisor': {'next': '__end__'}}
---
```
### Document Writing Team

Create the document writing team below using a similar approach. This time, we will give each agent access to different file-writing tools.

Note that we are giving file-system access to our agent here, which is not safe in all cases.


```python
llm = ChatOpenAI(model="gpt-4o")

doc_writer_agent = create_react_agent(
    llm,
    tools=[write_document, edit_document, read_document],
    prompt=(
        "You can read, write and edit documents based on note-taker's outlines. "
        "Don't ask follow-up questions."
    ),
)


def doc_writing_node(state: State) -> Command[Literal["supervisor"]]:
    result = doc_writer_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="doc_writer")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )


note_taking_agent = create_react_agent(
    llm,
    tools=[create_outline, read_document],
    prompt=(
        "You can read documents and create outlines for the document writer. "
        "Don't ask follow-up questions."
    ),
)


def note_taking_node(state: State) -> Command[Literal["supervisor"]]:
    result = note_taking_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="note_taker")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )


chart_generating_agent = create_react_agent(
    llm, tools=[read_document, python_repl_tool]
)


def chart_generating_node(state: State) -> Command[Literal["supervisor"]]:
    result = chart_generating_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=result["messages"][-1].content, name="chart_generator"
                )
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )


doc_writing_supervisor_node = make_supervisor_node(
    llm, ["doc_writer", "note_taker", "chart_generator"]
)
```

With the objects themselves created, we can form the graph.


```python
# Create the graph here
paper_writing_builder = StateGraph(State)
paper_writing_builder.add_node("supervisor", doc_writing_supervisor_node)
paper_writing_builder.add_node("doc_writer", doc_writing_node)
paper_writing_builder.add_node("note_taker", note_taking_node)
paper_writing_builder.add_node("chart_generator", chart_generating_node)

paper_writing_builder.add_edge(START, "supervisor")
paper_writing_graph = paper_writing_builder.compile()
```


```python
from IPython.display import Image, display

display(Image(paper_writing_graph.get_graph().draw_mermaid_png()))
```



</p>


```python
for s in paper_writing_graph.stream(
    {
        "messages": [
            (
                "user",
                "Write an outline for poem about cats and then write the poem to disk.",
            )
        ]
    },
    {"recursion_limit": 100},
):
    print(s)
    print("---")
```
```output
{'supervisor': {'next': 'note_taker'}}
---
{'note_taker': {'messages': [HumanMessage(content='The outline for the poem about cats has been created and saved as "cats_poem_outline.txt".', additional_kwargs={}, response_metadata={}, name='note_taker', id='14a5d8ca-9092-416f-96ee-ba16686e8658')]}}
---
{'supervisor': {'next': 'doc_writer'}}
---
{'doc_writer': {'messages': [HumanMessage(content='The poem about cats has been written and saved as "cats_poem.txt".', additional_kwargs={}, response_metadata={}, name='doc_writer', id='c4e31a94-63ae-4632-9e80-1166f3f138b2')]}}
---
{'supervisor': {'next': '__end__'}}
---
```
## Add Layers

In this design, we are enforcing a top-down planning policy. We've created two graphs already, but we have to decide how to route work between the two.

We'll create a _third_ graph to orchestrate the previous two, and add some connectors to define how this top-level state is shared between the different graphs.


API Reference: BaseMessage</a></i></sup>

```python
from langchain_core.messages import BaseMessage

llm = ChatOpenAI(model="gpt-4o")

teams_supervisor_node = make_supervisor_node(llm, ["research_team", "writing_team"])
```


```python
def call_research_team(state: State) -> Command[Literal["supervisor"]]:
    response = research_graph.invoke({"messages": state["messages"][-1]})
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content, name="research_team"
                )
            ]
        },
        goto="supervisor",
    )


def call_paper_writing_team(state: State) -> Command[Literal["supervisor"]]:
    response = paper_writing_graph.invoke({"messages": state["messages"][-1]})
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content, name="writing_team"
                )
            ]
        },
        goto="supervisor",
    )


# Define the graph.
super_builder = StateGraph(State)
super_builder.add_node("supervisor", teams_supervisor_node)
super_builder.add_node("research_team", call_research_team)
super_builder.add_node("writing_team", call_paper_writing_team)

super_builder.add_edge(START, "supervisor")
super_graph = super_builder.compile()
```


```python
from IPython.display import Image, display

display(Image(super_graph.get_graph().draw_mermaid_png()))
```



</p>


```python
for s in super_graph.stream(
    {
        "messages": [
            ("user", "Research AI agents and write a brief report about them.")
        ],
    },
    {"recursion_limit": 150},
):
    print(s)
    print("---")
```
```output
{'supervisor': {'next': 'research_team'}}
---
{'research_team': {'messages': [HumanMessage(content="**AI Agents Overview 2023**\n\nAI agents are sophisticated technologies that automate and enhance various processes across industries, becoming increasingly integral to business operations. In 2023, these agents are notable for their advanced capabilities in communication, data visualization, and language processing.\n\n**Popular AI Agents in 2023:**\n1. **Auto GPT**: This agent is renowned for its seamless integration abilities, significantly impacting industries by improving communication and operational workflows.\n2. **ChartGPT**: Specializing in data visualization, ChartGPT enables users to interact with data innovatively, providing deeper insights and comprehension.\n3. **LLMops**: With advanced language capabilities, LLMops is a versatile tool seeing widespread use across multiple sectors.\n\n**Market Trends:**\nThe AI agents market is experiencing rapid growth, with significant advancements anticipated by 2030. There's a growing demand for AI agents in personalized interactions, particularly within customer service, healthcare, and marketing sectors. This trend is fueled by the need for more efficient and tailored customer experiences.\n\n**Key Players:**\nLeading companies such as Microsoft, IBM, Google, Oracle, and AWS are key players in the AI agents market, highlighting the widespread adoption and investment in these technologies.\n\n**Technological Innovations:**\nAI agents are being developed alongside simulation technologies for robust testing and deployment environments. Innovations in generative AI are accelerating, supported by advancements in large language models and platforms like ChatGPT.\n\n**Applications in Healthcare:**\nIn healthcare, AI agents are automating routine tasks, allowing medical professionals to focus more on patient care. They're poised to significantly enhance healthcare delivery and efficiency.\n\n**Future Prospects:**\nThe future of AI agents is promising, with continued evolution and integration into various platforms and ecosystems, offering more seamless and intelligent interactions. As these technologies advance, they are expected to redefine business operations and customer interactions.", additional_kwargs={}, response_metadata={}, name='research_team', id='5f6606e0-838c-406c-b50d-9f9f6a076322')]}}
---
{'supervisor': {'next': 'writing_team'}}
---
{'writing_team': {'messages': [HumanMessage(content="Here are the contents of the documents:\n\n### AI Agents Overview 2023\n\n**AI Agents Overview 2023**\n\nAI agents are sophisticated technologies that automate and enhance various processes across industries, becoming increasingly integral to business operations. In 2023, these agents are notable for their advanced capabilities in communication, data visualization, and language processing.\n\n**Popular AI Agents in 2023:**\n1. **Auto GPT**: This agent is renowned for its seamless integration abilities, significantly impacting industries by improving communication and operational workflows.\n2. **ChartGPT**: Specializing in data visualization, ChartGPT enables users to interact with data innovatively, providing deeper insights and comprehension.\n3. **LLMops**: With advanced language capabilities, LLMops is a versatile tool seeing widespread use across multiple sectors.\n\n**Market Trends:**\nThe AI agents market is experiencing rapid growth, with significant advancements anticipated by 2030. There's a growing demand for AI agents in personalized interactions, particularly within customer service, healthcare, and marketing sectors. This trend is fueled by the need for more efficient and tailored customer experiences.\n\n**Key Players:**\nLeading companies such as Microsoft, IBM, Google, Oracle, and AWS are key players in the AI agents market, highlighting the widespread adoption and investment in these technologies.\n\n**Technological Innovations:**\nAI agents are being developed alongside simulation technologies for robust testing and deployment environments. Innovations in generative AI are accelerating, supported by advancements in large language models and platforms like ChatGPT.\n\n**Applications in Healthcare:**\nIn healthcare, AI agents are automating routine tasks, allowing medical professionals to focus more on patient care. They're poised to significantly enhance healthcare delivery and efficiency.\n\n**Future Prospects:**\nThe future of AI agents is promising, with continued evolution and integration into various platforms and ecosystems, offering more seamless and intelligent interactions. As these technologies advance, they are expected to redefine business operations and customer interactions.\n\n### AI_Agents_Overview_2023_Outline\n\n1. Introduction to AI Agents in 2023\n2. Popular AI Agents: Auto GPT, ChartGPT, LLMops\n3. Market Trends and Growth\n4. Key Players in the AI Agents Market\n5. Technological Innovations: Simulation and Generative AI\n6. Applications of AI Agents in Healthcare\n7. Future Prospects of AI Agents", additional_kwargs={}, response_metadata={}, name='writing_team', id='851bd8a6-740e-488c-8928-1f9e05e96ea0')]}}
---
{'supervisor': {'next': 'writing_team'}}
---
{'writing_team': {'messages': [HumanMessage(content='The documents have been successfully created and saved:\n\n1. **AI_Agents_Overview_2023.txt** - Contains the detailed overview of AI agents in 2023.\n2. **AI_Agents_Overview_2023_Outline.txt** - Contains the outline of the document.', additional_kwargs={}, response_metadata={}, name='writing_team', id='c87c0778-a085-4a8e-8ee1-9b43b9b0b143')]}}
---
{'supervisor': {'next': '__end__'}}
---
```